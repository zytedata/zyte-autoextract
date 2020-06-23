# -*- coding: utf-8 -*-
import pytest
import os
import sys

from autoextract.apikey import ENV_VARIABLE


collect_ignore = []
if sys.version_info < (3, 6):
    # Async support depends on Python 3.6+
    collect_ignore.append('test_aio/')


@pytest.fixture()
def autoextract_env_variable():
    _FAKE_KEY = 'APIKEY'
    old_env = os.environ.copy()
    os.environ[ENV_VARIABLE] = _FAKE_KEY
    try:
        yield _FAKE_KEY
    finally:
        os.environ = old_env
