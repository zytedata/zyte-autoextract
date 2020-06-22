# -*- coding: utf-8 -*-
from autoextract.utils import chunks


def test_chunks():
    assert list(chunks([1, 2, 3], 1)) == [[1], [2], [3]]
    assert list(chunks([1, 2, 3], 2)) == [[1, 2], [3]]
