from .base import DiscoveringPolicy


class DiscoverGenericMetrics(DiscoveringPolicy):
    def __init__(self, ns):
        super(DiscoverGenericMetrics, self).__init__(ns)

    def __call__(self, client):
        for item in client.get_cloudwatch_metrics(self._ns):
            dimensions = {dim['Name']: dim['Value'] for dim in item['Dimensions']}
            metric_names = [item['MetricName']]
            yield self._create_metrics(dimensions, metric_names)
