
from __future__ import absolute_import

from functools import wraps
from splunk import admin
from solnlib.splunkenv import get_splunkd_uri
from solnlib.utils import is_true

from .eai import EAI_FIELDS
from .handler import RestHandler
import os
from .endpoint import (
    SingleModel,
    DataInputModel,
    MultipleModel
)
import six

try:
    from custom_hook_mixin import CustomHookMixin as HookMixin
except ImportError:
    from .base_hook_mixin import BaseHookMixin as HookMixin


__all__ = [
    'make_conf_item',
    'build_conf_info',
    'AdminExternalHandler',
]


def make_conf_item(conf_item, content, eai):
    for key, val in six.iteritems(content):
        conf_item[key] = val

    for eai_field in EAI_FIELDS:
        conf_item.setMetadata(eai_field, eai.content[eai_field])

    return conf_item


def build_conf_info(meth):
    """
    Build conf info for admin external REST endpoint.

    :param meth:
    :return:
    """
    @wraps(meth)
    def wrapper(self, confInfo):
        result = meth(self, confInfo)
        for entity in result:
            make_conf_item(
                confInfo[entity.name],
                entity.content,
                entity.eai,
            )

    return wrapper

def get_splunkd_endpoint():
    if os.environ.get('SPLUNKD_URI'):
        return os.environ['SPLUNKD_URI']
    else:
        splunkd_uri = get_splunkd_uri()
        os.environ['SPLUNKD_URI'] = splunkd_uri
        return splunkd_uri


class AdminExternalHandler(HookMixin, admin.MConfigHandler, object):

    # Leave it for setting REST model
    endpoint = None

    # action parameter for getting clear credentials
    ACTION_CRED = '--cred--'

    def __init__(self, *args, **kwargs):
        # use classic inheritance to be compatible for
        # old version of Splunk private SDK
        admin.MConfigHandler.__init__(
            self,
            *args,
            **kwargs
        )
        self.handler = RestHandler(
            get_splunkd_endpoint(),
            self.getSessionKey(),
            self.endpoint,
        )
        self.payload = self._convert_payload()

    def setup(self):
        # add args for getting clear credentials
        if self.requestedAction == admin.ACTION_LIST:
            self.supportedArgs.addOptArg(self.ACTION_CRED)

        # add args in payload while creating/updating
        actions = (admin.ACTION_LIST, admin.ACTION_REMOVE)
        if self.requestedAction in actions:
            return
        model = self.endpoint.model(self.callerArgs.id)
        if self.requestedAction == admin.ACTION_CREATE:
            for field in model.fields:
                if field.required:
                    self.supportedArgs.addReqArg(field.name)
                else:
                    self.supportedArgs.addOptArg(field.name)

        if self.requestedAction == admin.ACTION_EDIT:
            for field in model.fields:
                self.supportedArgs.addOptArg(field.name)

    @build_conf_info
    def handleList(self, confInfo):
        decrypt = self.callerArgs.data.get(
            self.ACTION_CRED,
            [False],
        )
        decrypt = is_true(decrypt[0])
        if self.callerArgs.id:
            result = self.handler.get(
                self.callerArgs.id,
                decrypt=decrypt,
            )
        else:
            result = self.handler.all(
                decrypt=decrypt,
                count=0,
            )
        return result

    @build_conf_info
    def handleCreate(self, confInfo):
        self.create_hook(
            session_key=self.getSessionKey(),
            config_name=self._get_name(),
            stanza_id=self.callerArgs.id,
            payload=self.payload
        )
        return self.handler.create(
            self.callerArgs.id,
            self.payload,
        )

    @build_conf_info
    def handleEdit(self, confInfo):
        disabled = self.payload.get('disabled')
        if disabled is None:
            self.edit_hook(
                session_key=self.getSessionKey(),
                config_name=self._get_name(),
                stanza_id=self.callerArgs.id,
                payload=self.payload
            )
            return self.handler.update(
                self.callerArgs.id,
                self.payload,
            )
        elif is_true(disabled):
            return self.handler.disable(self.callerArgs.id)
        else:
            return self.handler.enable(self.callerArgs.id)

    @build_conf_info
    def handleRemove(self, confInfo):
        self.delete_hook(
            session_key=self.getSessionKey(),
            config_name=self._get_name(),
            stanza_id=self.callerArgs.id
        )
        return self.handler.delete(self.callerArgs.id)

    def _get_name(self):
        name = None
        if isinstance(self.handler.get_endpoint(), DataInputModel):
            name = self.handler.get_endpoint().input_type
        elif isinstance(self.handler.get_endpoint(), SingleModel):
            name = self.handler.get_endpoint().config_name
        elif isinstance(self.handler.get_endpoint(), MultipleModel):
            # For multiple model, the configuraiton name is same with stanza id
            name = self.callerArgs.id
        return name

    def _convert_payload(self):
        check_actions = (admin.ACTION_CREATE, admin.ACTION_EDIT)
        if self.requestedAction not in check_actions:
            return None

        payload = {}
        for filed, value in six.iteritems(self.callerArgs.data):
            payload[filed] = value[0] if value and value[0] else ''
        return payload


def handle(
        endpoint,
        handler=AdminExternalHandler,
        context_info=admin.CONTEXT_APP_ONLY,
):
    """
    Handle request.

    :param endpoint: REST endpoint
    :param handler: REST handler
    :param context_info:
    :return:
    """
    real_handler = type(
        handler.__name__,
        (handler, ),
        {'endpoint': endpoint},
    )
    admin.init(real_handler, ctxInfo=context_info)
