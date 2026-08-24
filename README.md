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

## Deploy to Vercel

The project is configured for Vercel's native FastAPI runtime. `app.py` is the deployment entrypoint and `vercel.json` allows a research request to run for up to the Hobby-plan maximum of five minutes. The function runs in Singapore (`sin1`), which is a sensible default for use from Bali and can be changed in `vercel.json`.

### From the Vercel dashboard

1. Push this folder to a GitHub repository.
2. In Vercel, choose **Add New → Project** and import that repository.
3. Keep the detected FastAPI settings and add these environment variables for Production, Preview, and Development as appropriate:
   - `OPENAI_API_KEY`
   - `GOOGLE_PLACES_API_KEY`
   - `APP_ACCESS_KEY` (strongly recommended)
   - `LLM_MODEL=openai/gpt-4.1-mini`
   - `CREWAI_TRACING_ENABLED=false`
4. Deploy, then open the generated HTTPS URL. On iPhone, use **Add to Home Screen** for an app-like icon.

### From the CLI

After installing and signing in to the Vercel CLI, run:

```bash
vercel
vercel env add OPENAI_API_KEY
vercel env add GOOGLE_PLACES_API_KEY
vercel env add APP_ACCESS_KEY
vercel env add LLM_MODEL
vercel env add CREWAI_TRACING_ENABLED
vercel --prod
```

The access key is optional locally but strongly recommended online because every research request uses paid APIs. Enter it under **Private access key** in the web form.

### Can it run for free?

Vercel's Hobby plan can host this personal project for free within its included usage and five-minute function limit. The application is stateless, so it fits Vercel's serverless model. The external services are separate: OpenAI model calls and the Google Places fields used here can incur charges, and Google requires billing to be enabled. Free Vercel hosting therefore does not make each research report free.

CrewAI is a relatively large dependency and cold starts will be slower than the `/health` endpoint. Vercel's standard Python function limit is 500 MB; new projects are eligible for Large Functions (currently beta), which allow larger bundles. If a build reports that the standard limit was exceeded, add `VERCEL_SUPPORT_LARGE_FUNCTIONS=1` in Vercel and redeploy. If a full research run regularly exceeds five minutes, a long-running job host is a better fit.

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
