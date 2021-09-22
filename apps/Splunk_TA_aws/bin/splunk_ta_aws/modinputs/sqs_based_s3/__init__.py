from __future__ import absolute_import
from splunksdc import logging
from splunksdc.collector import SimpleCollectorV1
from .handler import SQSBasedS3DataInput, SQSAgent, S3Agent


logger = logging.get_module_logger()


def modular_input_run(app, config):
    inputs = app.inputs()
    datainput = SQSBasedS3DataInput(inputs[0])
    return datainput.run(app, config)


def main():
    from requests.packages import urllib3
    urllib3.disable_warnings()
    arguments = {
        'aws_account': {
            'title': 'The name of AWS account'
        },
        'aws_iam_role': {
            'title': 'The name of IAM user would be assumed'
        },
        'using_dlq': {
            'title': 'This checkbox gives an option to remove the checking of DLQ for ingestion of specific data. It is recommended to have DLQ linked with SQS Queue.'
        },
        'sqs_queue_url': {
            'title': 'The URL of queue'
        },
        'sqs_queue_region': {
            'title': 'Which region the queue located in.'
        },
        'sqs_batch_size': {
            'title': 'The max number of messages would be processing concurrently.'
        },
        's3_file_decoder': {
            'title': 'Which decoder should be use to decode the content of file.'
        },
        'private_endpoint_enabled': {
            'title': 'To enable/disable use of private endpoint'
        },
        'sqs_private_endpoint_url': {
            'title': 'Private endpoint url to connect with sqs service'
        },
        's3_private_endpoint_url': {
            'title': 'Private endpoint url to connect with s3 service'
        },
        'sts_private_endpoint_url': {
            'title': 'Private endpoint url to connect with sts service'
        },
        'use_raw_hec': {
            'title': 'The URL of RawHEC endpoint.'
        },
    }

    SimpleCollectorV1.main(
        modular_input_run,
        title='AWS SQS-Based S3',
        use_single_instance=False,
        arguments=arguments,
    )


