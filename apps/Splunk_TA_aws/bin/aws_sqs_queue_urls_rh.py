"""
Custom REST Endpoint for enumerating AWS SQS queue names.
"""
from __future__ import absolute_import
import aws_bootstrap_env

import splunk
import splunk.admin
from botocore.exceptions import ClientError, ConnectTimeoutError
from splunktaucclib.rest_handler.error import RestError
from splunklib.client import Service
from splunksdc.config import ConfigManager
from solnlib.splunkenv import get_splunkd_access_info
from splunk_ta_aws.common.credentials import (
    AWSCredentialsProviderFactory,
    AWSCredentialsCache,
)
import splunk_ta_aws.common.ta_aws_common as tacommon
import splunk_ta_aws.common.proxy_conf as pc
import aws_common_validator as acv


class SQSQueueURLsHandler(splunk.admin.MConfigHandler):

    def setup(self):
        self.supportedArgs.addReqArg('aws_region')
        self.supportedArgs.addOptArg('aws_iam_role')
        self.supportedArgs.addReqArg('aws_account')
        self.supportedArgs.addOptArg('private_endpoint_enabled')
        self.supportedArgs.addOptArg('sqs_private_endpoint_url')
        self.supportedArgs.addOptArg('sts_private_endpoint_url')
        self.supportedArgs.addOptArg('using_dlq')
        self.supportedArgs.addOptArg('sqs_queue_url')

    def handleList(self, confInfo):
        # Set proxy for boto3
        proxy = pc.get_proxy_info(self.getSessionKey())
        tacommon.set_proxy_env(proxy)

        for queue_url in self._list_queues():
            if self.callerArgs.data.get('using_dlq', [None])[0] == '0':
                # Do not need to split queue url if "using_dlq" checkbox is unticked
                confInfo[queue_url].append('label', queue_url)
            else:
                confInfo[queue_url].append('label', queue_url.split('/')[-1])

    def _list_queues(self):
        if self.callerArgs.data.get('sqs_queue_url', [None])[0] != 'undefined' and self.callerArgs.data.get('using_dlq', [None])[0] == '0':
            return [self.callerArgs.data.get('sqs_queue_url', [None])[0]]
        if self.callerArgs.data.get('using_dlq', [None])[0] == '0':
            # Returning empty list as the "using_dlq" checkbox is unticked
            return []
        aws_account = self.callerArgs.data['aws_account'][0]
        aws_iam_role = self.callerArgs.data.get('aws_iam_role', [None])[0]
        region_name = self.callerArgs.data['aws_region'][0]
        if int(self.callerArgs.get('private_endpoint_enabled',[0])[0]):
            endpoint_urls = {
                "sqs_private_endpoint_url" : self.callerArgs.get('sqs_private_endpoint_url')[0],
                "sts_private_endpoint_url" : self.callerArgs.get('sts_private_endpoint_url')[0],
            }
            if endpoint_urls["sqs_private_endpoint_url"] and endpoint_urls["sts_private_endpoint_url"]:
                acv.on_fetch_validate_urls(endpoint_urls)
                sqs_endpoint_url = endpoint_urls["sqs_private_endpoint_url"]
                sts_endpoint_url = endpoint_urls["sts_private_endpoint_url"]
            else:
                return []
        else:
            sts_endpoint_url = None
            sqs_endpoint_url = None
        scheme, host, port = get_splunkd_access_info()
        service = Service(scheme=scheme, host=host, port=port,
                          token=self.getSessionKey())
        config = ConfigManager(service)
        try:
            factory = AWSCredentialsProviderFactory(config, region_name, sts_endpoint_url)
            provider = factory.create(aws_account, aws_iam_role)
            credentials_cache = AWSCredentialsCache(provider)
            client = credentials_cache.client('sqs', region_name, endpoint_url=sqs_endpoint_url)
            queues = client.list_queues()
            if 'QueueUrls' in queues:
                return queues['QueueUrls']
            else:
                return []
        except ClientError or ConnectTimeoutError as exc:
            raise RestError(400, str(exc))
        except Exception as exc:
            raise RestError(400, str(exc))


def main():
    splunk.admin.init(SQSQueueURLsHandler, splunk.admin.CONTEXT_NONE)


if __name__ == '__main__':
    main()
