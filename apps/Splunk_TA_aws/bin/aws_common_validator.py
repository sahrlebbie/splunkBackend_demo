from __future__ import absolute_import
from splunktaucclib.rest_handler.endpoint import (
    DataInputModel,
    SingleModel,
)
from splunktaucclib.rest_handler.error import RestError
import re
from splunksdc import log as logging

logger = logging.get_module_logger()

PRIVATE_ENDPOINT_PATTERN = r"^((http|https)://vpce(-(\w+?)){2}((-(\w+?)){3,4})?\.<service_name>\.((\w+?)-){2,3}\d\.vpce\.amazonaws\.com(/)?)$"

def on_fetch_validate_urls(data):
    for key in data.keys():
        data[key] = data[key].strip()
        service = key.split("_")[0]
        pattern = PRIVATE_ENDPOINT_PATTERN.replace("<service_name>", service)
        if not re.match(pattern,data[key]):
            raise RestError(400,"Provided Private Endpoint URL for %s is not valid." % service)

def on_save_validate_urls(endpoint_input_list, data):
    pattern = PRIVATE_ENDPOINT_PATTERN.replace('<service_name>', r'(\w+?)')
    logger.debug('Validating private endpoints : {}'.format(data.keys()))
    for endpoint_input in endpoint_input_list:
        if endpoint_input in data.keys():
            input_data = data.get(endpoint_input,'').strip()
            if not input_data:
                raise RestError(400,"You have enabled use of private endpoints. \
                                    You must provide private endpoints for all specified services.")
            if not re.match(pattern,input_data):
                raise RestError(
                    400,
                    "Provided Private Endpoint URL for %s is not valid." % endpoint_input.split("_")[0]
                )

class DataInputModelValidator(DataInputModel):
    """ Input validator for Inputs which uses DataInputModel"""
    
    def validate(self, name, data, existing=None):
        """Validate Input parameters."""
        endpoint_input_list = [
            "sqs_private_endpoint_url",
            "s3_private_endpoint_url",
            "sts_private_endpoint_url"
        ]
        private_endpoint_enabled = int(data.get('private_endpoint_enabled','0'))
        logger.debug('Checking private endpoint status : {}'.format(private_endpoint_enabled))
        if private_endpoint_enabled:
            on_save_validate_urls(endpoint_input_list, data)
        super(DataInputModelValidator, self).validate(name, data, existing)

class SingleModelValidator(SingleModel):
    """ Input validator for Inputs which uses SingleModel"""
    
    def validate(self, name, data, existing=None):
        """Validate Input parameters."""
        endpoint_input_list = [
            "kinesis_private_endpoint_url",
            "logs_private_endpoint_url",
            "sts_private_endpoint_url"
        ]
        private_endpoint_enabled = int(data.get('private_endpoint_enabled','0'))
        logger.debug('Checking private endpoint status : {}'.format(private_endpoint_enabled))
        if private_endpoint_enabled:
            on_save_validate_urls(endpoint_input_list, data)
        super(SingleModelValidator, self).validate(name, data, existing)