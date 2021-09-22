from __future__ import absolute_import
import os
import os.path as op
import six
import xml.sax.saxutils as xss


def is_true(val):
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def escape_cdata(data):
    data = xss.escape(data)
    return data


def get_app_path(absolute_path):
    marker = os.path.join(os.path.sep, 'etc', 'apps')
    start = absolute_path.rfind(marker)
    if start == -1:
        start = 0
    end = absolute_path.find('bin', start)
    if end == -1:
        return None
    # strip the tail
    end = end - 1
    path = absolute_path[:end]
    return path


class FileMonitor(object):

    def __init__(self, callback, files):
        """
        :files: files to be monidtored with full path
        """

        self._callback = callback
        self._files = files

        self.file_mtimes = {
            file_name: None for file_name in self._files
        }
        for k in self.file_mtimes:
            try:
                self.file_mtimes[k] = op.getmtime(k)
            except OSError:
                pass

    def __call__(self):
        return self.check_changes()

    def check_changes(self):
        file_mtimes = self.file_mtimes
        changed_files = []
        for f, last_mtime in six.iteritems(file_mtimes):
            try:
                current_mtime = op.getmtime(f)
                if current_mtime != last_mtime:
                    file_mtimes[f] = current_mtime
                    changed_files.append(f)
            except OSError:
                pass

        if changed_files:
            if self._callback:
                self._callback(changed_files)
            return True
        return False
