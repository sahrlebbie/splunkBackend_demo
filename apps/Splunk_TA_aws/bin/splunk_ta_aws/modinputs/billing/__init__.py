from __future__ import absolute_import
from splunksdc import environ
import os


# Notice that this function is copied and modified from incremental_s3
def delete_ckpt(name):
    root = environ.get_checkpoint_folder('aws_billing_cur')
    path = os.path.join(root, name)

    # try remove files for billing cur
    path += '.ckpt'
    if os.path.isfile(path):
        os.remove(path)
