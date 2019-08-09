import json
import os
import random
import logging
import boto3
import marshmallow
import pandas as pd
from botocore.exceptions import ClientError, IncompleteReadError


class InputSchema(marshmallow.Schema):
    """
    Add docs here.
    """
    queue_url = marshmallow.fields.Str(required=True)
    sqs_messageid_name = marshmallow.fields.Str(required=True)
    arn = marshmallow.fields.Str(required=True)
    checkpoint = marshmallow.fields.Str(required=True)
    atypical_columns = marshmallow.fields.Str(required=True)
    method_name = marshmallow.fields.Str(required=True)


class NoDataInQueueError(Exception):
    pass


def lambda_handler(event, context):
    """
    Add docs here.
    """
    current_module = "Atypicals - Wrangler"
    error_message = ""
    log_message = ""
    logger = logging.getLogger("Atypicals")
    logger.setLevel(10)
    try:

        logger.info("Atypicals Wrangler Begun")

        # clients
        sqs = boto3.client('sqs', region_name="eu-west-2")
        lambda_client = boto3.client('lambda', region_name="eu-west-2")
        sns = boto3.client('sns', region_name="eu-west-2")

        # env vars
        config, errors = InputSchema().load(os.environ)
        if errors:
            raise ValueError(f"Error validating environment params: {errors}")

        logger.info("Vaildated params")

        #  Reads in Data from SQS Queue
        response = get_sqs_message(config['queue_url'])
        if "Messages" not in response:
            raise NoDataInQueueError("No Messages in queue")
        message = response['Messages'][0]
        message_json = json.loads(message['Body'])
        receipt_handle = message['ReceiptHandle']

        logger.info("Succesfully retrieved data from sqs")

        data = pd.DataFrame(message_json)

        logger.info("Input data converted to dataframe")

        for col in config['atypical_columns'].split(','):
            data[col] = 0

        logger.info("Atypicals columns succesfully added")

        data_json = data.to_json(orient='records')

        logger.info("Dataframe converted to JSON")

        wrangled_data = lambda_client.invoke(
            FunctionName=config['method_name'],
            Payload=json.dumps(data_json)
        )

        json_response = wrangled_data.get('Payload').read().decode("UTF-8")

        logger.info("Succesfully invoked method lambda")

        sqs.send_message(
            QueueUrl=config['queue_url'],
            MessageBody=json_response,
            MessageGroupId=config['sqs_messageid_name'],
            MessageDeduplicationId=str(random.getrandbits(128))
        )

        logger.info("Successfully sent data to sqs")

        sqs.delete_message(QueueUrl=config['queue_url'], ReceiptHandle=receipt_handle)

        logger.info("Successfully deleted input data from sqs")

        send_sns_message(config['arn'], sns, config['checkpoint'])

        logger.info("Succesfully sent data to sns")

    except NoDataInQueueError as e:
        error_message = (
            "There was no data in sqs queue in:  "
            + current_module
            + " |-  | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except AttributeError as e:
        error_message = (
            "Bad data encountered in "
            + current_module
            + " |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except ValueError as e:
        error_message = (
            "Parameter validation error"
            + current_module
            + " |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except ClientError as e:
        error_message = (
            "AWS Error ("
            + str(e.response["Error"]["Code"])
            + ") "
            + current_module
            + " |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except KeyError as e:
        error_message = (
            "Key Error in "
            + current_module
            + " |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except IncompleteReadError as e:
        error_message = (
            "Incomplete Lambda response encountered in "
            + current_module
            + " |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    except Exception as e:
        error_message = (
            "General Error in "
            + current_module
            + " ("
            + str(type(e))
            + ") |- "
            + str(e.args)
            + " | Request ID: "
            + str(context["aws_request_id"])
        )
        log_message = error_message + " | Line: " + str(e.__traceback__.tb_lineno)
    finally:
        if (len(error_message)) > 0:
            logger.error(log_message)
            return {"success": False, "error": error_message}
        else:
            logger.info("Successfully completed module: " + current_module)
            return {"success": True, "checkpoint": config['checkpoint']}


def send_sns_message(arn, sns, checkpoint):
    """
    This function is responsible for sending notifications to the SNS Topic.
    Notifications will be used to relay information to the BPM.
    :param checkpoint: Location of process - Type: String.
    :param sns: boto3 SNS client - Type: boto3.client
    :param arn: The Address of the SNS topic - Type: String.
    :return: None.
    """
    sns_message = {
        "success": True,
        "module": "outlier_aggregation",
        "checkpoint": checkpoint
    }

    sns.publish(
        TargetArn=arn,
        Message=json.dumps(sns_message)
    )


def get_sqs_message(queue_url):
    """
    Retrieves message from the SQS queue.
    :param queue_url: The url of the SQS queue. - Type: String.
    :return: Message from queue - Type: String.
    """
    sqs = boto3.client("sqs", region_name="eu-west-2")
    return sqs.receive_message(QueueUrl=queue_url)
