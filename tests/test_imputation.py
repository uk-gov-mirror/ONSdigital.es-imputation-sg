import json
from unittest import mock

import pandas as pd
import pytest
from es_aws_functions import test_generic_library
from moto import mock_s3
from pandas.util.testing import assert_frame_equal

import add_regionless_method as lambda_regionless_method_function
import add_regionless_wrangler as lambda_regionless_wrangler_function
import apply_factors_method as lambda_apply_method_function
import apply_factors_wrangler as lambda_apply_wrangler_function
import atypicals_method as lambda_atypicals_method_function
import atypicals_wrangler as lambda_atypicals_wrangler_function
import calculate_imputation_factors_method as lambda_factors_method_function
import calculate_imputation_factors_wrangler as lambda_factors_wrangler_function
import calculate_means_method as lambda_means_method_function
import calculate_means_wrangler as lambda_means_wrangler_function
import calculate_movement_method as lambda_movement_method_function
import calculate_movement_wrangler as lambda_movement_wrangler_function
import imputation_functions as lambda_imputation_function
import iqrs_method as lambda_iqrs_method_function
import iqrs_wrangler as lambda_iqrs_wrangler_function
import recalculate_means_wrangler as lambda_recalc_wrangler_function

generic_environment_variables = {
    "bucket_name": "test_bucket",
    "checkpoint": "999",
    "method_name": "add_regionless_method",
    "response_type": "response_type",
    "run_environment": "temporary"
}

questions_list = [
    "Q601_asphalting_sand",
    "Q602_building_soft_sand",
    "Q603_concreting_sand",
    "Q604_bituminous_gravel",
    "Q605_concreting_gravel",
    "Q606_other_gravel",
    "Q607_constructional_fill"
  ]

wrangler_apply_runtime_variables = {
    "RuntimeVariables": {
        "current_data": "test_wrangler_movement_prepared_current_data",
        "distinct_values": ["region", "strata"],
        "factors_parameters": {
            "RuntimeVariables": {
                "region_column": "region",
                "regionless_code": 14
            }
        },
        "incoming_message_group_id": "test_group",
        "in_file_name": "test_wrangler_apply_input",
        "location": "Here",
        "out_file_name": "test_wrangler_apply_output.json",
        "outgoing_message_group_id": "test_id",
        "previous_data": "test_wrangler_movement_prepared_previous_data",
        "questions_list": questions_list,
        "queue_url": "Earl",
        "run_id": "bob",
        "sns_topic_arn": "fake_sns_arn",
        "sum_columns": [
            {
              "column_name": "Q608_total",
              "data": {
                "Q601_asphalting_sand": "+",
                "Q602_building_soft_sand": "+",
                "Q603_concreting_sand": "+",
                "Q604_bituminous_gravel": "+",
                "Q605_concreting_gravel": "+",
                "Q606_other_gravel": "+",
                "Q607_constructional_fill": "+"
              }
            }
          ],
        "unique_identifier": ["responder_id"]

    }
}

wrangler_atypicals_runtime_variables = {
    "RuntimeVariables": {
        "incoming_message_group_id": "test_group",
        "in_file_name": "test_wrangler_atypicals_input",
        "location": "Here",
        "out_file_name": "test_wrangler_atypicals_output.json",
        "outgoing_message_group_id": "test_id",
        "questions_list": questions_list,
        "queue_url": "Earl",
        "run_id": "bob",
        "sns_topic_arn": "fake_sns_arn"
    }
}

wrangler_factors_runtime_variables = {
    "RuntimeVariables": {
        "distinct_values": ["region", "strata"],
        "factors_parameters": "test_param",
        "incoming_message_group_id": "test_group",
        "in_file_name": "test_wrangler_factors_input",
        "location": "Here",
        "out_file_name": "test_wrangler_factors_output.json",
        "outgoing_message_group_id": "test_id",
        "period_column": "period",
        "questions_list": questions_list,
        "queue_url": "Earl",
        "run_id": "bob",
        "sns_topic_arn": "fake_sns_arn"
    }
}

wrangler_regionless_runtime_variables = {
    "RuntimeVariables": {
        "factors_parameters": {
            "RuntimeVariables": {
                "region_column": "region",
                "regionless_code": 14
            }
        },
        "incoming_message_group_id": "test_group",
        "in_file_name": "test_wrangler_regionless_input",
        "location": "Here",
        "out_file_name": "test_wrangler_regionless_output.json",
        "outgoing_message_group_id": "test_id",
        "queue_url": "Earl",
        "run_id": "bob",
        "sns_topic_arn": "fake_sns_arn"
    }
}

##########################################################################################
#                                     Generic                                            #
##########################################################################################

@pytest.mark.parametrize(
    "which_lambda,which_runtime_variables,which_environment_variables,"
    "which_data,expected_message,assertion",
    [
        (lambda_regionless_wrangler_function, wrangler_regionless_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_apply_wrangler_function, wrangler_apply_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_atypicals_wrangler_function, wrangler_atypicals_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_factors_wrangler_function, wrangler_factors_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_means_wrangler_function, wrangler_means_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_movement_wrangler_function, wrangler_movements_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_iqrs_wrangler_function, wrangler_iqrs_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert),
        (lambda_recalc_wrangler_function, wrangler_recalc_runtime_variables,
         generic_environment_variables, None,
         "ClientError", test_generic_library.wrangler_assert)
    ])
def test_client_error(which_lambda, which_runtime_variables,
                      which_environment_variables, which_data,
                      expected_message, assertion):
    test_generic_library.client_error(which_lambda, which_runtime_variables,
                                      which_environment_variables, which_data,
                                      expected_message, assertion)


@pytest.mark.parametrize(
    "which_lambda,which_runtime_variables,which_environment_variables,mockable_function,"
    "expected_message,assertion",
    [
        (lambda_method_function, method_runtime_variables,
         method_environment_variables, "strata_period_method.EnvironSchema",
         "'Exception'", test_generic_library.method_assert),
        (lambda_wrangler_function, wrangler_runtime_variables,
         wrangler_environment_variables, "strata_period_wrangler.EnvironSchema",
         "'Exception", test_generic_library.wrangler_assert)
    ])
def test_general_error(which_lambda, which_runtime_variables,
                       which_environment_variables, mockable_function,
                       expected_message, assertion):
    test_generic_library.general_error(which_lambda, which_runtime_variables,
                                       which_environment_variables, mockable_function,
                                       expected_message, assertion)


@mock_s3
@mock.patch('strata_period_wrangler.aws_functions.get_dataframe',
            side_effect=test_generic_library.replacement_get_dataframe)
def test_incomplete_read_error(mock_s3_get):
    file_list = ["test_wrangler_input.json"]

    test_generic_library.incomplete_read_error(lambda_wrangler_function,
                                               wrangler_runtime_variables,
                                               wrangler_environment_variables,
                                               file_list,
                                               "strata_period_wrangler",
                                               "IncompleteReadError")


@pytest.mark.parametrize(
    "which_lambda,which_environment_variables,expected_message,assertion",
    [
        (lambda_method_function, method_environment_variables,
         "KeyError", test_generic_library.method_assert),
        (lambda_wrangler_function, wrangler_environment_variables,
         "KeyError", test_generic_library.wrangler_assert)
    ])
def test_key_error(which_lambda, which_environment_variables,
                   expected_message, assertion):
    test_generic_library.key_error(which_lambda, which_environment_variables,
                                   expected_message, assertion)


@mock_s3
@mock.patch('strata_period_wrangler.aws_functions.get_dataframe',
            side_effect=test_generic_library.replacement_get_dataframe)
def test_method_error(mock_s3_get):
    file_list = ["test_wrangler_input.json"]

    test_generic_library.wrangler_method_error(lambda_wrangler_function,
                                               wrangler_runtime_variables,
                                               wrangler_environment_variables,
                                               file_list,
                                               "strata_period_wrangler")


@pytest.mark.parametrize(
    "which_lambda,expected_message,assertion",
    [(lambda_method_function,
      "Error validating environment param",
      test_generic_library.method_assert),
     (lambda_wrangler_function,
      "Error validating environment param",
      test_generic_library.wrangler_assert)])
def test_value_error(which_lambda, expected_message, assertion):
    test_generic_library.value_error(
        which_lambda, expected_message, assertion)

##########################################################################################
#                                     Specific                                           #
##########################################################################################


# def test_calculate_strata():
#     """
#     Runs the calculate_strata function that is called by the method.
#     :param None
#     :return Test Pass/Fail
#     """
#     with open("tests/fixtures/test_method_input.json", "r") as file_1:
#         file_data = file_1.read()
#     input_data = pd.DataFrame(json.loads(file_data))
#
#     produced_data = input_data.apply(
#         lambda_method_function.calculate_strata,
#         strata_column="strata",
#         value_column="Q608_total",
#         survey_column="survey",
#         region_column="region",
#         axis=1,
#     )
#     produced_data = produced_data.sort_index(axis=1)
#
#     with open("tests/fixtures/test_method_prepared_output.json", "r") as file_2:
#         file_data = file_2.read()
#     prepared_data = pd.DataFrame(json.loads(file_data))
#
#     assert_frame_equal(produced_data, prepared_data)
#
#
# @mock_s3
# def test_method_success():
#     """
#     Runs the method function.
#     :param None
#     :return Test Pass/Fail
#     """
#     with mock.patch.dict(lambda_method_function.os.environ,
#                          method_environment_variables):
#         with open("tests/fixtures/test_method_prepared_output.json", "r") as file_1:
#             file_data = file_1.read()
#         prepared_data = pd.DataFrame(json.loads(file_data))
#
#         with open("tests/fixtures/test_method_input.json", "r") as file_2:
#             test_data = file_2.read()
#         method_runtime_variables["RuntimeVariables"]["data"] = test_data
#
#         output = lambda_method_function.lambda_handler(
#             method_runtime_variables, test_generic_library.context_object)
#
#         produced_data = pd.DataFrame(json.loads(output["data"]))
#
#     assert output["success"]
#     assert_frame_equal(produced_data, prepared_data)
#
#
# def test_strata_mismatch_detector():
#     """
#     Runs the strata_mismatch_detector function that is called by the wrangler.
#     :param None
#     :return Test Pass/Fail
#     """
#     with open("tests/fixtures/test_method_output.json", "r") as file_1:
#         test_data_in = file_1.read()
#     method_data = pd.DataFrame(json.loads(test_data_in))
#
#     produced_data, anomalies = lambda_wrangler_function.strata_mismatch_detector(
#         method_data,
#         "201809", "period",
#         "responder_id", "strata",
#         "good_strata",
#         "current_period",
#         "previous_period",
#         "current_strata",
#         "previous_strata")
#
#     with open("tests/fixtures/test_wrangler_prepared_output.json", "r") as file_2:
#         test_data_out = file_2.read()
#     prepared_data = pd.DataFrame(json.loads(test_data_out))
#
#     assert_frame_equal(produced_data, prepared_data)
#
#
# @mock_s3
# @mock.patch('strata_period_wrangler.aws_functions.get_dataframe',
#             side_effect=test_generic_library.replacement_get_dataframe)
# @mock.patch('strata_period_wrangler.aws_functions.save_data',
#             side_effect=test_generic_library.replacement_save_data)
# def test_wrangler_success(mock_s3_get, mock_s3_put):
#     """
#     Runs the wrangler function.
#     :param mock_s3_get - Replacement Function For The Data Retrieval AWS Functionality.
#     :param mock_s3_put - Replacement Function For The Data Saveing AWS Functionality.
#     :return Test Pass/Fail
#     """
#     bucket_name = wrangler_environment_variables["bucket_name"]
#     client = test_generic_library.create_bucket(bucket_name)
#
#     file_list = ["test_wrangler_input.json"]
#
#     test_generic_library.upload_files(client, bucket_name, file_list)
#
#     with open("tests/fixtures/test_method_output.json", "r") as file_2:
#         test_data_out = file_2.read()
#
#     with mock.patch.dict(lambda_wrangler_function.os.environ,
#                          wrangler_environment_variables):
#         with mock.patch("strata_period_wrangler.boto3.client") as mock_client:
#             mock_client_object = mock.Mock()
#             mock_client.return_value = mock_client_object
#
#             mock_client_object.invoke.return_value.get.return_value.read \
#                 .return_value.decode.return_value = json.dumps({
#                  "data": test_data_out,
#                  "success": True,
#                  "anomalies": []
#                 })
#
#             output = lambda_wrangler_function.lambda_handler(
#                 wrangler_runtime_variables, test_generic_library.context_object
#             )
#
#     with open("tests/fixtures/test_wrangler_prepared_output.json", "r") as file_3:
#         test_data_prepared = file_3.read()
#     prepared_data = pd.DataFrame(json.loads(test_data_prepared))
#
#     with open("tests/fixtures/" +
#               wrangler_runtime_variables["RuntimeVariables"]["out_file_name"],
#               "r") as file_4:
#         test_data_produced = file_4.read()
#     produced_data = pd.DataFrame(json.loads(test_data_produced))
#
#     assert output
#     assert_frame_equal(produced_data, prepared_data)
