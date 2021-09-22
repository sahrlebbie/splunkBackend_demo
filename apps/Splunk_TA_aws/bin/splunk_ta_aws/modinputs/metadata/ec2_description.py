from __future__ import absolute_import
import os
import boto3
import datetime
import splunksdc.log as logging
import splunk_ta_aws.common.ta_aws_consts as tac
from . import description as desc

logger = logging.get_module_logger()

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)


def get_ec2_conn(config):
    return desc.BotoRetryWrapper(boto_client=boto3.client(
        'ec2',
        region_name=config.get(tac.region),
        aws_access_key_id=config.get(tac.key_id),
        aws_secret_access_key=config.get(tac.secret_key),
        aws_session_token=config.get('aws_session_token')
    ))


@desc.generate_credentials
@desc.decorate
def ec2_instances(config):
    ec2_conn = get_ec2_conn(config)
    paginator = ec2_conn.get_paginator('describe_instances')

    for page in paginator.paginate():
        for reservation in page.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance['OwnerId'] = reservation.get('OwnerId')
                yield instance
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,ec2_conn)



@desc.generate_credentials
@desc.decorate
def ec2_reserved_instances(config):
    ec2_conn = get_ec2_conn(config)
    res = ec2_conn.describe_reserved_instances()

    for reserved_instance in res.get('ReservedInstances', []):
        yield reserved_instance


@desc.generate_credentials
@desc.decorate
def ec2_ebs_snapshots(config):
    ec2_conn = get_ec2_conn(config)
    paginator = ec2_conn.get_paginator('describe_snapshots')

    for page in paginator.paginate():
        for item in page.get('Snapshots', []):
            yield item
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,ec2_conn)



@desc.generate_credentials
@desc.decorate
def ec2_volumes(config):
    ec2_conn = get_ec2_conn(config)
    paginator = ec2_conn.get_paginator('describe_volumes')

    for page in paginator.paginate():
        for volume in page.get('Volumes', []):
            yield volume
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,ec2_conn)


@desc.generate_credentials
@desc.decorate
def ec2_security_groups(config):
    ec2_conn = get_ec2_conn(config)
    paginator = ec2_conn.get_paginator('describe_security_groups')

    for page in paginator.paginate():
        for security_group in page.get('SecurityGroups', []):
            yield security_group
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,ec2_conn)


@desc.generate_credentials
@desc.decorate
def ec2_key_pairs(config):
    ec2_conn = get_ec2_conn(config)
    res = ec2_conn.describe_key_pairs()

    for key_pair in res.get('KeyPairs', []):
        yield key_pair


@desc.generate_credentials
@desc.decorate
def ec2_images(config):
    ec2_conn = get_ec2_conn(config)
    res = ec2_conn.describe_images(Owners=['self'])
    
    for image in res.get('Images', []):
        yield image


@desc.generate_credentials
@desc.decorate
def ec2_addresses(config):
    ec2_conn = get_ec2_conn(config)   
    res = ec2_conn.describe_addresses()

    for address in res.get('Addresses', []):
        yield address