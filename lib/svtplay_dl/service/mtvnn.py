from __future__ import absolute_import
import re
import os
import xml.etree.ElementTree as ET

from svtplay_dl.service import Service, OpenGraphThumbMixin
from svtplay_dl.utils import is_py2_old
from svtplay_dl.error import ServiceError
from svtplay_dl.log import log
from svtplay_dl.fetcher.rtmp import RTMP


# This is _very_ similar to mtvservices..
class Mtvnn(Service, OpenGraphThumbMixin):
    supported_domains = ['nickelodeon.se', "nickelodeon.nl", "nickelodeon.no"]

    def get(self, options):
        data = self.get_urldata()
        match = re.search(r'"(http://api.mtvnn.com/v2/mrss.xml[^"]+)"', data)
        if not match:
            yield ServiceError("Can't find id for the video")
            return

        data = self.http.request("get", match.group(1)).content
        xml = ET.XML(data)
        mediagen = xml.find("channel").find("item").find("{http://search.yahoo.com/mrss/}group")
        title = xml.find("channel").find("item").find("title").text
        if options.output_auto:
            directory = os.path.dirname(options.output)
            if len(directory):
                options.output = os.path.join(directory, title)
            else:
                options.output = title

        if self.exclude(options):
            yield ServiceError("Excluding video")
            return

        swfurl = mediagen.find("{http://search.yahoo.com/mrss/}player").attrib["url"]
        options.other = "-W %s" % self.http.check_redirect(swfurl)

        contenturl = mediagen.find("{http://search.yahoo.com/mrss/}content").attrib["url"]
        content = self.http.request("get", contenturl).content
        xml = ET.XML(content)
        ss = xml.find("video").find("item")
        if is_py2_old:
            sa = list(ss.getiterator("rendition"))
        else:
            sa = list(ss.iter("rendition"))

        for i in sa:
            yield RTMP(options, i.find("src").text, i.attrib["bitrate"])

    def find_all_episodes(self, options):
        match = re.search(r"data-franchise='([^']+)'", self.get_urldata())
        if match is None:
            log.error("Couldn't program id")
            return
        programid = match.group(1)
        match = re.findall(r"<li class='(divider playlist-item|playlist-item)'( data-item-id='([^']+)')?", self.get_urldata())
        if not match:
            log.error("Couldn't retrieve episode list")
            return
        episodNr = []
        for i in match:
            if i[0] == "playlist-item":
                episodNr.append(i[2])
            else:
                break

        episodes = []
        n = 0
        for i in sorted(episodNr):
            if n == options.all_last:
                break
            episodes.append("http://www.nickelodeon.se/serier/%s-something/videos/%s-something" % (programid, i))
            n += 1
        return episodes
