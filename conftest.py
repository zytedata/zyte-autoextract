# -*- coding: utf-8 -*-
collect_ignore = ["setup.py"]

# ignore async API tests if aiohttp is not available
try:
    from aiohttp import ClientTimeout  # we need recent aiohttp
except ImportError:
    collect_ignore.append("autoextract/aio.py")