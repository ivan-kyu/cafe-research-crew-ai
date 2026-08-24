import os
import re
import secrets
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from cafe_crew.models import ResearchReport, ResearchRequest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = PROJECT_ROOT / "web"
PHOTO_NAME_PATTERN = re.compile(r"^places/[^/]+/photos/[^/]+$")

app = FastAPI(title="Cafe Research Crew", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research", response_model=ResearchReport)
async def research(
    request: ResearchRequest,
    x_app_key: str | None = Header(default=None),
) -> ResearchReport:
    require_access_key(x_app_key)
    area = " ".join(request.area.split())

    try:
        result = await run_in_threadpool(lambda: run_research_flow(area))
        return ResearchReport.model_validate(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The research crew could not finish this report. Check the server logs.",
        ) from exc


@app.get("/api/place-photo", response_class=Response)
async def place_photo(
    name: str = Query(min_length=10, max_length=2048),
    x_app_key: str | None = Header(default=None),
) -> Response:
    """Fetch a bounded Google Places image without exposing the Google API key."""
    require_access_key(x_app_key)
    if not PHOTO_NAME_PATTERN.fullmatch(name):
        raise HTTPException(status_code=400, detail="Invalid Google Place photo name.")

    google_api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_PLACES_API_KEY is not configured.")

    try:
        content, content_type = await fetch_google_photo(name, google_api_key)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail="Google could not return this place photo.") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Google Place Photos is temporarily unavailable.") from exc

    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "private, no-store"},
    )


async def fetch_google_photo(name: str, api_key: str) -> tuple[bytes, str]:
    url = f"https://places.googleapis.com/v1/{name}/media"
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={"X-Goog-Api-Key": api_key},
            params={"maxWidthPx": 1200, "maxHeightPx": 900},
        )
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/jpeg")


def require_access_key(provided_key: str | None) -> None:
    expected_key = os.getenv("APP_ACCESS_KEY", "").strip()
    if expected_key and not secrets.compare_digest(provided_key or "", expected_key):
        raise HTTPException(status_code=401, detail="A valid private access key is required.")


def run_research_flow(area: str):
    # CrewAI is intentionally imported on first research request so health checks
    # and the landing page stay fast on small hosted runtimes.
    from cafe_crew.flow import CafeResearchFlow

    return CafeResearchFlow().kickoff(inputs={"area": area})


def run() -> None:
    uvicorn.run(
        "cafe_crew.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
