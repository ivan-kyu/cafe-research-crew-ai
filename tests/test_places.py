import httpx

from cafe_crew.places import GooglePlacesClient


def place(place_id: str, rating: float, review_count: int, status: str = "OPERATIONAL") -> dict:
    return {
        "id": place_id,
        "displayName": {"text": f"Place {place_id}"},
        "formattedAddress": "1 Test Street",
        "rating": rating,
        "userRatingCount": review_count,
        "businessStatus": status,
        "googleMapsUri": f"https://maps.google.com/?place={place_id}",
        "reviews": [
            {
                "rating": 5,
                "publishTime": "2026-07-01T10:00:00Z",
                "text": {"text": "Excellent coffee and kind staff."},
            }
        ],
    }


def test_discover_filters_deduplicates_and_sorts() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        payload = {
            "places": [
                place("best", 4.8, 100),
                place("duplicate", 4.7, 600),
                place("few-reviews", 4.9, 29),
                place("low-rating", 4.4, 900),
                place("closed", 5.0, 100, "CLOSED_PERMANENTLY"),
            ]
        }
        if calls == 2:
            payload["places"].append(place("duplicate", 4.7, 600))
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = GooglePlacesClient("test-key", client).discover("Test Area")

    assert calls == 2
    assert result.scanned_count == 5
    assert result.qualified_count == 2
    assert [item.place_id for item in result.places] == ["best", "duplicate"]
    assert result.places[0].reviews[0].text == "Excellent coffee and kind staff."


def test_google_error_is_readable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "API key rejected"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    try:
        GooglePlacesClient("bad-key", client).discover("Test Area")
    except RuntimeError as exc:
        assert str(exc) == "Google Places request failed: API key rejected"
    else:
        raise AssertionError("Expected RuntimeError")
