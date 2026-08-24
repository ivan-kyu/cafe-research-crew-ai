from datetime import datetime, timezone

import httpx

from cafe_crew.models import (
    DiscoveryResult,
    PhotoAttribution,
    PlacePhoto,
    ReviewSnippet,
    SourcePlace,
)


PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.userRatingCount",
        "places.primaryTypeDisplayName",
        "places.priceLevel",
        "places.googleMapsUri",
        "places.websiteUri",
        "places.businessStatus",
        "places.reviews",
        "places.photos",
    ]
)


class GooglePlacesClient:
    def __init__(
        self,
        api_key: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.http_client = http_client or httpx.Client(timeout=25.0)

    def close(self) -> None:
        self.http_client.close()

    def discover(self, area: str, limit: int = 8) -> DiscoveryResult:
        raw_places: dict[str, dict] = {}

        for query in self._queries(area):
            for place in self._search(query):
                place_id = place.get("id")
                if place_id:
                    raw_places[place_id] = place

        qualified = [
            self._to_source_place(place)
            for place in raw_places.values()
            if self._is_qualified(place)
        ]
        qualified.sort(key=lambda place: (place.rating, place.review_count), reverse=True)

        return DiscoveryResult(
            scanned_count=len(raw_places),
            qualified_count=len(qualified),
            places=qualified[:limit],
        )

    @staticmethod
    def _queries(area: str) -> tuple[str, str]:
        return (
            f"cafes and coffee shops in {area}",
            f"restaurants in {area}",
        )

    def _search(self, text_query: str) -> list[dict]:
        response = self.http_client.post(
            PLACES_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            json={
                "textQuery": text_query,
                "pageSize": 20,
                "minRating": 4.5,
                "rankPreference": "RELEVANCE",
            },
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._error_message(response)
            raise RuntimeError(f"Google Places request failed: {detail}") from exc

        return response.json().get("places", [])

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            return response.json().get("error", {}).get("message", response.text)
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    @staticmethod
    def _is_qualified(place: dict) -> bool:
        return (
            place.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"
            and float(place.get("rating", 0)) >= 4.5
            and int(place.get("userRatingCount", 0)) >= 30
        )

    @classmethod
    def _to_source_place(cls, place: dict) -> SourcePlace:
        reviews = [cls._to_review(review) for review in place.get("reviews", [])]
        reviews.sort(key=lambda review: cls._review_date(review.published_at), reverse=True)

        return SourcePlace(
            place_id=place["id"],
            name=place.get("displayName", {}).get("text", "Unnamed place"),
            address=place.get("formattedAddress", ""),
            rating=float(place.get("rating", 0)),
            review_count=int(place.get("userRatingCount", 0)),
            primary_type=place.get("primaryTypeDisplayName", {}).get("text", ""),
            price_level=place.get("priceLevel", ""),
            google_maps_url=place.get(
                "googleMapsUri",
                f"https://www.google.com/maps/search/?api=1&query_place_id={place['id']}",
            ),
            website_url=place.get("websiteUri", ""),
            reviews=reviews[:3],
            photos=[cls._to_photo(photo) for photo in place.get("photos", [])],
        )

    @staticmethod
    def _to_photo(photo: dict) -> PlacePhoto:
        return PlacePhoto(
            name=photo["name"],
            width_px=int(photo.get("widthPx", 0)),
            height_px=int(photo.get("heightPx", 0)),
            author_attributions=[
                PhotoAttribution(
                    display_name=author.get("displayName", ""),
                    uri=author.get("uri", ""),
                )
                for author in photo.get("authorAttributions", [])
            ],
            google_maps_url=photo.get("googleMapsUri", ""),
        )

    @staticmethod
    def _to_review(review: dict) -> ReviewSnippet:
        text = review.get("text", {}).get("text", "")
        if not text:
            text = review.get("originalText", {}).get("text", "")

        return ReviewSnippet(
            rating=review.get("rating"),
            published_at=review.get("publishTime", ""),
            relative_time=review.get("relativePublishTimeDescription", ""),
            text=text[:1200],
        )

    @staticmethod
    def _review_date(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
