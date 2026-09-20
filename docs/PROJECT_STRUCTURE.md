# Project Structure

The directory layout follows the architecture in `design_docs/Family Context Agent blue_print.pdf` and keeps frontend and backend implementation fully separate.

```text
family-context-agent/
|-- backend/
|   |-- app/
|   |   |-- api/v1/endpoints/     # REST transport only
|   |   |-- agents/               # One primary agent and its prompt/state
|   |   |-- clients/              # Nebius/NVIDIA and storage adapters
|   |   |-- core/                 # Settings, logging, errors, security
|   |   |-- db/                   # SQLAlchemy base and sessions
|   |   |-- jobs/                 # Scheduled deadline/dependency checks
|   |   |-- models/               # Ten PostgreSQL table models
|   |   |-- repositories/         # Database query layer
|   |   |-- schemas/              # Pydantic contracts
|   |   |-- services/             # Business workflows and rules
|   |   |-- tools/                # Seven controlled agent tools
|   |   `-- utils/                # Date and file helpers
|   |-- alembic/                  # Database migrations
|   |-- scripts/                  # Backend maintenance commands
|   `-- tests/                    # Unit, integration, and scenario tests
|-- frontend/
|   `-- src/
|       |-- app/                  # Router and application providers
|       |-- components/           # Reusable UI by feature
|       |-- hooks/                # Query and interaction hooks
|       |-- pages/                # Six user-facing screens
|       |-- services/api/         # Typed backend API adapters
|       |-- styles/               # Tailwind/global styles
|       |-- test/                 # Frontend test setup
|       |-- types/                # Shared TypeScript contracts
|       `-- utils/                # Presentation helpers
|-- synthetic_data/               # Connected fictional scenarios
|-- demo_documents/               # Safe sample uploads
|-- evaluation/                   # Ground truth and results
|-- deployment/                   # Hosting configuration
|-- design_docs/                  # Product and architecture sources
|-- docs/                         # Engineering documentation
`-- storage/uploads/              # Ignored local upload data
```

The layering rule is `API -> service -> repository -> database`. The NVIDIA model must request actions only through the registered tool layer and must never generate or execute arbitrary SQL.
