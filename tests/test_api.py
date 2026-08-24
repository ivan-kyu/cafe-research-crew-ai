from fastapi.testclient import TestClient

from cafe_crew.api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mobile_frontend_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert '<meta name="viewport" content="width=device-width, initial-scale=1"' in response.text
    assert "Only 4.5+ places with at least 30 ratings" in response.text


def test_optional_access_key_blocks_unknown_clients(monkeypatch) -> None:
    monkeypatch.setenv("APP_ACCESS_KEY", "private-test-key")

    response = client.post("/api/research", json={"area": "Ubud, Bali"})

    assert response.status_code == 401
    assert response.json()["detail"] == "A valid private access key is required."
