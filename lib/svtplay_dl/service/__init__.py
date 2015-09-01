# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
from __future__ import absolute_import
import re
from svtplay_dl.utils.urllib import urlparse
from svtplay_dl.utils import download_thumbnail, get_http_data, is_py2

import logging

log = logging.getLogger('svtplay_dl')

class Service(object):
    supported_domains = []
    supported_domains_re = []

    def __init__(self, _url):
        self._url = _url
        self._urldata = None
        self._error = False

    @property
    def url(self):
        return self._url

    def get_urldata(self):
        if self._urldata is None:
            self._error, self._urldata = get_http_data(self.url)
        return self._error, self._urldata

    @classmethod
    def handles(cls, url):
        urlp = urlparse(url)

        # Apply supported_domains_re regexp to the netloc. This
        # is meant for 'dynamic' domains, e.g. containing country
        # information etc.
        for domain_re in [re.compile(x) for x in cls.supported_domains_re]:
            if domain_re.match(urlp.netloc):
                return True

        if urlp.netloc in cls.supported_domains:
            return True

        # For every listed domain, try with www. subdomain as well.
        if urlp.netloc in ['www.'+x for x in cls.supported_domains]:
            return True

        return False

    def get_subtitle(self, options):
        pass

    def exclude(self, options):
        if options.exclude:
            for i in options.exclude:
                if is_py2:
                    i = i.decode("utf-8")
                if i in options.output:
                    return True
        return False

    # the options parameter is unused, but is part of the
    # interface, so we don't want to remove it. Thus, the
    # pylint ignore.
    def find_all_episodes(self, options): # pylint: disable-msg=unused-argument
        log.warning("--all-episodes not implemented for this service")
        return [self.url]

def opengraph_get(html, prop):
    """
    Extract specified OpenGraph property from html.

        >>> opengraph_get('<html><head><meta property="og:image" content="http://example.com/img.jpg"><meta ...', "image")
        'http://example.com/img.jpg'
        >>> opengraph_get('<html><head><meta content="http://example.com/img2.jpg" property="og:image"><meta ...', "image")
        'http://example.com/img2.jpg'
        >>> opengraph_get('<html><head><meta name="og:image" property="og:image" content="http://example.com/img3.jpg"><meta ...', "image")
        'http://example.com/img3.jpg'
    """
    match = re.search('<meta [^>]*property="og:' + prop + '" content="([^"]*)"', html)
    if match is None:
        match = re.search('<meta [^>]*content="([^"]*)" property="og:' + prop + '"', html)
        if match is None:
            return None
    return match.group(1)


class OpenGraphThumbMixin(object):
    """
    Mix this into the service class to grab thumbnail from OpenGraph properties.
    """
    def get_thumbnail(self, options):
        url = opengraph_get(self.get_urldata()[1], "image")
        if url is None:
            return
        download_thumbnail(options, url)


class Generic(object):
    ''' Videos embed in sites '''
    def get(self, sites, url):
        error, data = get_http_data(url)
        if error:
            return url, None
        match = re.search(r"src=(\"|\')(http://www.svt.se/wd[^\'\"]+)(\"|\')", data)
        stream = None
        if match:
            url = match.group(2)
            for i in sites:
                if i.handles(url):
                    url = url.replace("&amp;", "&").replace("&#038;", "&")
                    return url, i(url)

        match = re.search(r"src=\"(http://player.vimeo.com/video/[0-9]+)\" ", data)
        if match:
            for i in sites:
                if i.handles(match.group(1)):
                    return match.group(1), i(url)
        match = re.search(r"tv4play.se/iframe/video/(\d+)?", data)
        if match:
            url = "http://www.tv4play.se/?video_id=%s" % match.group(1)
            for i in sites:
                if i.handles(url):
                    return url, i(url)
        match = re.search(r"embed.bambuser.com/broadcast/(\d+)", data)
        if match:
            url = "http://bambuser.com/v/%s" % match.group(1)
            for i in sites:
                if i.handles(url):
                    return url, i(url)
        match = re.search(r'src="(http://tv.aftonbladet[^"]*)"', data)
        if match:
            url = match.group(1)
            for i in sites:
                if i.handles(url):
                    return url, i(url)
        match = re.search(r'a href="(http://tv.aftonbladet[^"]*)" class="abVi', data)
        if match:
            url = match.group(1)
            for i in sites:
                if i.handles(url):
                    return url, i(url)

        match = re.search(r"iframe src='(http://www.svtplay[^']*)'", data)
        if match:
            url = match.group(1)
            for i in sites:
                if i.handles(url):
                    return url, i(url)

        return url, stream

def service_handler(sites, url):
    handler = None

    for i in sites:
        if i.handles(url):
            handler = i(url)
            break

    return handler
