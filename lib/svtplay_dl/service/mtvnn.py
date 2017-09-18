from __future__ import absolute_import
import re
import os
import json
import xml.etree.ElementTree as ET

from svtplay_dl.service import Service, OpenGraphThumbMixin
from svtplay_dl.utils import is_py2_old
from svtplay_dl.error import ServiceError
from svtplay_dl.log import log
from svtplay_dl.fetcher.rtmp import RTMP
from svtplay_dl.fetcher.hls import hlsparse


# This is _very_ similar to mtvservices..
class Mtvnn(Service, OpenGraphThumbMixin):
    supported_domains = ['nickelodeon.se', "nickelodeon.nl", "nickelodeon.no", "www.comedycentral.se", "nickelodeon.dk"]

    def get(self):
        data = self.get_urldata()
        match = re.search(r'data-mrss=[\'"](http://gakusei-cluster.mtvnn.com/v2/mrss.xml[^\'"]+)[\'"]', data)
        if not match:
            yield ServiceError("Can't find id for the video")
            return

        mrssxmlurl = match.group(1)
        data = self.http.request("get", mrssxmlurl).content
        xml = ET.XML(data)
        mediagen = xml.find("channel").find("item").find("{http://search.yahoo.com/mrss/}group")
        title = xml.find("channel").find("item").find("title").text
        if self.options.output_auto:
            directory = os.path.dirname(self.options.output)
            if len(directory):
                self.options.output = os.path.join(directory, title)
            else:
                self.options.output = title

        if self.exclude():
            yield ServiceError("Excluding video")
            return

        swfurl = mediagen.find("{http://search.yahoo.com/mrss/}player").attrib["url"]
        self.options.other = "-W %s" % self.http.check_redirect(swfurl)

        contenturl = mediagen.find("{http://search.yahoo.com/mrss/}content").attrib["url"]
        content = self.http.request("get", contenturl).content
        xml = ET.XML(content)
        ss = xml.find("video").find("item")
        if is_py2_old:
            sa = list(ss.getiterator("rendition"))
        else:
            sa = list(ss.iter("rendition"))

        for i in sa:
            yield RTMP(self.options, i.find("src").text, i.attrib["bitrate"])

        match = re.search("gon.viacom_config=([^;]+);", self.get_urldata())
        if match:
            countrycode = json.loads(match.group(1))["country_code"].replace("_", "/")

            match = re.search("mtvnn.com:([^&]+)", mrssxmlurl)
            if match:
                urlpart = match.group(1).replace("-", "/").replace("playlist", "playlists") # it use playlists dunno from where it gets it
                hlsapi = "http://api.mtvnn.com/v2/{0}/{1}.json?video_format=m3u8&callback=&".format(countrycode, urlpart)
                data = self.http.request("get", hlsapi).text

                dataj = json.loads(data)
                for i in dataj["local_playlist_videos"]:
                    streams = hlsparse(self.options, self.http.request("get", i["url"]), i["url"])
                    if streams:
                        for n in list(streams.keys()):
                            yield streams[n]

    def find_all_episodes(self, options):
        match = re.search(r"data-franchise='([^']+)'", self.get_urldata())
        if match is None:
            log.error("Couldn't program id")
            return
        programid = match.group(1)
        match = re.findall(r"<li class='([a-z]+ )?playlist-item( [a-z]+)*?'( data-[-a-z]+='[^']+')* data-item-id='([^']+)'", self.get_urldata())
        if not match:
            log.error("Couldn't retrieve episode list")
            return
        episodNr = []
        for i in match:
            episodNr.append(i[3])
        episodes = []
        n = 0
        for i in sorted(episodNr):
            if n == options.all_last:
                break
            episodes.append("http://www.nickelodeon.se/serier/%s-something/videos/%s-something" % (programid, i))
            n += 1
        return episodes
