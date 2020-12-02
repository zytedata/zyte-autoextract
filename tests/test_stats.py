import time

from autoextract.stats import AggStats, ResponseStats


def test_agg_stats():
    stats = AggStats()
    stats.time_connect_stats.push(4)
    rs = ResponseStats.create(time.perf_counter())
    rs.record_read(stats)
    rs.record_connected(stats)
    assert isinstance(stats.summary(), str)
    assert isinstance(str(stats), str)
