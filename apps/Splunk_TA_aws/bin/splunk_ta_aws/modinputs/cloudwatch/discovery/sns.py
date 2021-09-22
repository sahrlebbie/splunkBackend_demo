from .base import DiscoveringPolicyRegistry, DiscoveringPolicy


class DiscoverSNSMetrics(DiscoveringPolicy):
    _METRIC_NAMES = [
        'NumberOfMessagesPublished',
        'NumberOfNotificationsDelivered',
        'NumberOfNotificationsFailed',
        'NumberOfNotificationsFilteredOut',
        'NumberOfNotificationsFilteredOut-NoMessageAttributes',
        'NumberOfNotificationsFilteredOut-InvalidAttributes',
        'PublishSize',
        'SMSMonthToDateSpentUSD',
        'SMSSuccessRate'
    ]

    def __call__(self, client):
        topic_names = self._get_topics(client)
        for tn in topic_names:
            dimension = {'TopicName': tn}
            yield self._create_metrics(dimension, self._METRIC_NAMES)

    @classmethod
    def _get_topics(cls, client):
        names = list()
        topics = client.get_sns_topics()
        for topic in topics:
            arn = topic['TopicArn']
            names.append(arn.split(':')[5])
        return names


def create_policy_registry():
    registry = DiscoveringPolicyRegistry()
    registry.set(DiscoverSNSMetrics, 'TopicName')
    return registry
