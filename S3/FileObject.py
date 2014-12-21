import os
import Utils

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
        if self._md5 is None:
            self._md5 = Utils.calculateChecksum(filename = self.filename, stream = self.stream)
        return self._md5


    def sr(self):
        """
        return (cached) result of os.stat_result()
        """
        if self._sr is None:
            self._sr = os.stat_result(os.stat(self.filename))
        return self._sr

    def size(self):
        return self.sr().st_size
