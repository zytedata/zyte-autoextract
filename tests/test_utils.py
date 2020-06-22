# -*- coding: utf-8 -*-
import pytest

from autoextract.utils import chunks, extract_retry_seconds


def test_chunks():
    assert list(chunks([1, 2, 3], 1)) == [[1], [2], [3]]
    assert list(chunks([1, 2, 3], 2)) == [[1, 2], [3]]


@pytest.mark.parametrize("msg, seconds", (
    ("Domain blablabla is occupied, please retry in 23.5 seconds ", 23.5),
    ("Domain blablabla is occupied, please retry in sfbe seconds ", None),
    ("Domain blablabla is occupied, please retry in 5 seconds ", 5.0),
    ("domain blablabla is occupied, please retry in 5 seconds ", 5.0),
    ("hi", None),
))
def test_extract_retry_secconds(msg, seconds):
    assert extract_retry_seconds(msg) == seconds
