import os
import secrets
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cafe_crew.models import ResearchReport, ResearchRequest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = PROJECT_ROOT / "web"

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


def require_access_key(provided_key: str | None) -> None:
    expected_key = os.getenv("APP_ACCESS_KEY", "").strip()
    if expected_key and not secrets.compare_digest(provided_key or "", expected_key):
        raise HTTPException(status_code=401, detail="A valid private access key is required.")


def run_research_flow(area: str):
    # CrewAI is intentionally imported on first research request so health checks
    # and the landing page stay fast on small container hosts.
    from cafe_crew.flow import CafeResearchFlow

    return CafeResearchFlow().kickoff(inputs={"area": area})


def run() -> None:
    uvicorn.run(
        "cafe_crew.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
