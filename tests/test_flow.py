from cafe_crew.models import AgentPlaceBrief, PlacePhoto, SourcePlace
from cafe_crew.reporting import merge_place


def test_merge_preserves_factual_source_fields() -> None:
    source = SourcePlace(
        place_id="abc",
        name="Grounded Cafe",
        address="Real address",
        rating=4.8,
        review_count=432,
        primary_type="Cafe",
        google_maps_url="https://maps.example/abc",
        photos=[PlacePhoto(name="places/abc/photos/photo-1")],
    )
    insight = AgentPlaceBrief(
        place_id="abc",
        style="local",
        why_it_stands_out="Strong coffee signal.",
        review_summary="People praise the coffee.",
        best_for="Morning coffee",
    )

    merged = merge_place(source, insight)

    assert merged.rating == 4.8
    assert merged.review_count == 432
    assert merged.style == "local"
    assert merged.google_maps_url == "https://maps.example/abc"
    assert merged.photos[0].name == "places/abc/photos/photo-1"
