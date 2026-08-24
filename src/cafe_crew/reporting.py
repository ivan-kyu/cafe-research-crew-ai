from cafe_crew.models import AgentPlaceBrief, PlaceBrief, SourcePlace


def merge_place(source: SourcePlace, insight: AgentPlaceBrief | None) -> PlaceBrief:
    """Attach agent interpretation while preserving all factual source fields."""
    return PlaceBrief(
        place_id=source.place_id,
        name=source.name,
        address=source.address,
        rating=source.rating,
        review_count=source.review_count,
        primary_type=source.primary_type,
        price_level=source.price_level,
        google_maps_url=source.google_maps_url,
        website_url=source.website_url,
        style=insight.style if insight else "unclear",
        why_it_stands_out=(
            insight.why_it_stands_out if insight else "Meets the rating and review-count thresholds."
        ),
        review_summary=insight.review_summary if insight else "No review summary was produced.",
        watch_out=insight.watch_out if insight else "",
        best_for=insight.best_for if insight else "Well-rated option",
    )

