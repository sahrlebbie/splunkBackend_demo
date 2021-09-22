from __future__ import absolute_import
import aws_bootstrap_env
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging
from aws_common_validator import SingleModelValidator

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'account',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'region',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'private_endpoint_enabled',
        required=False,
        encrypted=False,
        validator=None
    ), 
    field.RestField(
        'logs_private_endpoint_url',
        required=False,
        encrypted=False,
        validator=None
    ), 
    field.RestField(
        'sts_private_endpoint_url',
        required=False,
        encrypted=False,
        validator=None,
    ), 
    field.RestField(
        'groups',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'delay',
        required=False,
        encrypted=False,
        default=1800,
        validator=validator.Number(
            max_val=31536000, 
            min_val=0, 
        )
    ), 
    field.RestField(
        'only_after',
        required=False,
        encrypted=False,
        default='1970-01-01T00:00:00',
        validator=validator.Datetime(r'%Y-%m-%dT%H:%M:%S')
    ), 
    field.RestField(
        'stream_matcher',
        required=False,
        encrypted=False,
        default='.*',
        validator=None
    ), 
    field.RestField(
        'interval',
        required=False,
        encrypted=False,
        default=600,
        validator=validator.Number(
            max_val=31536000, 
            min_val=0, 
        )
    ), 
    field.RestField(
        'sourcetype',
        required=False,
        encrypted=False,
        default='aws:cloudwatchlogs',
        validator=None
    ), 
    field.RestField(
        'index',
        required=True,
        encrypted=False,
        default='default',
        validator=None
    ), 

    field.RestField(
        'disabled',
        required=False,
        validator=None
    )

]
model = RestModel(fields, name=None)


endpoint = SingleModelValidator(
    'aws_cloudwatch_logs_tasks',
    model,
    config_name='aws_cloudwatch_logs'
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
