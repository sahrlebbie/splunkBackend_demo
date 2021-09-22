from __future__ import absolute_import
import base64
import time

import splunksdc.log as logging
import splunk_ta_aws.common.ta_aws_consts as tac
from splunk_ta_aws.common import ta_aws_common
from . import aws_kinesis_consts as akc
import splunktalib.state_store as ss
import six


logger = logging.get_module_logger()


def get_ckpt_key(config):
    return ta_aws_common.b64encode_text("{}|{}|{}".format(
        config[akc.stream_name], config[akc.shard_id], config[tac.name]))


class AWSKinesisCheckpointer(object):

    def __init__(self, config):
        self._config = config
        self._state_store = ss.get_state_store(
            config, config[tac.app_name], collection_name="aws_kinesis",
            use_kv_store=config.get(tac.use_kv_store))
        self._key = get_ckpt_key(config)

    def sequence_number(self):
        state = self._state_store.get_state(self._key)
        if state:
            return state[akc.sequence_number]

    def set_sequence_number(self, seq_num):
        state = {
            akc.sequence_number: seq_num,
            "timestamp": time.time(),
            "version": 1,
        }
        self._state_store.update_state(self._key, state)


def clean_up_ckpt_for_deleted_data_input(tasks):
    if not tasks:
        return

    now_ckpts = {}
    for task in tasks:
        if task[tac.datainput] not in now_ckpts:
            now_ckpts[task[tac.datainput]] = []
        now_ckpts[task[tac.datainput]].append(get_ckpt_key(task))

    store = ss.get_state_store(
        tasks[0], tasks[0][tac.app_name], collection_name="aws_kinesis",
        use_kv_store=tasks[0][tac.use_kv_store])
    previous_ckpts = store.get_state("data_input_ckpts")
    if previous_ckpts:
        for datainput, ckpt_keys in six.iteritems(previous_ckpts):
            if datainput not in now_ckpts:
                logger.info(
                    "Detect datainput=%s has been deleted, remove its ckpts",
                    datainput)
                for key in ckpt_keys:
                    store.delete_state(key)

    store.update_state("data_input_ckpts", now_ckpts)
