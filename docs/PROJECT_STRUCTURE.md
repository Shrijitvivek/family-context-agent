# Project Structure

The repository separates the frontend, backend, persistence, AI integration, and test suites.

```text
family-context-agent/
├── backend/
│   ├── app/
│   │   ├── agents/             # Agent prompt, state, clarification, orchestration
│   │   ├── api/v1/endpoints/   # REST route handlers
│   │   ├── clients/            # Nebius AI client and document storage adapters
│   │   ├── core/               # Settings, constants, errors, logging
│   │   ├── db/                 # SQLAlchemy base and session
│   │   ├── jobs/               # Scheduled deadline checks
│   │   ├── models/             # SQLAlchemy table models
│   │   ├── repositories/       # Database queries
│   │   ├── schemas/            # Pydantic request/response contracts
│   │   ├── services/           # Business workflows and rules
│   │   ├── tools/              # Seven controlled agent tools
│   │   └── utils/              # Date and file helpers
│   ├── alembic/versions/       # Database migrations
│   ├── synthetic_data/scenarios/
│   └── tests/                  # Unit, integration, and scenario tests
├── frontend/src/               # React pages, components, hooks, API clients
├── demo_documents/             # Root-level demo PDFs and images
├── synthetic_data/             # Project-level synthetic data
├── evaluation/                 # Dataset and result locations
├── design_docs/                # Original team design references
├── docs/                       # Engineering documentation
├── deployment/                 # Deployment folder (currently placeholder)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Backend layering

The intended dependency flow is `API → service → repository → database`. The agent/tool layer invokes application service methods; it does not execute free-form SQL. The model client is isolated in `backend/app/clients/ai_model.py`.

## Demo assets

- Scenario JSON files are loaded from `backend/synthetic_data/scenarios/`.
- Document examples are intended to be stored in the root-level `demo_documents/` folder. The inspected `main` branch currently has only the folder placeholder; commit the approved sample PDF/JPG/PNG files there for a fresh-clone demo.
