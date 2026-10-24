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

## Environment Setup

### Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- A valid Nebius API key
- Git, if cloning the repository

### Configure Environment Variables

From the project root, create your local environment file:

```bash
cp .env.example .env
```

Edit `.env` and set your actual `NEBIUS_API_KEY`. Verify `NVIDIA_MODEL_NAME` and `NEBIUS_BASE_URL` match the model and endpoint available to your Nebius account.

Do not commit `.env` or expose API keys in logs, screenshots, or shared terminal output.

### Start the Application with Docker

Run this command from the project root:

```bash
docker compose up --build
```

Docker Compose builds the frontend and backend images, starts PostgreSQL, waits for the database health check, runs database migrations, and starts the backend API. The frontend starts after the backend passes its health check.

To run the services in the background:

```bash
docker compose up --build -d
```

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Swagger API documentation:** http://localhost:8000/docs
- **Backend health:** http://localhost:8000/health
- **Frontend API proxy health:** http://localhost:5173/api/v1/health

### Verify and Manage Services

Check service status:

```bash
docker compose ps
```

View backend logs:

```bash
docker compose logs --tail=100 backend
```

Stop the services:

```bash
docker compose down
```

The PostgreSQL database and uploaded documents use named Docker volumes. Stopping services with `docker compose down` preserves these volumes. Avoid `docker compose down -v` unless you intentionally want to delete them.

### Local Development Without Docker

For local development, configure the environment variables for your local PostgreSQL instance and follow the backend and frontend development instructions maintained by the project. The Docker-specific database hostname `db` is intended for containers on the Compose network; a locally running backend normally connects through `localhost`.

## Implementation order

Follow the design blueprint: database and APIs first, then frontend/backend integration, NVIDIA model client, controlled tools, dependencies and priorities, document processing, scheduled checks, judge scenarios, tests, deployment, and polish.

## Judge Mode — Nair Family Demo

Judge Mode provides a repeatable synthetic household for demonstrating the Family Context Agent without modifying real household data.

### Demo Household

- **Arun** — Father
- **Meera** — Mother
- **Lakshmi** — Grandmother
- **Rahul** — College Student

The scenario includes household expenses, utility bills, medical appointments, a college project deadline, home repairs, commitment dependencies, and completed tasks.

### Load or Reset Demo Data

Start the backend and open the Swagger UI at `/docs`.

- `GET /demo/scenarios` — List available demo scenarios.
- `POST /demo/reset` — Reset the Nair Family demo.
- `POST /demo/scenarios/nair-family/load` — Load the Nair Family scenario.

Resetting should affect only the deterministic demo household.

### Demonstration Flow

1. Load the Nair Family scenario.
2. Review family members and household expenses.
3. Ask the agent about pending commitments and upcoming deadlines.
4. Explore dependencies between commitments.
5. Create or update a commitment.
6. Reset the demo to restore the original synthetic dataset.
7. Review agent event logs to demonstrate observability.

