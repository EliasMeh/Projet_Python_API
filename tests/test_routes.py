from fastapi.testclient import TestClient

from api.main import app, _store


client = TestClient(app)


def setup_function():
    _store.clear()


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_route():
    response = client.get("/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert {"cpu_percent", "memory_percent", "disk_percent"}.issubset(payload)


def test_post_server_requires_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    response = client.post(
        "/servers",
        json={"name": "api-1", "host": "httpbin.org", "port": 443},
    )
    assert response.status_code == 403


def test_create_and_list_servers(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    headers = {"X-API-Key": "secret"}

    create_response = client.post(
        "/servers",
        json={"name": "api-1", "host": "httpbin.org", "port": 443, "tags": ["prod"]},
        headers=headers,
    )
    assert create_response.status_code == 201

    list_response = client.get("/servers")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_get_missing_server_returns_404():
    response = client.get("/servers/999")
    assert response.status_code == 404


def test_websocket_metrics_stream():
    with client.websocket_connect("/ws/metrics") as websocket:
        message = websocket.receive_json()
        assert {"cpu_percent", "memory_percent", "disk_percent"}.issubset(message)
