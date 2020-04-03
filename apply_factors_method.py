import logging

import pandas as pd
from es_aws_functions import general_functions


def lambda_handler(event, context):
    """
    Applies imputation factors on a question-by-question basis.
    :param event:  JSON payload that contains: json_data and questions_list - Type: JSON.
    :param context: N/A
    :return: Success - {"success": True/False, "data"/"error": "JSON String"/"Message"}
    """
    current_module = "Apply Factors - Method"
    error_message = ""
    logger = logging.getLogger("Apply")
    logger.setLevel(10)
    run_id = 0
    try:
        logger.info("Apply Factors Method Begun")
        # Retrieve run_id before input validation
        # Because it is used in exception handling
        run_id = event['RuntimeVariables']['run_id']
        json_data = event['RuntimeVariables']["json_data"]
        sum_columns = event['RuntimeVariables']["sum_columns"]
        working_dataframe = pd.DataFrame(json_data)

        questions_list = event['RuntimeVariables']["questions_list"]

        for question in questions_list:
            # Loop through each question value, impute based on factor and previous value
            # then drop the previous value and the imp factor
            working_dataframe[question] = working_dataframe.apply(
                lambda x:
                general_functions.sas_round(x["prev_" + question] *
                                            x["imputation_factor_" + question]),
                axis=1,
            )

            logger.info("Completed imputation of " + str(question))

        working_dataframe = working_dataframe.apply(
            lambda x: sum_data_columns(x, sum_columns), axis=1)

        final_output = {"data": working_dataframe.to_json(orient="records")}

    except Exception as e:
        error_message = general_functions.handle_exception(e, current_module,
                                                           run_id, context)
    finally:
        if (len(error_message)) > 0:
            logger.error(error_message)
            return {"success": False, "error": error_message}

    logger.info("Successfully completed module: " + current_module)
    final_output['success'] = True
    return final_output


def sum_data_columns(input_row, sum_columns):
    # Calculate all sum columns.
    for sum_column in sum_columns:
        new_sum = 0
        for data_column in sum_column['data']:
            if sum_column['data'][data_column] == "+":
                new_sum += input_row[data_column]
            elif sum_column['data'][data_column] == "-":
                new_sum -= input_row[data_column]
        input_row[sum_column['column_name']] = int(new_sum)

    return input_row
