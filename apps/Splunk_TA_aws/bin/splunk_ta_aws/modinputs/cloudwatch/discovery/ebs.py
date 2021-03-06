from .base import DiscoveringPolicyRegistry, DiscoveringPolicy


class DiscoverEBSMetrics(DiscoveringPolicy):
    _METRIC_NAMES = [
        'VolumeReadBytes',
        'VolumeWriteBytes',
        'VolumeReadOps',
        'VolumeWriteOps',
        'VolumeTotalReadTime',
        'VolumeTotalWriteTime',
        'VolumeIdleTime',
        'VolumeQueueLength',
        'VolumeThroughputPercentage',
        'VolumeConsumedReadWriteOps',
        'BurstBalance'
    ]

    _EXT_DIMS = [
        'State',
        'AvailabilityZone',
        'VolumeType',
    ]

    def __call__(self, client):
        for volume in client.get_ebs_volumes():
            dimension = {'VolumeId': volume['VolumeId']}
            tags = self._extract_extra_dimensions(volume)
            yield self._create_metrics(dimension, self._METRIC_NAMES, tags)

    @classmethod
    def _extract_extra_dimensions(cls, volume):
        extra = [{item['Key']: item['Value']} for item in volume.get('Tags', [])]
        dims = {key: volume.get(key) for key in cls._EXT_DIMS}
        extra.extend([{key: value} for key, value in dims.items() if value])
        return extra


def create_policy_registry():
    registry = DiscoveringPolicyRegistry()
    registry.set(DiscoverEBSMetrics, 'VolumeId')
    return registry
