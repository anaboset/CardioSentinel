# CardioSentinel MAS — Production Deployment Guide

> **Research & Demonstration Only.** Not intended for clinical use without regulatory approval.

## Quick Start

### Docker (Recommended)

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY

docker compose up --build
# Open http://localhost:8000
```

### Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
cp .env.example .env
# Set GROQ_API_KEY in .env

uvicorn api.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
# Web UI:   http://localhost:8000/
```

### CLI

```bash
python main.py
```

---

## Architecture

The primary production surface is the FastAPI service in [api/main.py](api/main.py). The legacy Streamlit UI in [pages/](pages/) and the human-review helpers in [hitl/](hitl/) remain available for local demos and future integration, but are not required by the main deployed workflow.

```
┌─────────────────────────────────────────────────────┐
│  FastAPI REST API + Web UI (api/)                   │
│  POST /api/v1/analyze  ·  GET /api/v1/health        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  LangGraph Orchestration (core/graph.py)            │
│  Input Validation → Guideline → Risk → Medication   │
│  → Patient → Human Review → Finalize                │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Agents (agents/)                                   │
│  Guideline · Risk · Medication · Patient            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Tools & Services                                   │
│  RAG Engine · ASCVD Calculator · openFDA · Local DB │
└─────────────────────────────────────────────────────┘
```

---

## API Reference

### `GET /api/v1/health`

Health check for monitoring and load balancers.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 123.4,
  "services": {
    "groq_llm": "configured",
    "rag_engine": "ready",
    "openfda": "ready"
  }
}
```

### `POST /api/v1/analyze`

Run the full multi-agent analysis workflow.

**Request:**
```json
{
  "patient": {
    "age": 65,
    "sex": "Male",
    "bp": "150/95",
    "ldl": 160,
    "conditions": ["hypertension", "smoking"],
    "medications": ["lisinopril"]
  },
  "query": "What is the first-line therapy for this patient?"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "workflow_status": "completed",
    "guidelines": { "recommendations": [...], "evidence_sources": [...], "confidence": "high" },
    "risk": { "score": 15.2, "classification": "High", "factors": [...] },
    "medication_safety": { "safe_to_proceed": true, "interactions": [], "contraindications": [] },
    "patient_communication": { "summary": "...", "lifestyle_advice": [...] },
    "audit_trail": [...]
  }
}
```

### `GET /api/v1/guidelines/search?q=...&conditions=hypertension`

Direct guideline corpus search.

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes* | — | Groq API key for patient communication agent |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | LLM model name |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `OPENFDA_ENABLED` | No | `false` | Enable live openFDA drug interaction lookups |
| `LANGCHAIN_TRACING_V2` | No | `false` | Enable LangSmith observability |
| `LANGCHAIN_API_KEY` | No | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | No | `cardiosentinel` | LangSmith project name |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated) |

*Patient agent gracefully degrades without API key; other agents work independently.

---

## Testing

```bash
pytest tests/ -v --cov --cov-report=term-missing
# 89 tests, ≥70% coverage on core modules
```

Test categories:
- `test_tools.py` — Unit tests for RAG, ASCVD risk, drug tools
- `test_agents.py` — Unit tests for all 4 agents
- `test_security.py` — Input validation and content filtering
- `test_integration.py` — LangGraph workflow and routing
- `test_pipeline.py` — End-to-end pipeline tests
- `test_api.py` — FastAPI endpoint tests
- `test_resilience.py` — Retry and loop limit tests

---

## Logging & Observability

- Structured logging via Python `logging` module (format in `config.py`)
- LangSmith tracing when `LANGCHAIN_TRACING_V2=true`
- Full audit trail in every workflow response
- Health endpoint for uptime monitoring

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `GROQ_API_KEY not configured` | Missing API key | Set `GROQ_API_KEY` in `.env` |
| Patient summary empty | LLM call failed | Check API key and model name |
| Slow drug checks | openFDA enabled | Set `OPENFDA_ENABLED=false` (default) |
| Validation error 422 | Invalid patient data | Ensure BP format `SBP/DBP`, age 18–120 |
| `smoking` not recognized | Condition alias | Use `smoking` or `smoker` — both normalized |
| Docker health check fails | App not ready | Wait 15s start period; check logs |

---

## Maintenance

- **Guideline corpus**: Edit `data/guidelines_corpus.py` to add/update clinical guidelines
- **Drug knowledge**: Edit `data/drug_knowledge.py` for interactions and contraindications
- **Risk thresholds**: Adjust `RISK_THRESHOLDS` in `config.py`
- **HITL routing**: Modify `core/edge_routing.py`

---

## Security Notes

- Input validation on all patient data and queries
- Content filtering on LLM outputs (unsafe medical advice removed)
- Medical disclaimer appended to patient communications
- No PHI persistence by default (stateless API)
- CORS configurable via environment variable