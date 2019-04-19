# -*- coding: utf-8 -*-
import pytest

from xod.apikey import get_apikey, NoApiKey


def test_get_apikey(xod_env_variable):
    assert get_apikey('foo') == 'foo'
    assert get_apikey() == xod_env_variable


def test_get_apikey_missing():
    with pytest.raises(NoApiKey):
        get_apikey()
