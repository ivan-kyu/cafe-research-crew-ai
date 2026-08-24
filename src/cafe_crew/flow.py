from datetime import datetime, timezone

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from cafe_crew.config import Settings
from cafe_crew.crew import build_research_crew
from cafe_crew.models import (
    AgentReport,
    DiscoveryResult,
    ResearchReport,
    SourcePlace,
)
from cafe_crew.places import GooglePlacesClient
from cafe_crew.reporting import merge_place


REVIEW_NOTE = (
    "Review summaries use up to three of the five relevance-ranked reviews returned by Google. "
    "They are a useful signal, but are not guaranteed to be the newest or exhaustive."
)


class CafeResearchState(BaseModel):
    area: str = ""
    scanned_count: int = 0
    qualified_count: int = 0
    source_places: list[SourcePlace] = Field(default_factory=list)


class CafeResearchFlow(Flow[CafeResearchState]):
    @start()
    def discover_places(self) -> DiscoveryResult:
        settings = Settings.from_env()
        client = GooglePlacesClient(settings.google_places_api_key)
        try:
            result = client.discover(self.state.area)
        finally:
            client.close()
        self.state.scanned_count = result.scanned_count
        self.state.qualified_count = result.qualified_count
        self.state.source_places = result.places
        return result

    @listen(discover_places)
    def research_shortlist(self, discovery: DiscoveryResult) -> AgentReport:
        if not discovery.places:
            return AgentReport(
                area_summary="No places met both the rating and review-count thresholds.",
                area_style="unclear",
                places=[],
            )

        settings = Settings.from_env()
        crew = build_research_crew(settings.llm_model)
        result = crew.kickoff(
            inputs={
                "area": self.state.area,
                "places_json": discovery.model_dump_json(indent=2),
            }
        )

        if result.pydantic is None:
            return AgentReport.model_validate_json(result.raw)
        return AgentReport.model_validate(result.pydantic)

    @listen(research_shortlist)
    def assemble_report(self, agent_report: AgentReport) -> ResearchReport:
        insights = {item.place_id: item for item in agent_report.places}
        places = [merge_place(source, insights.get(source.place_id)) for source in self.state.source_places]

        return ResearchReport(
            area=self.state.area,
            area_summary=agent_report.area_summary,
            area_style=agent_report.area_style,
            scanned_count=self.state.scanned_count,
            qualified_count=self.state.qualified_count,
            shown_count=len(places),
            generated_at=datetime.now(timezone.utc),
            places=places,
            review_note=REVIEW_NOTE,
        )
