# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-

# pylint has issues with urlparse: "some types could not be inferred"
# pylint: disable=E1103

from __future__ import absolute_import
import re
import json
import copy
import os

from svtplay_dl.utils.urllib import urlparse, quote_plus
from svtplay_dl.service import Service
from svtplay_dl.utils import filenamify
from svtplay_dl.log import log
from svtplay_dl.fetcher.hls import hlsparse
from svtplay_dl.error import ServiceError


class TwitchException(Exception):
    pass


class TwitchUrlException(TwitchException):
    """
    Used to indicate an invalid URL for a given media_type. E.g.:

      TwitchUrlException('video', 'http://twitch.tv/example')
    """
    def __init__(self, media_type, url):
        super(TwitchUrlException, self).__init__(
            "'%s' is not recognized as a %s URL" % (url, media_type)
        )


class Twitch(Service):
    # Twitch uses language subdomains, e.g. en.www.twitch.tv. They
    # are usually two characters, but may have a country suffix as well (e.g.
    # zh-tw, zh-cn and pt-br.
    supported_domains_re = [
        r'^(?:(?:[a-z]{2}-)?[a-z]{2}\.)?(www\.)?twitch\.tv$',
    ]

    api_base_url = 'https://api.twitch.tv'
    hls_base_url = 'http://usher.justin.tv/api/channel/hls'

    def get(self):
        urlp = urlparse(self.url)

        if self.exclude(self.options):
            yield ServiceError("Excluding video")
            return

        match = re.match(r'/(\w+)/([bcv])/(\d+)', urlp.path)
        if not match:
            data = self._get_channel(self.options, urlp)
        else:
            if match.group(2) in ["b", "c"]:
                yield ServiceError("This twitch video type is unsupported")
                return
            data = self._get_archive(self.options, match.group(3))
        try:
            for i in data:
                yield i
        except TwitchUrlException as e:
            yield ServiceError("This twitch video type is unsupported")
            return

    def _get_static_video(self, options, videoid):
        access = self._get_access_token(videoid)

        if options.output_auto:
            data = self.http.request("get", "https://api.twitch.tv/kraken/videos/v%s" % videoid)
            if data.status_code == 404:
                yield ServiceError("Can't find the video")
                return
            info = json.loads(data.text)
            name = "twitch-%s-%s" % (info["channel"]["name"], filenamify(info["title"]))
            directory = os.path.dirname(options.output)
            if os.path.isdir(directory):
                name = os.path.join(directory, name)
            options.output = name

        if "token" not in access:
            raise TwitchUrlException('video', self.url)
        nauth = quote_plus(str(access["token"]))
        authsig = access["sig"]

        url = "http://usher.twitch.tv/vod/%s?nauth=%s&nauthsig=%s" % (
            videoid, nauth, authsig)

        streams = hlsparse(options, self.http.request("get", url), url)
        if streams:
            for n in list(streams.keys()):
                yield streams[n]

    def _get_archive(self, options, vid):
        try:
            for n in self._get_static_video(options, vid):
                yield n
        except TwitchUrlException as e:
            log.error(str(e))

    def _get_access_token(self, channel, vtype="vods"):
        """
        Get a Twitch access token. It's a three element dict:

         * mobile_restricted
         * sig
         * token

        `sig` is a hexadecimal string, and `token` is a JSON blob, with
        information about access expiration. `mobile_restricted` is not
        important, but is a boolean.

        Both `sig` and `token` should be added to the HLS URI, and the
        token should, of course, be URI encoded.
        """
        return self._ajax_get('/api/%s/%s/access_token' % (vtype, channel))

    def _ajax_get(self, method):
        url = "%s/%s" % (self.api_base_url, method)

        # Logic found in Twitch's global.js. Prepend /kraken/ to url
        # path unless the API method already is absolute.
        if method[0] != '/':
            method = '/kraken/%s' % method

        # There are references to a api_token in global.js; it's used
        # with the "Twitch-Api-Token" HTTP header. But it doesn't seem
        # to be necessary.
        payload = self.http.request("get", url, headers={
            'Accept': 'application/vnd.twitchtv.v2+json'
        })
        return json.loads(payload.text)

    def _get_hls_url(self, channel):
        access = self._get_access_token(channel, "channels")

        query = "token=%s&sig=%s" % (quote_plus(access['token']), access['sig'])
        return "%s/%s.m3u8?%s" % (self.hls_base_url, channel, query)

    def _get_channel(self, options, urlp):
        match = re.match(r'/(\w+)', urlp.path)

        if not match:
            raise TwitchUrlException('channel', urlp.geturl())

        channel = match.group(1)
        if options.output_auto:
            options.output = "twitch-%s" % channel

        hls_url = self._get_hls_url(channel)
        urlp = urlparse(hls_url)

        options.live = True
        if not options.output:
            options.output = channel
        data = self.http.request("get", hls_url)
        if data.status_code == 404:
            yield ServiceError("Stream is not online.")
            return
        streams = hlsparse(options, data, hls_url)
        for n in list(streams.keys()):
            yield streams[n]
