from __future__ import absolute_import
import botocore.endpoint
from requests.utils import should_bypass_proxies

HTTP_PROXY = None
HTTPS_PROXY = None


def _get_proxies(self, url):
    if should_bypass_proxies(url, None):
        return {}
    return {"http": HTTP_PROXY, "https": HTTPS_PROXY}

botocore.endpoint.EndpointCreator._get_proxies = _get_proxies


def set_proxies(http_proxy, https_proxy):
    global HTTP_PROXY
    global HTTPS_PROXY

    HTTP_PROXY = http_proxy
    HTTPS_PROXY = https_proxy
