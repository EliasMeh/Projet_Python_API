from api.metrics import get_system_metrics


def test_metrics_contains_expected_fields(monkeypatch):
    monkeypatch.setattr("api.metrics.psutil.cpu_percent", lambda interval=None: 42.0)

    class Memory:
        percent = 50.0

    class Disk:
        percent = 60.0

    monkeypatch.setattr("api.metrics.psutil.virtual_memory", lambda: Memory())
    monkeypatch.setattr("api.metrics.psutil.disk_usage", lambda path: Disk())

    metrics = get_system_metrics()

    assert set(metrics) == {"cpu_percent", "memory_percent", "disk_percent"}
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert 0 <= metrics["disk_percent"] <= 100
