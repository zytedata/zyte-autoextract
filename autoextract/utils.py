# -*- coding: utf-8 -*-
import re
from typing import Optional

from .__version__ import __version__


_DOMAIN_OCCUPIED_RE = re.compile(
    r".*domain .* is occupied, please retry in (.*) seconds.*",
    re.IGNORECASE
)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def user_agent(library):
    return 'scrapinghub-autoextract/{} {}/{}'.format(
        __version__,
        library.__name__,
        library.__version__)


def extract_retry_seconds(msg: msg) -> Optional[float]:
    """Extract retry seconds from domain occupied message."""
    match = _DOMAIN_OCCUPIED_RE.match(msg or "")
    if not match:
        return

    try:
        return float(match.group(1))
    except ValueError:
        pass
