# ScrollMates

ScrollMates is a split-stack app with a React + Tailwind frontend in [`frontend/`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/frontend) and a FastAPI backend in [`backend/`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/backend).

## Prerequisites

- Node.js 24+
- Python 3.11+
- `ffprobe` on your `PATH` is recommended but no longer required for common browser uploads
- A Gemini API key

## Frontend setup

```bash
npm install --prefix frontend
```

Start the frontend:

```bash
npm run dev:frontend
```

## Backend setup

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Copy [`backend/.env.example`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/backend/.env.example) to `backend/.env` or export the variables in your shell:

```bash
export GEMINI_API_KEY=your_gemini_api_key
export GEMINI_MODEL=gemini-2.5-flash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
export SUPABASE_SUMMARY_JOBS_TABLE=summary_jobs
```

Start the backend:

```bash
npm run dev:backend
```

## Common commands

```bash
npm run dev:frontend
npm run dev:backend
npm run build
npm run lint
```

## API

- `GET /api/health`
- `POST /api/summarize`
- `GET /api/summarize/{job_id}`

`POST /api/summarize` now accepts multipart form-data with a `video` file and returns a job kickoff payload instead of the final summary:

```json
{
  "job_id": "uuid",
  "status": "processing",
  "stage": "persisting_upload"
}
```

The frontend should poll `GET /api/summarize/{job_id}` for the current job state, final summary, or error.

For duration validation, the backend prefers `ffprobe` when installed and otherwise falls back to the browser-reported video duration sent by the frontend.

## Supabase Schema

Create a `summary_jobs` table in Supabase with the columns expected by the backend. A starter SQL definition is included in [`backend/supabase_summary_jobs.sql`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/backend/supabase_summary_jobs.sql).
