from __future__ import absolute_import

import boto3
import datetime
import splunksdc.log as logging
import splunk_ta_aws.common.ta_aws_consts as tac
from . import description as desc


logger = logging.get_module_logger()

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)


def connect_cloudfront(config):
    return desc.BotoRetryWrapper(boto_client=boto3.client(
        'cloudfront',
        region_name=config.get(tac.region),
        aws_access_key_id=config.get(tac.key_id),
        aws_secret_access_key=config.get(tac.secret_key),
        aws_session_token=config.get('aws_session_token')
    ))


@desc.generate_credentials
@desc.decorate
def cloudfront_distributions(config):
    conn = connect_cloudfront(config)
    paginator = conn.get_paginator('list_distributions')

    for page in paginator.paginate():
        for item in page.get('DistributionList', {}).get('Items', []):
            yield item
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,conn)

