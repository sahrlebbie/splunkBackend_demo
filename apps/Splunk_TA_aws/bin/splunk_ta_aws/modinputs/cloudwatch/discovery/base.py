from __future__ import absolute_import
from splunk_ta_aws.modinputs.cloudwatch.metric import Metric


class DiscoveringPolicyRegistry(object):
    def __init__(self):
        self._registry = dict()

    def set(self, policy, *keys):
        self._registry[keys] = policy
        return self

    def get(self, *keys):
        return self._registry.get(keys)


class DiscoveringPolicy(object):
    def __init__(self, ns):
        self._ns = ns

    def _create_metrics(self, dimensions, metric_names, tags=None):
        dimensions = [(key, value) for key, value in dimensions.items()]
        dimensions.sort(key=lambda _: _[0])
        return [Metric(self._ns, name, dimensions, tags) for name in metric_names]

    def __call__(self, client):
        pass
