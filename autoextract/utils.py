# -*- coding: utf-8 -*-
from .__version__ import __version__


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def user_agent(library):
    return 'zyte-autoextract/{} {}/{}'.format(
        __version__,
        library.__name__,
        library.__version__)
