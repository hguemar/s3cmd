class RemoteObject(object):
    def __init__(self):
        self._size = None
        self.timestamp = None
        self._md5 = None
        self.object_key = None
        self.object_uri_str = None
        self.base_uri = None
        self.local_filename = None

    def md5(self):
        return self._md5

    def size(self):
        return self._size
