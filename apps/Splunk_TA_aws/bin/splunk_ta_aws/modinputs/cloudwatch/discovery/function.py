from .base import DiscoveringPolicyRegistry, DiscoveringPolicy


class DiscoverLambdaMetrics(DiscoveringPolicy):
    _METRIC_NAMES = [
        'Invocations',
        'Errors',
        'Dead Letter Error',
        'Duration',
        'Throttles',
        'IteratorAge',
        'ConcurrentExecutions',
        'UnreservedConcurrentExecutions',
    ]

    def __call__(self, client):
        functions = client.get_lambda_functions()
        for item in functions:
            dimension = {'FunctionName': item['FunctionName']}
            yield self._create_metrics(dimension, self._METRIC_NAMES)


def create_policy_registry():
    registry = DiscoveringPolicyRegistry()
    registry.set(DiscoverLambdaMetrics, 'FunctionName')
    return registry

