import re
import os
import json
import boto3

from botocore.config import Config
from splunktaucclib.rest_handler.error import RestError
from splunktaucclib.rest_handler.base_hook_mixin import BaseHookMixin
import splunk_ta_aws.common.ta_aws_consts as tac
import splunk_ta_aws.modinputs.generic_s3.aws_s3_consts as asc
import splunk_ta_aws.common.ta_aws_common as tacommon
from solnlib.splunkenv import get_splunkd_uri
import splunksdc.log as logging
from botocore.regions import EndpointResolver
import splunk_ta_aws.common.proxy_conf as pc


logger = logging.get_module_logger()

ENDPOINTS_PATH = os.path.join(os.path.dirname(__file__), '3rdparty', 'python3', 'botocore', 'data', 'endpoints.json')


class CustomHookMixin(BaseHookMixin):

    BUCKET_NAME_INPUTS = ['aws_billing', 'aws_s3', 'splunk_ta_aws_logs']
    BUCKET_REGION_INPUTS = ['splunk_ta_aws_logs', 'aws_billing_cur']

    def create_hook(self, session_key, config_name, stanza_id, payload):
        self._delete_ckpt(config_name, stanza_id)
        payload = self._fill_host_and_region(session_key, config_name, payload)

        return payload

    def delete_hook(self, session_key, config_name, stanza_id):
        self._delete_ckpt(config_name, stanza_id)
        return True

    def _fill_host_and_region(self, session_key, config_name, payload):
        if config_name in self.BUCKET_NAME_INPUTS or config_name in self.BUCKET_REGION_INPUTS:
            if asc.host_name in payload and len(payload[asc.host_name]) > 0:
                return payload

            (region, host) = self._get_region_host(session_key, payload)
            if config_name in self.BUCKET_NAME_INPUTS:
                payload[asc.host_name] = host

            if config_name in self.BUCKET_REGION_INPUTS:
                payload[asc.bucket_region] = region

        return payload

    def get_region_for_bucketname(self, config, default_region='us-east-1'):
        bucket_region = default_region
        if config.get('aws_s3_region'):
            bucket_region = config['aws_s3_region']
        if int(config.get('private_endpoint_enabled','0')):
            endpoint_url = config['s3_private_endpoint_url']
        else:
            endpoint_url = "https://{}.{}.amazonaws.com/".format('s3',bucket_region)
        try:
            client = boto3.client('s3',
                aws_access_key_id=config[tac.key_id],
                aws_secret_access_key=config[tac.secret_key],
                aws_session_token=config['aws_session_token'],
                region_name=bucket_region,
                config=Config(signature_version='s3v4'),
                endpoint_url=endpoint_url
            )
            bucket_region = client.get_bucket_location(Bucket=config[asc.bucket_name]).get('LocationConstraint')

            if not bucket_region:
                bucket_region = 'us-east-1'
            elif bucket_region == 'EU':
                bucket_region = 'eu-west-1'
        except Exception as ex:
            logger.error('Error while getting region for bucket {}'.format(config[asc.bucket_name]))

        return bucket_region

    def _get_region_host(self, session_key, payload):
        config = pc.get_proxy_info(session_key)
        tacommon.set_proxy_env(config)

        credentials_service = tacommon.create_credentials_service(
            get_splunkd_uri(), session_key)

        if int(payload.get('private_endpoint_enabled',0)):
            sts_endpoint_url = payload['sts_private_endpoint_url']
        else:
            sts_endpoint_url = None
        credentials = credentials_service.load(
            payload[tac.aws_account],
            payload[tac.aws_iam_role],
            payload.get('aws_s3_region'),
            sts_endpoint_url,
        )

        config[tac.key_id] = credentials.aws_access_key_id
        config[tac.secret_key] = credentials.aws_secret_access_key
        config['aws_session_token'] = credentials.aws_session_token
        config[asc.bucket_name] = payload[asc.bucket_name]
        config[asc.host_name] = tac.CATEGORY_HOST_NAME_MAP[credentials.category]
        config['aws_s3_region'] = payload.get('aws_s3_region')
        config['private_endpoint_enabled'] = payload.get('private_endpoint_enabled',0)
        config['s3_private_endpoint_url'] = payload.get('s3_private_endpoint_url')
        config['sts_private_endpoint_url'] = payload.get('sts_private_endpoint_url')
        if config[asc.host_name] == asc.default_host:
            region = self.get_region_for_bucketname(config)
            with open(ENDPOINTS_PATH, 'r') as endpoints_file:
                endpoints = json.load(endpoints_file)

            host_name = EndpointResolver(endpoints).construct_endpoint('s3', region).get('hostname', asc.default_host)
        else:
            pattern = r's3[.-]([\w-]+)\.amazonaws.com'
            m = re.search(pattern, config[asc.host_name])
            region = m.group(1) if m else 'us-east-1'
            host_name = config[asc.host_name]

        return (region, host_name)

    def _delete_ckpt(self, config_name, stanza_id):
        if config_name == 'aws_cloudtrail':
            from splunk_ta_aws.modinputs.cloudtrail import delete_ckpt
        elif config_name == 'aws_s3':
            from splunk_ta_aws.modinputs.generic_s3 import delete_ckpt
        elif config_name == 'splunk_ta_aws_logs':
            from splunk_ta_aws.modinputs.incremental_s3 import delete_data_input as delete_ckpt
        elif config_name == 'aws_billing_cur':
            from splunk_ta_aws.modinputs.billing import delete_ckpt as delete_ckpt
        elif config_name == 'aws_cloudwatch':
            from splunk_ta_aws.modinputs.cloudwatch import delete_ckpt

        try:
            delete_ckpt(stanza_id)
        except NameError:
            return False
        except Exception as exc:
            if (isinstance(exc, IOError) and
                    'No such file or directory' in str(exc)):
                return
            RestError(500, 'Failed to delete checkpoint for input %s' % config_name)

        return True
