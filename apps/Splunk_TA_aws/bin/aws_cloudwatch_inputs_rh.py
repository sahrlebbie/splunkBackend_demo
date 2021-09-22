from __future__ import absolute_import
import splunk.admin as admin
from base_input_rh import BaseInputRestHandler
from splunktaucclib.rest_handler.error import RestError
import re
from aws_common_validator import PRIVATE_ENDPOINT_PATTERN

ARGS = [
    'aws_account',
    'aws_region',
    'private_endpoint_enabled',
    's3_private_endpoint_url',
    'ec2_private_endpoint_url',
    'elb_private_endpoint_url',
    'lambda_private_endpoint_url',
    'monitoring_private_endpoint_url',
    'autoscaling_private_endpoint_url',
    'sts_private_endpoint_url',
    'index',
    'aws_iam_role',
    'metric_dimensions',
    'metric_names',
    'metric_namespace',
    'period',
    'polling_interval',
    'sourcetype',
    'statistics',
    'disabled',
    'use_metric_format',
]

GROUP_FIELDS = ['metric_dimensions', 'metric_names', 'metric_namespace', 'statistics']

class InputsProxyHandler(BaseInputRestHandler):
    def __init__(self, *args, **kwargs):
        self.opt_args = ARGS
        self.required_args = []
        self.group_fields = GROUP_FIELDS
        self.input_name = 'aws_cloudwatch'

        BaseInputRestHandler.__init__(
            self,
            *args,
            **kwargs
        )

        return

    def handleCreate(self, confInfo):
        self._validate_inputs(self.callerArgs)
        BaseInputRestHandler.handleCreate(self, confInfo)

    def handleEdit(self, confInfo):
        self._validate_inputs(self.callerArgs)
        BaseInputRestHandler.handleEdit(self, confInfo)
    
    def _generate_endpoint_list(self, data):
        ''' Generates list of endpoints which needs to be validated '''
        metric_input_str = data.get('metric_namespace',[None])[0]
        if metric_input_str:
            metric_input_list = metric_input_str[2:-2].split('","')
        else:
            metric_input_list = []
        service_mapping = {
            'AWS/ApplicationELB':'elb_private_endpoint_url',
            'AWS/EBS':'ec2_private_endpoint_url',
            'AWS/EC2':'ec2_private_endpoint_url',
            'AWS/ELB':'elb_private_endpoint_url',
            'AWS/Lambda':'lambda_private_endpoint_url',
            'AWS/S3':'s3_private_endpoint_url',
        }
        endpoint_input_list = ["sts_private_endpoint_url", "monitoring_private_endpoint_url",]
        for key in service_mapping:
            if key in metric_input_list:
                endpoint_input_list.append(service_mapping[key])
                if key == "AWS/EC2":
                    endpoint_input_list.append('autoscaling_private_endpoint_url')
        return endpoint_input_list

    def _validate_inputs(self, data):
        endpoint_input_list = self._generate_endpoint_list(data)
        private_endpoint_enabled = int(data.get('private_endpoint_enabled',['0'])[0])
        if not private_endpoint_enabled:
            return

        # Validate region and private endpoints
        regions = data.get('aws_region',[''])[0] # contains comma seperated region values
        region_list = regions.split(',')
        if len(region_list) != 1:
            raise RestError(400, 'Only one region is allowed when private endpoints are enabled.')
        pattern = PRIVATE_ENDPOINT_PATTERN.replace('<service_name>', r'(\w+?)')
        for endpoint_input in endpoint_input_list:
            input_data = data.get(endpoint_input,[''])[0]
            if not input_data or not input_data.strip():
                raise RestError(400,"You have enabled use of private endpoints. \
                                    You must provide private endpoints for all specified services.")
            if not re.match(pattern,input_data.strip()):
                raise RestError(
                    400,
                    "Provided Private Endpoint URL for %s is not valid." % endpoint_input.split("_")[0]
                )
admin.init(InputsProxyHandler, admin.CONTEXT_APP_ONLY)
