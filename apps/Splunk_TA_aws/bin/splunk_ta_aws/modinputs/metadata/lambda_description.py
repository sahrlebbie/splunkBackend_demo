from __future__ import absolute_import
import json
import boto3
import datetime
import splunksdc.log as logging

from splunk_ta_aws.common.ta_aws_common import is_http_ok
import splunk_ta_aws.common.ta_aws_consts as tac
from . import description as desc


logger = logging.get_module_logger()

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)

def get_lambda_conn(config):
    return desc.BotoRetryWrapper(boto_client=boto3.client(
        'lambda',
        region_name=config[tac.region],
        aws_access_key_id=config[tac.key_id],
        aws_secret_access_key=config[tac.secret_key],
        aws_session_token=config.get('aws_session_token')
    ))


@desc.generate_credentials
@desc.decorate
def lambda_functions(config):
    lambda_conn = get_lambda_conn(config)
    paginator = lambda_conn.get_paginator('list_functions')

    for page in paginator.paginate():
        for function in page.get('Functions', []):
            yield function
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,lambda_conn)
