from fastapi.testclient import TestClient

from cafe_crew.api import app


client = TestClient(app)


def test_vercel_entrypoint_exports_the_application() -> None:
    from app import app as vercel_app

    assert vercel_app is app


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


def test_photo_proxy_rejects_invalid_resource_name(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "google-test-key")

    response = client.get("/api/place-photo", params={"name": "https://example.com/image.jpg"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Google Place photo name."


def test_photo_proxy_returns_google_image(monkeypatch) -> None:
    from cafe_crew import api

    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "google-test-key")

    async def fake_fetch(name: str, api_key: str) -> tuple[bytes, str]:
        assert name == "places/abc/photos/photo-1"
        assert api_key == "google-test-key"
        return b"image bytes", "image/webp"

    monkeypatch.setattr(api, "fetch_google_photo", fake_fetch)
    response = client.get(
        "/api/place-photo",
        params={"name": "places/abc/photos/photo-1"},
    )

    assert response.status_code == 200
    assert response.content == b"image bytes"
    assert response.headers["content-type"] == "image/webp"
    assert response.headers["cache-control"] == "private, no-store"
