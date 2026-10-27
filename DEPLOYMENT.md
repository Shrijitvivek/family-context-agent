# Deployment Instructions

## Available deployment path: Docker Compose

The repository currently includes `docker-compose.yml`, a backend Dockerfile, and a frontend Dockerfile with Nginx. The Compose setup is suitable for local runs and controlled demonstrations. It is not, by itself, a complete production deployment plan.

### Configure secrets and settings

1. Copy `.env.example` to `.env` at the repository root.
2. Set `NEBIUS_API_KEY` and `NVIDIA_MODEL_NAME` to valid values for your Nebius account.
3. Replace the example database password.
4. Review CORS origins, timezone, upload limit, and any optional Supabase storage credentials.
5. Keep `.env` out of source control and never embed API secrets in frontend `VITE_*` variables.

### Build and start

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 backend
```

The Compose backend command runs `alembic upgrade head` before starting Uvicorn. The frontend is served by Nginx and proxies API requests to the backend service.

### Check and stop

- Frontend: `http://localhost:5173`
- API health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

```bash
docker compose down
```

The Compose file uses named volumes for PostgreSQL data and uploaded documents; `down` preserves those volumes. `docker compose down -v` removes volumes and should be reserved for intentional cleanup/reset.

## Ports and storage

- Frontend is exposed on host port `5173`.
- Backend is exposed on host port `8000`.
- PostgreSQL container port `5432` is published on host port `5433`; the backend uses the Compose service hostname `db`.
- The Compose file mounts named volumes for PostgreSQL and `/app/storage/uploads`.
- The code contains local and Supabase storage adapters, while the dependency wiring initializes the Supabase adapter. For deployments, provision the private `family-documents` bucket and configure valid Supabase URL/service-role credentials, or explicitly wire the intended storage adapter before deploying with local storage only.

## Production hardening checklist

Before using real family data or exposing the application publicly:

- Add and verify authentication and authorization at the API layer.
- Restrict access to family records and uploaded documents; verify family/member scope for every route.
- Terminate TLS/HTTPS at a trusted ingress or reverse proxy.
- Use a secret manager or managed environment secrets instead of a committed `.env`.
- Use strong database credentials, private networking, least-privilege access, and tested backups/restore procedures.
- Configure durable private document storage and retention/deletion policy.
- Enable the deadline scheduler on only one API worker; the scheduler is in-process.
- Configure logging, metrics, alerting, rate limits, and health/readiness checks.
- Review CORS, upload limits, MIME/type validation, and resource limits.
- Test Alembic migrations against a staging database before production updates.
- Run unit/integration tests and verify critical user journeys in the target environment.
- Select and publish an open-source license if intended; no root `LICENSE` file was present in the inspected branch.

## Other hosting targets

`deployment/` currently contains only a placeholder on the inspected branch, so no independent Kubernetes/cloud-hosting manifest is provided here. Add target-specific instructions only after that deployment configuration has been implemented and verified.
