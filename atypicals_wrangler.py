import json
import logging
import os

import boto3
from es_aws_functions import aws_functions, exception_classes, general_functions
from marshmallow import Schema, fields

import imputation_functions as imp_func


class EnvironmentSchema(Schema):
    """
    Schema to ensure that environment variables are present and in the correct format.
    :return: None
    """
    bucket_name = fields.Str(required=True)
    checkpoint = fields.Str(required=True)
    method_name = fields.Str(required=True)
    run_environment = fields.Str(required=True)


def lambda_handler(event, context):
    """
    The wrangler converts the data from JSON format into a dataframe and then adds new
    Atypical columns (one for each question) onto the dataframe.
    These columns are initially populated with 0 values.
    :param event: Contains all the variables which are required for the specific run.
    :param context: N/A
    :return:  Success & Checkpoint/Error - Type: JSON
    """
    current_module = "Imputation Atypicals - Wrangler."
    error_message = ""
    logger = logging.getLogger("Atypicals")
    logger.setLevel(10)
    # Define run_id outside of try block
    run_id = 0
    try:

        logger.info("Starting " + current_module)

        # Retrieve run_id before input validation
        # Because it is used in exception handling
        run_id = event["RuntimeVariables"]["run_id"]

        sqs = boto3.client("sqs", region_name="eu-west-2")
        lambda_client = boto3.client("lambda", region_name="eu-west-2")

        environment_variables, errors = EnvironmentSchema().load(os.environ)
        if errors:
            logger.error(f"Error validating environment params: {errors}")
            raise ValueError(f"Error validating environment params: {errors}")

        runtime_variables, errors = RuntimeSchema().load(event["RuntimeVariables"])
        if errors:
            logger.error(f"Error validating runtime params: {errors}")
            raise ValueError(f"Error validating runtime params: {errors}")

        logger.info("Validated parameters.")

        # Environment Variables
        bucket_name = environment_variables["bucket_name"]
        checkpoint = environment_variables["checkpoint"]
        method_name = environment_variables["method_name"]
        run_environment = environment_variables["run_environment"]

        # Runtime Variables
        in_file_name = event["RuntimeVariables"]["in_file_name"]
        incoming_message_group_id = event["RuntimeVariables"]["incoming_message_group_id"]
        location = event["RuntimeVariables"]["location"]
        out_file_name = event["RuntimeVariables"]["out_file_name"]
        outgoing_message_group_id = event["RuntimeVariables"]["outgoing_message_group_id"]
        questions_list = event["RuntimeVariables"]["questions_list"]
        sns_topic_arn = event["RuntimeVariables"]["sns_topic_arn"]
        sqs_queue_url = event["RuntimeVariables"]["queue_url"]

        logger.info("Retrieved configuration variables.")

        data, receipt_handler = aws_functions.get_dataframe(sqs_queue_url, bucket_name,
                                                            in_file_name,
                                                            incoming_message_group_id,
                                                            location)

        logger.info("Successfully retrieved data.")
        atypical_columns = imp_func.produce_columns("atyp_", questions_list)

        for col in atypical_columns:
            data[col] = 0

        logger.info("Atypicals columns successfully added")

        data_json = data.to_json(orient="records")

        payload = {
            "RuntimeVariables": {
                "data": json.loads(data_json),
                "questions_list": questions_list,
                "run_id": run_id
            }
        }

        logger.info("Dataframe converted to JSON")

        wrangled_data = lambda_client.invoke(
            FunctionName=method_name,
            Payload=json.dumps(payload)
        )
        logger.info("Successfully invoked method.")

        json_response = json.loads(wrangled_data.get("Payload").read().decode("UTF-8"))
        logger.info("JSON extracted from method response.")

        if not json_response["success"]:
            raise exception_classes.MethodFailure(json_response["error"])

        aws_functions.save_data(bucket_name, out_file_name,
                                json_response["data"], sqs_queue_url,
                                outgoing_message_group_id, location)
        logger.info("Successfully sent data to s3.")

        if receipt_handler:
            sqs.delete_message(QueueUrl=sqs_queue_url, ReceiptHandle=receipt_handler)
            logger.info("Successfully deleted message from sqs.")

        if run_environment != "development":
            logger.info(aws_functions.delete_data(bucket_name, in_file_name, location))
            logger.info("Successfully deleted input data.")

        logger.info(aws_functions.send_sns_message(checkpoint, sns_topic_arn,
                                                   "Imputation - Atypicals."))

        logger.info("Successfully sent message to sns.")

    except Exception as e:
        error_message = general_functions.handle_exception(e, current_module,
                                                           run_id, context)
    finally:
        if (len(error_message)) > 0:
            logger.error(error_message)
            raise exception_classes.LambdaFailure(error_message)

    logger.info("Successfully completed module: " + current_module)

    return {"success": True, "checkpoint": checkpoint}
