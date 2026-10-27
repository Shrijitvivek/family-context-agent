# Agent and Tool Architecture

Famora AI implements one primary agent orchestrator (`backend/app/agents/orchestrator.py`) around a configured Nebius AI model client. It is not a multi-agent worker graph: the model decides whether to respond directly or request a registered application tool.

## Request flow

1. The chat endpoint receives a request and delegates to `ChatService`.
2. The service loads the conversation and relevant household context from PostgreSQL.
3. The agent builds its messages from the system prompt, conversation history, household context, and optional attached-document context.
4. `AIModelClient` sends a chat-completions request to Nebius, including registered tool definitions.
5. If the model requests a tool, `ToolRegistry` validates the name and arguments using the registered Pydantic input model.
6. The tool calls the same business service used by the REST API; the service/repository layer applies domain rules and persists changes.
7. The tool result is appended to the model conversation. The model can continue tool use or return a final response.
8. The chat response exposes tool calls/results and whether clarification is required.

The tool loop is bounded to avoid unlimited repeated calls. The model client validates the response and maps timeout, authentication, rate-limit, HTTP, and malformed-response errors into application errors.

## Registered tools

| Tool | Purpose |
|---|---|
| `add_expense` | Record a household expense with validated amount/category/date/member context |
| `get_expense_summary` | Calculate a filtered expense total and transaction count |
| `create_commitment` | Create a bill, task, appointment, test, renewal, or deadline; date-required types need due dates |
| `search_commitments` | Find existing commitments by title and supported filters before modification |
| `update_commitment` | Update an existing commitment, such as amount, status, or due date |
| `create_dependency` | Create a `MUST_COMPLETE_BEFORE` relationship between commitments |
| `get_family_priorities` | Return attention items and reasons calculated by the priority service |

## Safety and correctness boundaries

- Only tools registered by the backend can be dispatched; the model cannot directly run SQL or arbitrary Python.
- Pydantic input models and service validation protect the persistence layer even when model arguments are incomplete or malformed.
- The backend supplies the selected `family_id` and member context from the application request rather than trusting the model to choose arbitrary household scope.
- Required details trigger clarification rather than silently persisting incomplete date-bound commitments.
- Commitment search should occur before changing an existing record; ambiguous matches require clarification. Duplicate protection is implemented in the domain service/tool flow.
- The document service treats extracted fields as proposals. A commitment created from a document requires an explicit confirmation step.
- Priority ranking is deterministic and based on commitment status/dates plus dependency state; the language model is not the source of priority calculation.
- Deadline checks run with APScheduler in the API process. In multi-worker deployments, the scheduler should be enabled on only one worker.

## Key implementation locations

- Agent: `backend/app/agents/`
- Model client: `backend/app/clients/ai_model.py`
- Tool contracts and registry: `backend/app/tools/`
- Business logic: `backend/app/services/`
- Persistence: `backend/app/repositories/` and `backend/app/models/`
- API transport: `backend/app/api/v1/endpoints/`
- Scheduled checks: `backend/app/jobs/`
