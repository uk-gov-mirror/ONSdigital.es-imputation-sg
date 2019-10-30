import json
import unittest
import unittest.mock as mock

from moto import mock_lambda, mock_s3, mock_sqs

import calculate_movement_method
import calculate_movement_wrangler


class TestStringMethods(unittest.TestCase):

    def test_lambda_handler_movement_method(self):
        with mock.patch.dict(calculate_movement_method.os.environ, {
           'current_period': '201809',
           'previous_period': '201806',
           'questions_list': 'Q601_asphalting_sand '
                             'Q602_building_soft_sand '
                             'Q603_concreting_sand '
                             'Q604_bituminous_gravel '
                             'Q605_concreting_gravel '
                             'Q606_other_gravel '
                             'Q607_constructional_fill'
        }):

            with open("tests/fixtures/method_input_test_data.json") as file:
                input_data = json.load(file)
            with open("tests/fixtures/method_output_compare_result.json") as file:
                result = json.load(file)

            string_result = json.dumps(result)
            striped_string = string_result.replace(" ", "")

            response = calculate_movement_method.lambda_handler(input_data,
                                                                {"aws_request_id": "666"})

        assert response == striped_string

    @mock_sqs
    @mock_lambda
    def test_wrangler_catch_exception(self):
        with mock.patch.dict(calculate_movement_wrangler.os.environ, {
            'arn': 'arn:aws:sns:eu-west-2:8:some-topic',
            's3_file': 'file_to_get_from_s3.json',
            'bucket_name': 'some-bucket-name',
            'queue_url': 'https://sqs.eu-west-2.amazonaws.com/'
                         '82618934671237/SomethingURL.fifo',
            'sqs_messageid_name': 'output_something_something',
            'checkpoint': '3',
            'method_name': 'method_name_here',
            'time': 'period',
            'response_type': 'response_type',
            'questions_list': 'Q601_asphalting_sand '
                              'Q602_building_soft_sand '
                              'Q603_concreting_sand '
                              'Q604_bituminous_gravel '
                              'Q605_concreting_gravel '
                              'Q606_other_gravel '
                              'Q607_constructional_fill',
            'output_file': 'output_file.json',
            'reference': 'responder_id',
            'segmentation': 'strata',
            'stored_segmentation': 'goodstrata',
            'current_time': 'current_period',
            'previous_time': 'previous_period',
            'current_segmentation': 'current_strata',
            'previous_segmentation': 'previous_strata',
            'incoming_message_group': 'bananas',
            'file_name': 'le file'
        }):

            # using get_from_s3 to force exception early on.

            with mock.patch('calculate_movement_wrangler'
                            '.funk.read_dataframe_from_s3') as mocked:

                mocked.side_effect = Exception('SQS Failure')

                response = calculate_movement_wrangler.lambda_handler(
                    {"RuntimeVariables": {"period": 201809}}, {"aws_request_id": "666"})

                assert 'success' in response
                assert response['success'] is False

    @mock_sqs
    @mock_lambda
    def test_method_catch_exception(self):
        with mock.patch.dict(calculate_movement_method.os.environ, {
            'current_period': '201809',
            'previous_period': '201806',
            'questions_list': 'Q601_asphalting_sand '
                              'Q602_building_soft_sand '
                              'Q603_concreting_sand '
                              'Q604_bituminous_gravel '
                              'Q605_concreting_gravel '
                              'Q606_other_gravel '
                              'Q607_constructional_fill'
        }):

            with mock.patch('calculate_movement_method.pd.DataFrame') as mocked:
                mocked.side_effect = Exception('SQS Failure')

                response = calculate_movement_method.lambda_handler(
                    {"RuntimeVariables": {"period": 201809}}, {"aws_request_id": "666"})

                assert 'success' in response
                assert response['success'] is False

    @mock_sqs
    @mock_s3
    def test_marshmallow_raises_method_exception(self):
        """
        Testing the marshmallow raises an exception in method.
        :return: None.
        """
        with mock.patch.dict(calculate_movement_method.os.environ, {
            'current_period': '201809',
            'previous_period': '201806',
            'questions_list': 'Q601_asphalting_sand '
                              'Q602_building_soft_sand '
                              'Q603_concreting_sand '
                              'Q604_bituminous_gravel '
                              'Q605_concreting_gravel '
                              'Q606_other_gravel '
                              'Q607_constructional_fill'
            }
        ):
            # Removing the previous_period to allow for test of missing parameter
            calculate_movement_method.os.environ.pop("previous_period")

            response = calculate_movement_method.lambda_handler({"RuntimeVariables":
                                                                {"period": "201809"}},
                                                                {"aws_request_id": "666"})

            assert (response['error'].__contains__("""Parameter validation error"""))

    @mock_sqs
    @mock_s3
    def test_marshmallow_raises_wrangler_exception(self):
        """
        Testing the marshmallow raises an exception in wrangler.
        :return: None.
        """
        with mock.patch.dict(calculate_movement_wrangler.os.environ, {
            'arn': 'arn:aws:sns:eu-west-2:014669633018:some-topic',
            's3_file': 'file_to_get_from_s3.json',
            'bucket_name': 'some-bucket-name',
            'queue_url': 'https://sqs.eu-west-2.amazonaws.com/'
                         '82618934671237/SomethingURL.fifo',
            'sqs_messageid_name': 'output_something_something',
            'checkpoint': '3',
            'method_name': 'method_name_here',
            'time': 'period',
            'response_type': 'response_type',
            'questions_list': 'Q601_asphalting_sand '
                              'Q602_building_soft_sand '
                              'Q603_concreting_sand '
                              'Q604_bituminous_gravel '
                              'Q605_concreting_gravel '
                              'Q606_other_gravel '
                              'Q607_constructional_fill',
            'output_file': 'output_file.json',
            'reference': 'responder_id',
            'segmentation': 'strata',
            'stored_segmentation': 'goodstrata',
            'current_time': 'current_period',
            'previous_time': 'previous_period',
            'current_segmentation': 'current_strata',
            'previous_segmentation': 'previous_strata',
            'incoming_message_group': 'bananas',
            'file_name': 'le file'
            }
        ):
            # Removing the previous_period to allow for test of missing parameter
            calculate_movement_wrangler.os.environ.pop("checkpoint")

            response = calculate_movement_wrangler.lambda_handler({
                "RuntimeVariables": {"period": "201809"}}, {"aws_request_id": "666"}
            )

            assert (response['error'].__contains__("""Parameter validation error"""))

    @mock_sqs
    def test_fail_to_get_from_sqs(self):
        with mock.patch.dict(calculate_movement_wrangler.os.environ, {
                'arn': 'arn:aws:sns:eu-west-2:014669633018:some-topic',
                's3_file': 'file_to_get_from_s3.json',
                'bucket_name': 'some-bucket-name',
                'queue_url': 'https://sqs.eu-west-2.amazonaws.com/'
                             '82618934671237/SomethingURL.fifo',
                'sqs_messageid_name': 'output_something_something',
                'checkpoint': '3',
                'method_name': 'method_name_here',
                'time': 'period',
                'response_type': 'response_type',
                'questions_list': 'Q601_asphalting_sand '
                                  'Q602_building_soft_sand '
                                  'Q603_concreting_sand '
                                  'Q604_bituminous_gravel '
                                  'Q605_concreting_gravel '
                                  'Q606_other_gravel '
                                  'Q607_constructional_fill',
                'output_file': 'output_file.json',
                'reference': 'responder_id',
                'segmentation': 'strata',
                'stored_segmentation': 'goodstrata',
                'current_time': 'current_period',
                'previous_time': 'previous_period',
                'current_segmentation': 'current_strata',
                'previous_segmentation': 'previous_strata',
                'incoming_message_group': 'bananas',
                'file_name': 'le file'
            },
        ):
            response = calculate_movement_wrangler.lambda_handler(
                {"RuntimeVariables": {"period": 201809}}, {"aws_request_id": "666"}
            )
            assert "success" in response
            assert response["success"] is False
            assert response["error"].__contains__("""AWS Error""")

    def test_method_key_error_exception(self):
        with mock.patch.dict(calculate_movement_method.os.environ, {
            'current_period': '201809',
            'previous_period': '201806',
            'questions_list': 'Q601_asphalting_sand '
                              'Q602_building_soft_sand '
                              'Q603_concreting_sand '
                              'Q604_bituminous_gravel '
                              'Q605_concreting_gravel '
                              'Q606_other_gravel '
                              'Q607_constructional_fill'
            }
        ):
            input_file = "tests/fixtures/method_input_test_data.json"

            with open(input_file, "r") as file:
                content = file.read()
                content = content.replace("Q", "TEST")
                json_content = json.loads(content)

            output_file = calculate_movement_method.lambda_handler(
                json_content, {"aws_request_id": "666"}
            )

            assert not output_file["success"]
            assert "Key Error" in output_file["error"]
