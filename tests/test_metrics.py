import time

from app.metrics import RequestMetrics


def test_records_p95_and_logs():
    metrics = RequestMetrics()
    durations = [0.01 * i for i in range(1, 21)]
    for duration in durations:
        metrics.record(duration)

    assert 0.19 <= metrics.p95() <= 0.2

    start_count = len(metrics.durations)
    with metrics.time_request():
        time.sleep(0.005)
    assert len(metrics.durations) == start_count + 1
