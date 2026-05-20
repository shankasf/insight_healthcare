# ai-service (Insight Healthcare)

Python FastAPI service that powers the Insight Healthcare chatbot. See the repo root `README.md` for full architecture, ERD, and seed data. This file only captures ai-service-local quirks.

## Run locally

```bash
cd ai-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
export DATABASE_URL=postgresql+asyncpg://postgres:<pw>@72.62.162.83:5432/insight_healthcare

alembic upgrade head            # creates tables + extensions + static seed + slot generator
python -m scripts.embed_faqs    # fills FAQ embeddings (needs OPENAI_API_KEY)

uvicorn app.main:app --reload --port 8000
```

## Re-seed (idempotent)

`python -m scripts.seed_clinic` re-runs the 002 + 003 logic against the live DB. Clinic settings, providers, plans, and members use fixed UUIDs with `ON CONFLICT (id) DO UPDATE`. Slots and appointments are wiped and regenerated so the demo always has fresh "tomorrow 10:00" windows.

## HTTP contract

- `POST /chat` — body `{ "message": str, "session_key": str }` → `{ "reply": str, "agent_used": "triage"|"appointment"|"insurance"|"knowledge"|"out_of_scope", "session_key": str }`
- `GET /health` → `{ "status": "ok" }`

Frontend is expected to talk to this via a Next.js API route — CORS allows `http://localhost:3000` by default.

## Agent layout

- `app/agents/triage.py` — head agent, never answers directly; only `handoffs`.
- `app/agents/appointment.py` — tools: `list_available_slots`, `book_appointment`, `cancel_appointment`.
- `app/agents/insurance.py` — tools: `check_payer_accepted`, `verify_member`.
- `app/agents/knowledge.py` — tools: `get_clinic_info`, `search_clinic_faqs`.

All tools live in `app/agents/tools.py` and depend on `app/repositories/*` — agents never touch raw SQL (DIP).

## Notes on decisions

- Tool functions open their own short-lived `AsyncSession` (`session_scope` ctx manager) rather than reusing the request-scoped session because the Agents SDK invokes tools out-of-band and may interleave them.
- IVFFlat is created with `lists = 100`. With only 15 FAQs the index falls back to seq-scan anyway, but the parameter is set so it scales when the FAQ corpus grows.
- `chat_events` records `triage` only when the head agent answered itself (refusal or pre-handoff failure). Anything routed correctly is logged as the specialist's lowercased name.
- `ip_hash` is SHA-256 of `X-Forwarded-For[0]` (fallback to `request.client.host`). Raw IP is never stored.
