from __future__ import absolute_import
import itertools
from .base import DiscoveringPolicyRegistry, DiscoveringPolicy


class DiscoverS3Metrics(DiscoveringPolicy):
    _STORAGE_METRIC_NAMES = [
        'BucketSizeBytes',
        'NumberOfObjects',
    ]

    _STORAGE_TYPES = [
        'StandardStorage',
        'StandardIAStorage',
        'OneZoneIAStorage',
        'ReducedRedundancyStorage',
        'GlacierStorage',
        'AllStorageTypes',
    ]

    def __call__(self, client):
        bucket_names = client.get_s3_buckets()
        pairs = itertools.product(bucket_names, self._STORAGE_TYPES)
        for bn, st in pairs:
            dimension = {'BucketName': bn, 'StorageType': st}
            yield self._create_metrics(dimension, self._STORAGE_METRIC_NAMES)


def create_policy_registry():
    registry = DiscoveringPolicyRegistry()
    registry.set(DiscoverS3Metrics, 'BucketName', 'StorageType')
    return registry
