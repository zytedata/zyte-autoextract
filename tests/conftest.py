# -*- coding: utf-8 -*-
import pytest
import os

from autoextract.apikey import ENV_VARIABLE


def fake_env(key):
    old_env = os.environ.copy()
    os.environ[ENV_VARIABLE] = key
    try:
        yield key
    finally:
        os.environ = old_env


@pytest.fixture()
def autoextract_env_variable():
    yield from fake_env('APIKEY')


@pytest.fixture()
def autoextract_blank_env_variable():
    yield from fake_env('')
