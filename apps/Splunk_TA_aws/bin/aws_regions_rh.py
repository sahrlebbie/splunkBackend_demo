"""
Custom REST Endpoint for enumerating AWS regions.
"""

from __future__ import absolute_import
import aws_bootstrap_env

from boto3.session import Session
from botocore.session import create_loader

import splunk
import splunk.admin
from splunksdc import log as logging
from splunktaucclib.rest_handler.error import RestError
import splunk_ta_aws.common.ta_aws_consts as tac
import splunk_ta_aws.common.ta_aws_common as tacommon
from solnlib.splunkenv import get_splunkd_uri

logger = logging.get_module_logger()

ACCOUNT_OPT_ARGS = ['account', 'aws_account']
DUMMY_BOTO3_SESSION = Session()

INPUT_SERVICE_MAP = {
    'aws_cloudwatch': 'cloudwatch',
    'aws_cloudtrail': 'cloudtrail',
    'aws_config': 'config',
    'aws_config_rule': 'config', # There is no dedicated config rule service in endpoint
    'aws_cloudwatch_logs': 'logs',
    'aws_description': 'ec2', # There is no dedicated description service in endpoint
    'aws_metadata': 'ec2', # There is no dedicated metadata service in endpoint
    'aws_inspector': 'inspector',
    'aws_kinesis': 'kinesis',
    'aws_sqs_based_s3': 'sqs',
    'splunk_ta_aws_sqs': 'sqs',
    'aws_s3': 's3',
    'aws_sts': 'sts'
}

def _load_description_of_regions():
    loader = create_loader()
    endpoints = loader.load_data('endpoints')
    regions = dict()
    for partition in endpoints['partitions']:
        regions.update(partition['regions'])
    return regions


class ConfigHandler(splunk.admin.MConfigHandler):

    def setup(self):
        self.supportedArgs.addReqArg('aws_service')
        self.supportedArgs.addOptArg('category')
        for account_arg in ACCOUNT_OPT_ARGS:
            self.supportedArgs.addOptArg(account_arg)

    def handleList(self, confInfo):
        input_name = self.callerArgs.data['aws_service'][0]

        account_category = self.callerArgs.data.get('category',[None])[0]
        if not account_category:
            for account_arg in ACCOUNT_OPT_ARGS:
                if account_arg in self.callerArgs.data:
                    account_name = self.callerArgs.data[account_arg][0]
                    account = tacommon.get_account(get_splunkd_uri(), self.getSessionKey(), account_name)
                    account_category = account.category
                    break
        else:
            account_category = int(account_category)

        if account_category == tac.RegionCategory.USGOV:
            partition = 'aws-us-gov'
        elif account_category == tac.RegionCategory.CHINA:
            partition = 'aws-cn'
        else:
            partition = 'aws'

        if input_name in INPUT_SERVICE_MAP:
            regions = DUMMY_BOTO3_SESSION.get_available_regions(INPUT_SERVICE_MAP[input_name], partition)
            descriptions = _load_description_of_regions()
            for region in regions:
                confInfo[region].append('label', descriptions[region]['description'])
        else:
            msg = "Unsupported aws_service={} specified.".format(input_name)
            raise RestError(400, msg)

        if len(confInfo) == 0:
            raise RestError(400, 'This service is not available for your AWS account.')

def main():
    splunk.admin.init(ConfigHandler, splunk.admin.CONTEXT_NONE)


if __name__ == '__main__':
    main()
