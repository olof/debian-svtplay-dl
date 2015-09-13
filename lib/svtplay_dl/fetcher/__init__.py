from __future__ import absolute_import
from svtplay_dl.utils import HTTP

class VideoRetriever(object):
    def __init__(self, options, url, bitrate=0, **kwargs):
        self.options = options
        self.url = url
        self.bitrate = int(bitrate)
        self.kwargs = kwargs
        self.http = HTTP()

    def name(self):
        pass
