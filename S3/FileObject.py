import os
import sys
from logging import debug
import Utils
import Config

cfg = Config.Config()

class FileObject(object):
    def __init__(self, filename):
        self.filename = filename
        self.relative_file = None
        self._sr = None
        self.stream = None
        self._sha256 = None
        self._md5 = None

    def full_name_unicode(self):
        return Utils.unicodise(self.filename)

    def md5(self):
        if 'md5' not in cfg.sync_checks:
            return None
        if self._md5 is None:
            self._md5, self._sha256 = Utils.calculateChecksum(filename = self.filename, stream = self.stream)
        return self._md5

    def sha256(self):
        if self._sha256 is None:
            self._md5, self._sha256 = Utils.calculateChecksum(filename = self.filename, stream = self.stream)
        debug(u'returning sha256 of %s = %s' % (self.filename, self._sha256))
        return self._sha256

    def sr(self):
        """
        return (cached) result of os.stat_result()
        """
        if self._sr is None:
            self._sr = os.stat_result(os.stat(self.filename))
        return self._sr

    def size(self):
        if self.stream == sys.stdin:
            return 0
        return self.sr().st_size
