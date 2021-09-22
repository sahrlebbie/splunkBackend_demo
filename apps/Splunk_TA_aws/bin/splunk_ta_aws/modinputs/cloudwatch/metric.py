from __future__ import absolute_import
import re
import time
import json
import zlib
import base64
import threading
from six.moves import range

import hashlib
from boto3.session import Session
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from splunksdc import log as logging
from splunksdc.utils import LogExceptions, LogWith
from splunksdc.checkpoint import Partition
from six.moves import zip


logger = logging.get_module_logger()


class Metric(object):
    def __init__(self, namespace, name, dimensions, tags=None):
        self._namespace = namespace
        self._name = name
        self._dimensions = dimensions
        self._tags = tags
        self._key = self._make_state_key(namespace, name, dimensions)

    def match(self, filtering):
        if not filtering.match_name(self._name):
            return False
        if not filtering.match_dimensions(self._dimensions):
            return False
        return True

    def write(self, points, writer):
        logger.debug('Start writing data points.', key=self._key, count=len(points))
        return writer(points, self._namespace, self._name, self._dimensions, self._tags)

    def get(self, checkpoint):
        return checkpoint.get(self._key, [])

    def set(self, checkpoint, markers, expiration):
        return checkpoint.set(self._key, markers, expiration)

    def flatten(self, namespace, name, dimensions, tags):
        namespace.append(self._namespace)
        name.append(self._name)
        dimensions.append(self._dimensions)
        tags.append(self._tags)

    def query(self, client, statistics, period, start_time, end_time):
        params = {
            'Namespace': self._namespace,
            'MetricName': self._name,
            'Dimensions': [{'Name': key, 'Value': value} for key, value in self._dimensions],
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': period,
            'Statistics': statistics
        }
        response = client.get_metric_statistics(**params)
        points = [MetricPoint(_, period) for _ in response.get('Datapoints', [])]
        points.sort(key=lambda _: _.timestamp)
        logger.debug('GetMetricStatistics success.', key=self._key, count=len(points))
        return points

    @classmethod
    def _make_state_key(cls, namespace, name, dimensions):
        dimensions = json.dumps(dimensions, sort_keys=True)
        seed = ''.join([namespace, name, dimensions])
        sha = hashlib.sha224()
        sha.update(seed.encode('utf-8'))
        key = base64.b64encode(sha.digest())
        return key.decode('utf-8')

    @classmethod
    def archive(cls, metrics):
        namespace = list()
        name = list()
        dimensions = list()
        tags = list()

        for metric in metrics:
            metric.flatten(namespace, name, dimensions, tags)

        return [namespace, name, dimensions, tags]

    @classmethod
    def restore(cls, quadruples):
        return [Metric(*args) for args in zip(*quadruples)]


class MetricCheckpoint(object):
    def __init__(self, checkpoint):
        self._checkpoint = checkpoint
        self._states = Partition(checkpoint, '/states/')
        self._cache = Partition(checkpoint, '/cache/')
        self._now = time.time

    def set(self, key, data, expiration):
        expiration = self._now() + expiration
        payload = [data, expiration]
        return self._states.set(key, payload)

    def get(self, key, default):
        item = self._states.find(key)
        return item.value[0] if item else default

    def sweep(self):
        marker = self._now()
        expired = list()
        for key, value in self._states.items():
            _, expiration = value
            if expiration < marker:
                expired.append(key)
        for key in expired:
            self._states.delete(key)
        self._checkpoint.sweep()

    def archive(self, data, expiration):
        data = json.dumps(data)
        data = data.encode('utf-8')
        data = zlib.compress(data, 9)
        expiration = self._now() + expiration
        self._cache.set('metrics', data)
        self._cache.set('expiration', expiration)
        logger.debug('Update metrics cache.', size=len(data), expiration=expiration)
        return data

    def restore(self):
        item = self._cache.find('metrics')
        if not item:
            return []
        data = item.value
        data = zlib.decompress(data)
        data = json.loads(data)
        logger.debug('Load metrics from cache.')
        return data

    def need_refresh(self):
        item = self._cache.find('expiration')
        if not item:
            return True
        return item.value < self._now()


class MetricFilter(object):
    def __init__(self, names, dimensions):
        self._names = self._create_pattern_for_names(names)
        self._dimensions = self._create_pattern_for_dimensions(dimensions)

    def get_dimension_keys(self):
        keys = list(self._dimensions.keys())
        keys.sort()
        return tuple(keys)

    def match_dimensions(self, dimensions):
        if len(dimensions) != len(self._dimensions):
            return False

        return all([
            self._match_one_dimension(key, value)
            for key, value in dimensions
        ])

    def _match_one_dimension(self, key, value):
        if key not in self._dimensions:
            return False
        pattern = self._dimensions[key]
        return pattern.match(value)

    def match_name(self, name):
        return self._names.match(name)

    @classmethod
    def _create_pattern_for_names(cls, regex):
        if isinstance(regex, list):
            regex = '|'.join(regex)
        return re.compile(regex)

    @classmethod
    def _create_pattern_for_dimensions(cls, rules):
        dims = dict()
        for key, regex in rules.items():
            if isinstance(regex, list):
                regex = '|'.join(regex)
            dims[key] = re.compile(regex)
        return dims


class MetricPoint(object):
    _EPOCH = datetime(1970, 1, 1, tzinfo=tzutc())

    def __init__(self, point, period):
        moment = point['Timestamp']
        self._timestamp = self._datetime_to_timestamp(moment)
        self._value = {k: v for k, v in point.items() if k != 'Timestamp'}
        self._period = period

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def iso1806(self):
        moment = datetime.utcfromtimestamp(self._timestamp)
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def value(self):
        return self._value

    @property
    def period(self):
        return self._period

    @classmethod
    def _datetime_to_timestamp(cls, dt):
        elapse = dt - cls._EPOCH
        return elapse.total_seconds()


class MetricQueryResult(object):
    def __init__(self):
        self._metrics = list()
        self._points = list()

    def append(self, metric, points):
        self._metrics.append(metric)
        self._points.append(points)

    def __iter__(self):
        return zip(self._metrics, self._points)


class MetricQuery(object):
    def __init__(self, metrics, statistics, period, start_time, end_time):
        self._metrics = metrics
        self._statistics = statistics
        self._period = period
        self._start_time = start_time
        self._end_time = end_time

    def run(self, client):
        result = MetricQueryResult()
        for metric in self._metrics:
            points = metric.query(
                client,
                self._statistics, self._period,
                self._start_time, self._end_time
            )
            result.append(metric, points)
        return result


class MetricQueryBuilder(object):
    def __init__(self, statistics, period, query_window_size):
        self._statistics = statistics
        self._period = period
        self._query_window_size = query_window_size
        self._query_batch_size = 64
        self._now = time.time

    def _make_time_range(self):
        elapse = self._now() // self._period * self._period
        end_time = datetime.utcfromtimestamp(elapse)
        seconds = self._query_window_size * self._period
        start_time = end_time - timedelta(seconds=seconds)
        return start_time, end_time

    def create_batches(self, metrics):
        start_time, end_time = self._make_time_range()
        queries = list()
        args = self._statistics, self._period,  start_time, end_time
        logger.debug('Create metric query.', period=self._period, start_time=str(start_time), end_time=str(end_time))
        for metrics in self._chunk(metrics, self._query_batch_size):
            query = MetricQuery(metrics, *args)
            queries.append(query)
        for queries in self._chunk(queries, self._query_batch_size):
            yield queries

    @classmethod
    def _chunk(cls, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))


class MetricQueryExecutor(object):

    _tlb = threading.local()

    def __init__(self, region, credentials, io, endpoint_url=None):
        self._credentials = credentials
        self._region = region
        self._endpoint_url = endpoint_url
        self._io = io
        self._top_ctx = logging.ThreadLocalLoggingStack.top()

    def run(self, batches):
        for result in self._io.map(self._run, batches):
            if isinstance(result, Exception):
                logger.warning('Querying metric data points failed.')
                continue
            for metric, points in result:
                yield metric, points

    def _create_client(self, session):
        return self._credentials.client('cloudwatch', self._region, session, self._endpoint_url)

    @property
    def top_ctx(self):
        return self._top_ctx

    @LogWith(prefix=top_ctx)
    @LogExceptions(logger, 'An error occurred during querying metric data points.', lambda e: e)
    def _run(self, batch):
        session = self._acquire_session()
        client = self._create_client(session)
        return batch.run(client)

    @classmethod
    def _acquire_session(cls):
        if not hasattr(cls._tlb, 'session'):
            cls._tlb.session = Session()
        return cls._tlb.session
