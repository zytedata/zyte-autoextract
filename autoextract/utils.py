# -*- coding: utf-8 -*-
from .__version__ import __version__


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def user_agent(name):
    return 'AutoExtract {} v{}'.format(name, __version__)
