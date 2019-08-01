# -*- coding: utf-8 -*-
import os
from typing import Optional

from .constants import ENV_VARIABLE


class NoApiKey(Exception):
    pass


def get_apikey(key: Optional[str] = None) -> str:
    """ Return API key, probably loading it from an environment variable """
    if key is not None:
        return key
    try:
        return os.environ[ENV_VARIABLE]
    except KeyError:
        raise NoApiKey("API key not found. Please set {} "
                       "environment variable or pass".format(ENV_VARIABLE))
