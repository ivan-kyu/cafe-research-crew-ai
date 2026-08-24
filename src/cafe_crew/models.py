from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PlaceStyle = Literal["local", "western", "mixed/international", "unclear"]


class ReviewSnippet(BaseModel):
    rating: float | None = None
    published_at: str = ""
    relative_time: str = ""
    text: str = ""


class PhotoAttribution(BaseModel):
    display_name: str = ""
    uri: str = ""


class PlacePhoto(BaseModel):
    name: str
    width_px: int = 0
    height_px: int = 0
    author_attributions: list[PhotoAttribution] = Field(default_factory=list)
    google_maps_url: str = ""


class SourcePlace(BaseModel):
    place_id: str
    name: str
    address: str
    rating: float
    review_count: int
    primary_type: str = ""
    price_level: str = ""
    google_maps_url: str
    website_url: str = ""
    reviews: list[ReviewSnippet] = Field(default_factory=list)
    photos: list[PlacePhoto] = Field(default_factory=list)


class DiscoveryResult(BaseModel):
    scanned_count: int = 0
    qualified_count: int = 0
    places: list[SourcePlace] = Field(default_factory=list)


class PlaceClassification(BaseModel):
    place_id: str
    style: PlaceStyle
    evidence: str = Field(description="A short explanation grounded in the supplied data.")


class ScoutingResult(BaseModel):
    classifications: list[PlaceClassification]


class ReviewInsight(BaseModel):
    place_id: str
    review_summary: str
    watch_out: str = ""
    best_for: str


class ReviewAnalysis(BaseModel):
    insights: list[ReviewInsight]


class AgentPlaceBrief(BaseModel):
    place_id: str
    style: PlaceStyle
    why_it_stands_out: str
    review_summary: str
    watch_out: str = ""
    best_for: str


class AgentReport(BaseModel):
    area_summary: str
    area_style: PlaceStyle
    places: list[AgentPlaceBrief]


class PlaceBrief(BaseModel):
    place_id: str
    name: str
    address: str
    rating: float
    review_count: int
    primary_type: str
    price_level: str
    google_maps_url: str
    website_url: str
    style: PlaceStyle
    why_it_stands_out: str
    review_summary: str
    watch_out: str
    best_for: str
    photos: list[PlacePhoto] = Field(default_factory=list)


class ResearchReport(BaseModel):
    area: str
    area_summary: str
    area_style: PlaceStyle
    scanned_count: int
    qualified_count: int
    shown_count: int
    generated_at: datetime
    places: list[PlaceBrief]
    review_note: str


class ResearchRequest(BaseModel):
    area: str = Field(min_length=2, max_length=120)
