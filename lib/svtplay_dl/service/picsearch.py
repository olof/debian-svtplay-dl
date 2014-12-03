# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
from __future__ import absolute_import
import re
import json
import copy

from svtplay_dl.service import Service, OpenGraphThumbMixin
from svtplay_dl.utils import get_http_data, HTTPError
from svtplay_dl.fetcher.rtmp import RTMP
from svtplay_dl.log import log

class Picsearch(Service, OpenGraphThumbMixin):
    supported_domains = ['dn.se', 'mobil.dn.se']

    def get(self, options):
        try:
            ajax_auth = re.search(r"picsearch_ajax_auth = '(\w+)'", self.get_urldata())
        except HTTPError:
            log.error("Can't get the page.")
            return
        if not ajax_auth:
            log.error("Cant find token for video")
            return
        mediaid = re.search(r"mediaId = '([^']+)';", self.get_urldata())
        if not mediaid:
            mediaid = re.search(r'media-id="([^"]+)"', self.get_urldata())
            if not mediaid:
                log.error("Cant find media id")
                return
        jsondata = get_http_data("http://csp.picsearch.com/rest?jsonp=&eventParam=1&auth=%s&method=embed&mediaid=%s" % (ajax_auth.group(1), mediaid.group(1)))
        jsondata = json.loads(jsondata)
        playlist = jsondata["media"]["playerconfig"]["playlist"][1]
        if "bitrates" in playlist:
            files = playlist["bitrates"]
            server = jsondata["media"]["playerconfig"]["plugins"]["bwcheck"]["netConnectionUrl"]

            for i in files:
                options.other = "-y '%s'" % i["url"]
                yield RTMP(copy.copy(options), server, i["height"])
        if "provider" in playlist:
            options.live = playlist["live"]
            if playlist["url"].endswith(".f4m"):
                    streams = hdsparse(copy.copy(options), playlist["url"])
                    if streams:
                        for n in list(streams.keys()):
                            yield streams[n]
