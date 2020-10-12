import os
import sys

from setuptools import find_packages

if "build_exe" in sys.argv:
    from cx_Freeze import setup, Executable
else:
    from setuptools import setup

    # fake Executable class to avoid cx_Freeze on non-Windows
    # noinspection Mypy
    class Executable:
        # noinspection PyUnusedLocal
        def __init__(self, script=None, base=None):
            pass


import versioneer

srcdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib/")
sys.path.insert(0, srcdir)

vi = sys.version_info
if vi < (3, 5):
    raise RuntimeError("svtplay-dl requires Python 3.5 or greater")

about = {}
with open(os.path.join(srcdir, "svtplay_dl", "__version__.py")) as f:
    exec(f.read(), about)

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

deps = []
deps.append("requests>=2.0.0")
deps.append("PySocks")
deps.append("cryptography")
deps.append("pyyaml")

setup(
    name="svtplay-dl",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages("lib", exclude=["tests", "*.tests", "*.tests.*"]),
    install_requires=deps,
    package_dir={"": "lib"},
    scripts=["bin/svtplay-dl"],
    author="Johan Andersson",
    author_email="j@i19.se",
    description="Command-line program to download videos from various video on demand sites",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://svtplay-dl.se",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    # cx_freeze info for Windows builds with Python embedded
    options={"build_exe": {"packages": ["cffi", "cryptography", "idna", "queue"], "includes": "_cffi_backend"}},
    executables=[Executable("bin/svtplay-dl", base=None)],
)
