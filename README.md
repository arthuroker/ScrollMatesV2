# ScrollMates

ScrollMates is a split-stack app with a React + Tailwind frontend in [`frontend/`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/frontend) and a FastAPI backend in [`backend/`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/backend).

## Prerequisites

- Node.js 24+
- Python 3.11+
- `ffprobe` on your `PATH` is recommended but no longer required for common browser uploads
- A Gemini API key
- A Supabase project with Auth enabled and the schema from the project prompt already applied

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
export GEMINI_EMBEDDING_MODEL=text-embedding-004
export SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
export SUPABASE_JWT_SECRET=your_supabase_jwt_secret
export ADMIN_SECRET=your_admin_secret
export MATCH_TOP_K=5
export MATCH_POLL_INTERVAL_SECONDS=10
export CORS_ALLOW_ORIGINS=http://localhost:5173
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

Copy [`frontend/.env.example`](/Users/arthuroker/Documents/Coding Projects/ScrollMates/frontend/.env.example) to `frontend/.env`:

```bash
export VITE_SUPABASE_URL=https://your-project.supabase.co
export VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## API

- `GET /api/health`
- `POST /api/upload`
- `GET /api/jobs/{job_id}`
- `GET /api/profile`
- `GET /api/matches`
- `POST /api/admin/trigger-match-run`

`POST /api/upload` accepts multipart form-data with a `video` file and returns a job kickoff payload:

```json
{
  "job_id": "uuid"
}
```

The frontend should poll `GET /api/jobs/{job_id}` until the job reaches `completed` or `failed`, then fetch `/api/profile` and `/api/matches`.

For duration validation, the backend prefers `ffprobe` when installed and otherwise falls back to the browser-reported video duration sent by the frontend. The weekly matcher runs inside the FastAPI process and polls `match_runs` for pending rows.
