import json
import logging
import os

import boto3
import pandas as pd
from es_aws_functions import aws_functions, exception_classes, general_functions
from marshmallow import EXCLUDE, Schema, fields

import imputation_functions as imp_func


class EnvironmentSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    def handle_error(self, e, data, **kwargs):
        logging.error(f"Error validating environment params: {e}")
        raise ValueError(f"Error validating environment params: {e}")

    bucket_name = fields.Str(required=True)
    method_name = fields.Str(required=True)
    run_environment = fields.Str(required=True)


class RuntimeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    def handle_error(self, e, data, **kwargs):
        logging.error(f"Error validating runtime params: {e}")
        raise ValueError(f"Error validating runtime params: {e}")

    bpm_queue_url = fields.Str(required=True)
    distinct_values = fields.List(fields.String, required=True)
    environment = fields.Str(required=True)
    factors_parameters = fields.Dict(required=True)
    in_file_name = fields.Str(required=True)
    out_file_name = fields.Str(required=True)
    period_column = fields.Str(required=True)
    questions_list = fields.List(fields.String, required=True)
    sns_topic_arn = fields.Str(required=True)
    survey = fields.Str(required=True)


def lambda_handler(event, context):
    """
    Prepares data for and calls the Calculate imputation factors method by adding on the
    required columns needed by the method.
    :param event: Contains all the variables which are required for the specific run.
    :param context: lambda context
    :return: Success & None/Error - Type: JSON
    """
    current_module = "Imputation Calculate Factors - Wrangler."
    error_message = ""

    # Define run_id outside of try block
    run_id = 0

    # Set-up variables for status message
    bpm_queue_url = None

    try:
        # Retrieve run_id before input validation
        # Because it is used in exception handling
        run_id = event["RuntimeVariables"]["run_id"]

        # Set up clients
        lambda_client = boto3.client("lambda", region_name="eu-west-2")

        environment_variables = EnvironmentSchema().load(os.environ)

        runtime_variables = RuntimeSchema().load(event["RuntimeVariables"])

        # Environment Variables
        bucket_name = environment_variables["bucket_name"]
        method_name = environment_variables["method_name"]
        run_environment = environment_variables["run_environment"]

        # Runtime Variables
        bpm_queue_url = runtime_variables["bpm_queue_url"]
        distinct_values = runtime_variables["distinct_values"]
        environment = runtime_variables["environment"]
        factors_parameters = runtime_variables["factors_parameters"]
        in_file_name = runtime_variables["in_file_name"]
        out_file_name = runtime_variables["out_file_name"]
        period_column = runtime_variables["period_column"]
        questions_list = runtime_variables["questions_list"]
        sns_topic_arn = runtime_variables["sns_topic_arn"]
        survey = runtime_variables['survey']

    except Exception as e:
        error_message = general_functions.handle_exception(e, current_module, run_id,
                                                           context=context)
        raise exception_classes.LambdaFailure(error_message)

    try:
        logger = general_functions.get_logger(survey, current_module, environment,
                                              run_id)
    except Exception as e:
        error_message = general_functions.handle_exception(e, current_module,
                                                           run_id, context=context)
        raise exception_classes.LambdaFailure(error_message)

    try:
        logger.info("Started - retrieved configuration variables.")

        data = aws_functions.read_dataframe_from_s3(bucket_name, in_file_name)

        logger.info("Successfully retrieved data")

        factor_columns = imp_func.\
            produce_columns("imputation_factor_", questions_list)

        # create df columns needed for method
        for factor in factor_columns:
            data[factor] = 0

        payload = {
            "RuntimeVariables": {
                "bpm_queue_url": bpm_queue_url,
                "data": json.loads(data.to_json(orient="records")),
                "environment": environment,
                "questions_list": questions_list,
                "distinct_values": distinct_values,
                "factors_parameters": factors_parameters,
                "run_id": run_id,
                "survey": survey
            }
        }

        # invoke the method to calculate the factors
        calculate_factors = lambda_client.invoke(
            FunctionName=method_name, Payload=json.dumps(payload)
        )
        logger.info("Successfully invoked method.")

        json_response = json.loads(
            calculate_factors.get("Payload").read().decode("UTF-8"))
        logger.info("JSON extracted from method response.")

        if not json_response["success"]:
            raise exception_classes.MethodFailure(json_response["error"])

        output_df = pd.read_json(json_response["data"], dtype=False)
        distinct_values.append(period_column)
        columns_to_keep = imp_func.produce_columns(
                                             "imputation_factor_",
                                             questions_list,
                                             distinct_values
                                            )

        final_df = output_df[columns_to_keep].drop_duplicates().to_json(orient="records")
        aws_functions.save_to_s3(bucket_name, out_file_name, final_df)
        logger.info("Successfully sent data to s3.")

        if run_environment != "development":
            logger.info(aws_functions.delete_data(bucket_name, in_file_name))
            logger.info("Successfully deleted input data.")

        aws_functions.send_sns_message(sns_topic_arn, "Imputation - Calculate Factors.")
        logger.info("Successfully sent message to sns.")

    except Exception as e:
        error_message = general_functions.handle_exception(e, current_module,
                                                           run_id, context=context,
                                                           bpm_queue_url=bpm_queue_url)
    finally:
        if (len(error_message)) > 0:
            logger.error(error_message)
            raise exception_classes.LambdaFailure(error_message)

    logger.info("Successfully completed module: " + current_module)

    return {"success": True}
