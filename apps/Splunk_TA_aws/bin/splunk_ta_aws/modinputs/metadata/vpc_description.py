from __future__ import absolute_import

import boto3
import datetime
import splunksdc.log as logging
import splunk_ta_aws.common.ta_aws_consts as tac
from . import description as desc

logger = logging.get_module_logger()

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)

def get_vpc_conn(config):
    return desc.BotoRetryWrapper(boto_client=boto3.client(
        'ec2',
        region_name=config[tac.region],
        aws_access_key_id=config[tac.key_id],
        aws_secret_access_key=config[tac.secret_key],
        aws_session_token=config.get('aws_session_token')
    ))


@desc.generate_credentials
@desc.decorate
def vpcs(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_vpcs')

    for page in paginator.paginate():
        for vpc in page.get('Vpcs', []):
            yield vpc
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)


@desc.generate_credentials
@desc.decorate
def vpc_subnets(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_subnets')

    for page in paginator.paginate():
        for subnet in page.get('Subnets', []):
            yield subnet
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)


@desc.generate_credentials
@desc.decorate
def vpc_network_acls(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_network_acls')

    for page in paginator.paginate():
        for network_acl in page.get('NetworkAcls', []):
            yield network_acl
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

@desc.generate_credentials
@desc.decorate
def vpn_gateways(config):
    vpc_conn = get_vpc_conn(config)
    res = vpc_conn.describe_vpn_gateways()
    
    for vpn_gateway in res.get('VpnGateways', []):
        yield vpn_gateway

@desc.generate_credentials
@desc.decorate
def internet_gateways(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_internet_gateways')

    for page in paginator.paginate():
        for internet_gateway in page.get('InternetGateways', []):
            yield internet_gateway
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

@desc.generate_credentials
@desc.decorate
def customer_gateways(config):
    vpc_conn = get_vpc_conn(config)
    res = vpc_conn.describe_customer_gateways()

    for customer_gateway in res.get('CustomerGateways', []):
        yield customer_gateway

@desc.generate_credentials
@desc.decorate
def nat_gateways(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_nat_gateways')

    for page in paginator.paginate():
        for nat_gateway in page.get('NatGateways', []):
            yield nat_gateway
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

@desc.generate_credentials
@desc.decorate
def local_gateways(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_local_gateways')

    for page in paginator.paginate():
        for local_gateway in page.get('LocalGateways', []):
            yield local_gateway
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

@desc.generate_credentials
@desc.decorate
def carrier_gateways(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_carrier_gateways')

    for page in paginator.paginate():
        for carrier_gateway in page.get('CarrierGateways', []):
            yield carrier_gateway
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

@desc.generate_credentials
@desc.decorate
def transit_gateways(config):
    vpc_conn = get_vpc_conn(config)
    paginator = vpc_conn.get_paginator('describe_transit_gateways')

    for page in paginator.paginate():
        for transit_gateway in page.get('TransitGateways', []):
            yield transit_gateway
        desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,vpc_conn)

