# AI Automation Growth Platform — Live Data Edition



https://github.com/user-attachments/assets/743a8f61-2578-42b0-bcf0-5b6d537451dd


A lean multi-tenant SaaS application for live CRM records, events, AI-assisted qualification/content, human approvals, workflows, and analytics.

This edition intentionally contains **no seeded demo workspace, no demo login, no sample customer records, and no deterministic Demo AI provider**. New workspaces start empty and all metrics come from stored workspace data.

## Core pages kept

Only the product-critical pages remain in the main navigation:

1. **Dashboard** — live KPIs, recent leads, recent automation runs, AI copilot.
2. **Leads** — CRM records, qualification, next actions, outreach drafting.
3. **Events** — event planning and event-driven growth context.
4. **Content Studio** — generate editable business content from supplied live context.
5. **Meeting Intelligence** — analyze pasted real meeting notes/transcripts.
6. **Workflows** — create, edit, activate, duplicate, and test supported automations.
7. **Automation Runs** — inspect execution state, steps, inputs/outputs, failures, retries.
8. **Approvals** — human review before sensitive or external actions continue.
9. **Analytics** — live pipeline and workflow metrics from the database.
10. **Settings & Connections** — workspace identity, AI status, integration status, recent audit activity.

Removed as standalone pages because they were duplicate/thin/unfinished: Overview, Contacts, Outreach, Campaigns, AI Insights, Signals, Conversion, Automation ROI, Integrations, and Audit Logs. Important capabilities were merged into the pages above instead of being discarded.

## Live AI providers only

Supported AI modes:

- `gemini`
- `groq`
- `auto` — uses Gemini first when configured and Groq second when both keys exist.

There is **no local/demo AI fallback**. If no AI key is configured, the CRM, events, workflows, approvals, audit, and analytics still run; AI actions return a clear configuration error.

Recommended low/no-cost setup:

```env
AI_PROVIDER=auto
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash

# Optional secondary free-plan provider
GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-20b
```

Free plans and quotas are controlled by Google/Groq and can change. The application does not require OpenAI, Anthropic, LinkedIn, Airtable, Make, Zapier, or other paid API keys.

## Architecture

```text
React/Vite frontend
        |
        | /api/v1
        v
FastAPI backend
        |
        +-- Auth + tenant isolation
        +-- Live leads / events
        +-- Workflow engine
        +-- Human approvals
        +-- Analytics / audit
        +-- AI Gateway
              +-- Gemini
              +-- Groq
        |
        v
SQLite (local development)
PostgreSQL / Supabase Postgres (production)
```

## Local setup — no Python virtual environment

### Requirements

- Python 3.11+ (3.12 recommended)
- Node.js 20+ (22 recommended)
- npm

A Python virtual environment is **not required** by this project. Direct installation changes packages in the Python installation you invoke, so use a dedicated machine/interpreter if you want isolation.

### Windows quick install

From the project root:

```bat
install_no_venv.bat
```

Or manually:

```powershell
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

### Backend

Create `backend/.env` from `backend/.env.example` and set at least a strong local secret. Add Gemini and/or Groq keys only if you want AI features.

PowerShell:

```powershell
cd backend
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/health
```

### Frontend

In another terminal:

```powershell
cd frontend
$env:VITE_API_URL="http://localhost:8000/api/v1"
npm run dev
```

Open:

```text
http://localhost:5173
```

Register a workspace. It will be empty until you add live records.

## Docker

Docker also avoids a Python virtual environment:

```bash
cp .env.example .env
# add GEMINI_API_KEY and/or GROQ_API_KEY if desired
docker compose up --build
```

Docker uses PostgreSQL for persistent application records.

## Production/live database

For production set:

```env
ENVIRONMENT=production
SECRET_KEY=<strong random 32+ character secret>
DATABASE_URL=<postgresql connection string>
# or
SUPABASE_DB_URL=<postgresql connection string>
AUTO_CREATE_TABLES=false
```

Apply the SQL migration in `backend/migrations/` before starting production. Production mode intentionally rejects SQLite and automatic table creation.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `ENVIRONMENT` | `development`, `test`, or `production` |
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Local SQLite or PostgreSQL URL |
| `SUPABASE_DB_URL` | Optional PostgreSQL/Supabase DB URL override |
| `AUTO_CREATE_TABLES` | Local convenience only; false in production |
| `CORS_ORIGINS` | Allowed frontend origins |
| `AI_PROVIDER` | `auto`, `gemini`, or `groq` |
| `AI_FALLBACK_TO_SECONDARY` | In auto mode, try the second configured provider after failure |
| `AI_LOG_CONTENT` | Keep false unless sensitive prompt logging is explicitly desired |
| `GEMINI_API_KEY` | Optional Google Gemini key |
| `GEMINI_MODEL` | Gemini model ID |
| `GROQ_API_KEY` | Optional Groq key |
| `GROQ_MODEL` | Groq model ID |
| `VITE_API_URL` | Frontend API base URL |

Secrets are server-side only. Never place Gemini/Groq keys in `VITE_*` variables.

## Data behavior

- Registration creates only the organization and owner user.
- No leads, events, workflows, approvals, or run history are automatically inserted.
- Dashboard/analytics read only database records for the signed-in organization.
- AI qualification updates a lead only after a successful configured-provider response.
- AI-generated outreach/content is not treated as sent/published.
- External communication must remain behind approval and a real connector.

## Tests

Development test dependencies are separate from production dependencies:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

AI-dependent tests use test doubles; the automated suite does not spend provider quota or require a real key.

## Frontend build

```bash
cd frontend
npm ci
npm run build
```

## Important limitations

- Outbound email/LinkedIn sending is intentionally not implemented without a real connector.
- Engagement scores are meaningful only after your application supplies real engagement data.
- Meeting analysis currently accepts pasted notes/transcripts; automatic meeting-provider ingestion is not included.
- Content approval is persisted, but publishing remains disconnected until a real publishing connector is implemented.
