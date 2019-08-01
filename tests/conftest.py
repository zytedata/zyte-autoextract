# -*- coding: utf-8 -*-
import pytest
import os

from autoextract.apikey import ENV_VARIABLE


@pytest.fixture()
def autoextract_env_variable():
    _FAKE_KEY = 'APIKEY'
    old_env = os.environ.copy()
    os.environ[ENV_VARIABLE] = _FAKE_KEY
    try:
        yield _FAKE_KEY
    finally:
        os.environ = old_env
