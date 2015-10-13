# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
from __future__ import absolute_import
import re
import json
import copy

from svtplay_dl.service import Service, OpenGraphThumbMixin
from svtplay_dl.utils.urllib import urlparse
from svtplay_dl.fetcher.hds import hdsparse
from svtplay_dl.fetcher.hls import hlsparse
from svtplay_dl.subtitle import subtitle
from svtplay_dl.error import ServiceError


class Nrk(Service, OpenGraphThumbMixin):
    supported_domains = ['nrk.no', 'tv.nrk.no', 'p3.no']

    def get(self, options):
        data = self.get_urldata()

        if self.exclude(options):
            yield ServiceError("Excluding video")
            return

        match = re.search("data-subtitlesurl = \"(/.*)\"", data)

        if match:
            parse = urlparse(self.url)
            suburl = "%s://%s%s" % (parse.scheme, parse.netloc, match.group(1))
            yield subtitle(copy.copy(options), "tt", suburl)

        if options.force_subtitle:
            return

        match = re.search(r'data-media="(.*manifest.f4m)"', self.get_urldata())
        if match:
            manifest_url = match.group(1)
        else:
            match = re.search(r'data-nrk-id="([^"]+)"></div><script', self.get_urldata())
            if match is None:
                match = re.search(r'video-id="([^"]+)"', self.get_urldata())
                if match is None:
                    yield ServiceError("Can't find video id.")
                    return
            vid = match.group(1)
            dataurl = "http://v8.psapi.nrk.no/mediaelement/%s" % vid
            data = self.http.request("get", dataurl).text
            data = json.loads(data)
            manifest_url = data["mediaUrl"]
            options.live = data["isLive"]

        hlsurl = manifest_url.replace("/z/", "/i/").replace("manifest.f4m", "master.m3u8")
        data = self.http.request("get", hlsurl)
        if data.status_code == 403:
            yield ServiceError("Can't fetch the video because of geoblocked")
            return
        streams = hlsparse(options, data, hlsurl)
        for n in list(streams.keys()):
            yield streams[n]

        streams = hdsparse(copy.copy(options), self.http.request("get", manifest_url, params={"hdcore": "3.7.0"}), manifest_url)
        if streams:
            for n in list(streams.keys()):
                yield streams[n]
