from __future__ import absolute_import
import json
import types
import copy
import datetime
import time
from dateutil.tz import tzutc

import splunk_ta_aws.common.ta_aws_consts as tac
from splunk_ta_aws.common.ta_aws_common import load_credentials_from_cache

import splunksdc.log as logging
from botocore.exceptions import ClientError
from botocore.credentials import Credentials
import six
from six.moves import range

_MIN_TTL=datetime.timedelta(minutes=5)

logger = logging.get_module_logger()


_BUILT_IN_TYPES = (
    type(None),
    bool,
    int,
    int,
    float,
    bytes,
    str,
    list,
    dict,
)

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

OP_WHITELIST = ['describe_', 'get_', 'list_']
OP_BLACKLIST = []
REQUEST_LIMIT_ERROR_CODE = 'RequestLimitExceeded'
UNHANDLED_ERROR_CODE = ['InvalidAction', 'MethodNotAllowed']


class _ExtendedEncoder(json.JSONEncoder):
    def default(self, obj):
        # check datetime
        if isinstance(obj, datetime.datetime):
            # ISO 8601 time format
            if obj.utcoffset() is None or obj.utcoffset().total_seconds() == 0:
                return obj.strftime(DATETIME_FORMAT)[:-3] + 'Z'
            else:
                return obj.strftime(DATETIME_FORMAT)[:-3] + obj.strftime('%z')

        if not isinstance(obj, _BUILT_IN_TYPES):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


class BotoRetryWrapper(object):
    def __init__(self, boto_client = None, retries = 5):
        self.boto_client = boto_client
        self.retries = retries

    def __getattr__(self, item):
        need_retry = False

        for op in OP_WHITELIST:
            if item.startswith(op):
                need_retry = True
                break

        for op in OP_BLACKLIST:
            if item.startswith(op):
                need_retry = False
                break

        if not need_retry:
            return getattr(self.boto_client, item)

        def wrapper_func(*args, **kwargs):
            max_tries = max(self.retries, 0) + 1
            last_ex = None

            for i in range(max_tries):
                try:
                    return getattr(self.boto_client, item)(*args, **kwargs)

                except Exception as e:
                    error_code = None
                    if isinstance(e, ClientError):
                        if 'Code' in e.response['Error']:
                            error_code = e.response['Error']['Code']

                    if error_code == REQUEST_LIMIT_ERROR_CODE:
                        last_ex = e
                        if i < max_tries - 1:
                            time.sleep(2 ** i)
                        logger.warn('Retry description function (%s).' % item)
                        continue
                    elif error_code and (error_code.startswith('NoSuch') or error_code in UNHANDLED_ERROR_CODE):
                        # these exceptions need not error logs
                        raise
                    else:
                        logger.exception('Run description function (%s) failed.' % item)
                        raise

            if last_ex:
                logger.exception('Run description function (%s) failed after retries.' % item)
                raise last_ex

        return wrapper_func


def decorate(func):
    '''Decorator to add common metadata for each item.'''
    def wrapper(config, *args, **kwargs):
        for item in func(config, *args, **kwargs):
            item['AccountId'] = config[tac.account_id]
            #ADDON-15532: Remove region from IAM users
            if func.__name__ != 'iam_users':
                item['Region'] = item.get('Region', config[tac.region])
            yield serialize(item)

    return wrapper


def serialize(value):
    return json.dumps(value, cls=_ExtendedEncoder)


def generate_credentials(func):
    """
    Decorator for refreshing credentials.

    :param func:
    :return:
    """

    def wrapper(config, *args, **kwargs):
        load_credentials(config)
        return func(config, *args, **kwargs)

    return wrapper

def load_credentials(config):
        credentials = load_credentials_from_cache(
            config[tac.server_uri],
            config[tac.session_key],
            config[tac.aws_account],
            config.get(tac.aws_iam_role),
            config.get(tac.region)
        )
        config[tac.key_id] = credentials.aws_access_key_id
        config[tac.secret_key] = credentials.aws_secret_access_key
        config['aws_session_token'] = credentials.aws_session_token
        config[tac.account_id] = credentials.account_id
        config['token_expiration'] = credentials.expiration

def refresh_credentials(config,credential_threshold,client):
    if need_retire(config['token_expiration'],credential_threshold):
        logger.info("Refresh credentials of S3 connection.")
        load_credentials(config)
        # Change credentails dynamically inside boto3 client
        client._request_signer._credentials = Credentials(
            config[tac.key_id],
            config[tac.secret_key],
            config['aws_session_token']
        )
    
def need_retire(expiration,threshold=_MIN_TTL):
    if not expiration:
        return False
    now = datetime.datetime.utcnow().replace(tzinfo=tzutc())
    delta = expiration - now
    return delta < threshold
