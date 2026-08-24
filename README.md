# Cafe Research Crew

A small CrewAI Flow that turns an area name into a concise, phone-friendly cafe and restaurant shortlist.

## How it works

```text
Area name
   ↓
Google Places discovery (facts + hard filters)
   ↓
Local Map Scout (local / Western / mixed classification)
   ↓
Review Signal Analyst (praise, caveats, best-for)
   ↓
On-the-Road Briefing Editor (concise report)
```

The rating rules are enforced in regular Python, not left to an LLM:

- rating must be at least **4.5**
- rating count must be at least **30**
- permanently closed places are removed
- factual ratings, counts, addresses, and links are copied from Google data after the agents finish

“Local” and “Western” describe the apparent food/cafe style, not ownership. Google returns at most five reviews per place, ranked by relevance; this app uses the three most recently published reviews within that returned sample.

## Roles

The agents and their tasks live together in `src/cafe_crew/crew.py`. That is the main file to edit when you want to change roles, prompts, or hand-offs. The event-driven steps live in `src/cafe_crew/flow.py`.

## Run locally

1. Create Google Cloud and OpenAI API keys. Enable **Places API (New)** and billing for the Google project.
2. Copy the environment template and fill in the two API keys (plus an optional local access key):

   ```bash
   cp .env.example .env
   ```

3. Install and run:

   ```bash
   python3 -m venv .venv.nosync
   source .venv.nosync/bin/activate
   pip install -e ".[dev]"
   python dev.py
   ```

   The `.nosync` suffix keeps the generated environment local when this project is inside an iCloud-synced Documents folder. `dev.py` adds `src` to Python's import path and watches only `src` and `web`, so the reloader does not watch or restart on virtual-environment changes.

   If the first start is unusually slow, use Finder's **Keep Downloaded** action on the project folder or move the repository outside an iCloud-synced Documents directory.

   The equivalent direct Uvicorn command is:

   ```bash
   python -m uvicorn cafe_crew.api:app \
     --app-dir src \
     --reload \
     --reload-dir src \
     --reload-dir web
   ```

4. Open [http://localhost:8000](http://localhost:8000).

## Put it online for your iPhone

The included `Dockerfile` works on common container hosts. `render.yaml` also provides a Render Blueprint:

1. Push this folder to a GitHub repository.
2. In Render, create a Blueprint from that repository.
3. Add `OPENAI_API_KEY`, `GOOGLE_PLACES_API_KEY`, and a private `APP_ACCESS_KEY` when prompted.
4. Open the resulting HTTPS URL in Safari and use **Add to Home Screen** if you want an app-like icon.

For any other container host, deploy the Dockerfile and add the same secrets. The access key is optional locally but strongly recommended online because every research request uses paid APIs. Enter it under **Private access key** in the web form. The server reads its port from `PORT` and exposes `/health` for health checks.

## API

```bash
curl -X POST http://localhost:8000/api/research \
  -H 'Content-Type: application/json' \
  -H 'X-App-Key: your-private-access-key' \
  -d '{"area":"Ubud, Bali"}'
```

The API returns structured JSON, so a native iPhone app or another frontend can be added later without changing the crew.

## Cost and data notes

- Each report makes two Google Text Search requests and three LLM calls when qualifying places exist.
- Requesting ratings and reviews uses paid Google Places data fields. Set billing alerts in Google Cloud.
- Review summaries are an AI interpretation of a small, relevance-ranked sample. Always use the Google Maps link for the latest details before travelling.
