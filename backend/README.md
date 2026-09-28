# Backend

FastAPI backend for the live-data AI Automation Growth Platform.

No Python virtual environment is required by the project.

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

AI is optional at startup. Add a Gemini and/or Groq key to `.env` to enable AI endpoints.

For tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

See the root `README.md` for production database, Docker, migrations, and frontend setup.
