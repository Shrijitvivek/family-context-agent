# Family Context Agent

Starter structure for the Nebius x NVIDIA Global AI Hackathon project.

The application accepts household text, PDF, and image inputs; turns them into structured expenses and commitments; tracks dependencies and deadlines; and explains what the family should handle next.

## Repository boundaries

- `backend/` contains the FastAPI application, PostgreSQL access, one agent orchestrator, seven controlled tools, background jobs, migrations, and backend tests.
- `frontend/` contains the independent React, TypeScript, Vite, and Tailwind web client.
- `synthetic_data/` contains connected fictional household scenarios.
- `demo_documents/` contains safe sample PDFs/images for judge demonstrations.
- `evaluation/` contains ground-truth datasets and generated evaluation results.
- `deployment/` contains future deployment configuration.
- `design_docs/` remains the architecture source supplied by the team.

Backend modules are intentionally implementation-free. Each Python file contains only a module docstring describing what students should build.

## Planned MVP screens

1. Home dashboard
2. Chat
3. Timeline
4. Expenses
5. Documents
6. Judge Mode

## Planned controlled tools

1. `add_expense`
2. `get_expense_summary`
3. `create_commitment`
4. `search_commitments`
5. `update_commitment`
6. `create_dependency`
7. `get_family_priorities`

## Environment setup

The checked-in `.env.example` documents every expected variable. The local `.env` contains development placeholders and is ignored by Git. Students must add a real Nebius API key locally and must never commit it.

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements-dev.txt
```

Frontend dependencies can be prepared independently:

```powershell
Set-Location frontend
npm install
```

The Dockerfiles and `docker-compose.yml` are intentionally empty placeholders for the deployment workstream.

## Implementation order

Follow the design blueprint: database and APIs first, then frontend/backend integration, NVIDIA model client, controlled tools, dependencies and priorities, document processing, scheduled checks, judge scenarios, tests, deployment, and polish.
