from __future__ import absolute_import
import boto3
import datetime
import time
import splunksdc.log as logging
from . import description as desc
import splunk_ta_aws.common.ta_aws_consts as tac
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.get_module_logger()

skipped_error_code_list = ['NoSuchLifecycleConfiguration',
                           'NoSuchCORSConfiguration', 'NoSuchTagSet',
                           'UnsupportedArgument', 'MethodNotAllowed']

CREDENTIAL_THRESHOLD=datetime.timedelta(minutes=20)

class S3ConnectionPool(object):
    """
    S3 connection pool for different regions.
    """
    _region_conn_pool = {}

    @classmethod
    def get_conn(cls, config, region):
        """Return s3 connection to region where bucket is located."""
        if region not in cls._region_conn_pool:
            cls._region_conn_pool[region] =  desc.BotoRetryWrapper(boto3.client(
                's3',
                aws_access_key_id=config[tac.key_id],
                aws_secret_access_key=config[tac.secret_key],
                aws_session_token=config.get('aws_session_token'),
                region_name=region,
                config=Config(signature_version='s3v4'),
                endpoint_url="https://{}.{}.amazonaws.com/".format('s3',region)
            ))
        else:
            desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,cls._region_conn_pool[region])

        return cls._region_conn_pool[region]

@desc.generate_credentials
@desc.decorate
def s3_buckets(config):
    s3_client = S3ConnectionPool.get_conn(config, region = config.get(tac.region))
    bucket_arr = s3_client.list_buckets()['Buckets']
    s3_bucket_client = None

    if bucket_arr is not None and len(bucket_arr) > 0:
        for bucket in bucket_arr:

            try:
                bucket_region = None
                response = s3_client.get_bucket_location(Bucket=bucket['Name'])
                response.pop('ResponseMetadata', None)

                # http://docs.aws.amazon.com/AmazonS3/latest/API/RESTBucketGETlocation.html#RESTBucketGETlocation-responses-response-elements
                # if location is us-east-1, it will return None
                if response.get('LocationConstraint') is None:
                    response['LocationConstraint'] = 'us-east-1'

                bucket_region = response.get('LocationConstraint')
                bucket.update(response)

                s3_bucket_client = S3ConnectionPool.get_conn(config, region=bucket_region)
            except Exception:
                logger.exception('An error occurred when getting bucket location for %s bucket.' % (bucket['Name']))
                s3_bucket_client = s3_client
            # add other info
            for operation in ['get_bucket_accelerate_configuration',
                              'get_bucket_cors', 'get_bucket_lifecycle',
                              'get_bucket_logging',
                              'get_bucket_tagging']:
                try:
                    response = getattr(s3_bucket_client, operation)(Bucket = bucket['Name'])
                    response.pop('ResponseMetadata', None)

                    bucket.update(response)

                except ClientError as client_error:
                    if 'Code' not in client_error.response['Error'] or client_error.response['Error']['Code'] not in skipped_error_code_list:
                        logger.exception('%s operation is invalid in %s bucket.' % (operation, bucket['Name']))
                    continue

                except Exception:
                    logger.exception('An error occurred when attempting %s operation on %s bucket.' % (operation, bucket['Name']))
                    continue

            bucket['Region'] = bucket.get('LocationConstraint')

            yield bucket
            desc.refresh_credentials(config,CREDENTIAL_THRESHOLD,s3_client)
