from __future__ import absolute_import

import boto3
import datetime
import splunksdc.log as logging
import splunk_ta_aws.common.ta_aws_consts as tac
from . import description as desc

logger = logging.get_module_logger()

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)

def get_rds_conn(config):
    return desc.BotoRetryWrapper(boto_client=boto3.client(
        'rds',
        region_name=config[tac.region],
        aws_access_key_id=config[tac.key_id],
        aws_secret_access_key=config[tac.secret_key],
        aws_session_token=config.get('aws_session_token')
    ))


@desc.generate_credentials
@desc.decorate
def rds_instances(config):
    rds_conn = get_rds_conn(config)
    paginator = rds_conn.get_paginator('describe_db_instances')

    for page in paginator.paginate():
        for db_instance in page.get('DBInstances', []):
            yield db_instance
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,rds_conn)

