#!/usr/bin/env python
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
from setuptools import setup, find_packages
import sys
import os

srcdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib/")
sys.path.insert(0, srcdir)
import svtplay_dl

setup(
    name = "svtplay-dl",
    version = svtplay_dl.__version__,
    packages = find_packages(
        'lib',
        exclude=["tests", "*.tests", "*.tests.*"]),
    install_requires=["requests>=2.0.0"],
    package_dir = {'': 'lib'},
    scripts = ['bin/svtplay-dl'],

    author = "Johan Andersson",
    author_email = "j@i19.se",
    description = "Command-line program to download videos from various video on demand sites",
    license = "MIT",
    url = "https://github.com/spaam/svtplay-dl",
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Environment :: Console",
                 "Operating System :: POSIX",
                 "Operating System :: Microsoft :: Windows",
                 "Programming Language :: Python :: 2.6",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3.3",
                 "Programming Language :: Python :: 3.4",
                 "Programming Language :: Python :: 3.5",
                 "Topic :: Internet :: WWW/HTTP",
                 "Topic :: Multimedia :: Sound/Audio",
                 "Topic :: Multimedia :: Video",
                 "Topic :: Utilities"]
)
