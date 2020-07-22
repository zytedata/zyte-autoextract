# -*- coding: utf-8 -*-
import sys


collect_ignore = ["setup.py"]

# ignore async API tests if aiohttp is not available
try:
    from aiohttp import ClientTimeout  # we need recent aiohttp
except ImportError:
    collect_ignore.append("autoextract/aio/")
    collect_ignore.append("autoextract/__main__.py")

if sys.version_info < (3, 6):
    # Async support depends on Python 3.6+
    collect_ignore.append('tests/test_aio/')
