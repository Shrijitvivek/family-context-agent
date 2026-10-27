# API Reference

The API is implemented with FastAPI and is mounted under `/api/v1`. When the backend is running, the interactive schema is available at [Swagger UI](http://localhost:8000/docs) and [OpenAPI JSON](http://localhost:8000/openapi.json). These generated schemas are the source of truth for request and response models.

## Base URLs

- Backend API: `http://localhost:8000/api/v1`
- Health endpoint outside the versioned router: `GET http://localhost:8000/health`
- Versioned database health: `GET http://localhost:8000/api/v1/health`

## Route groups

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Checks API and database status (versioned route) |
| GET | `/families` | List families |
| POST | `/families` | Create a family |
| GET | `/families/{family_id}` | Get family details |
| GET | `/families/{family_id}/members` | List members; supports `include_inactive` |
| POST | `/families/{family_id}/members` | Add a member |
| PATCH | `/families/{family_id}/members/{member_id}` | Update a member |
| POST | `/commitments` | Create a commitment |
| GET | `/commitments` | Search/list commitments using query parameters |
| GET | `/commitments/{commitment_id}` | Get a commitment; requires `family_id` query context |
| PATCH | `/commitments/{commitment_id}` | Update a commitment |
| POST | `/commitments/dependencies` | Create a commitment dependency |
| POST | `/expenses` | Record an expense |
| GET | `/expenses` | List expenses with supported filters |
| GET | `/expenses/summary` | Return a calculated expense summary |
| GET | `/priorities` | List attention items for a family (`family_id` query parameter) |
| POST | `/priorities/recalculate` | Recalculate attention items for a family |
| GET | `/timeline` | Return chronological commitments; supports family, date, and member filters |
| POST | `/chat` | Send a chat message and return the assistant response and tool results |
| GET | `/chat/{conversation_id}` | Retrieve conversation history; requires `family_id` query parameter |
| POST | `/documents/upload` | Upload and process a document |
| GET | `/documents` | List documents for a family; optional member filter |
| GET | `/documents/{document_id}` | Get document processing details; requires `family_id` query parameter |
| POST | `/documents/{document_id}/process` | Retry document processing |
| POST | `/documents/{document_id}/confirm` | Confirm proposed document fields and create a commitment |
| GET | `/demo/scenarios` | List available demo scenario definitions |
| POST | `/demo/scenarios/{scenario_id}/load` | Load a fictional scenario |
| POST | `/demo/reset` | Reset the Nair Family demo scenario |

All paths in the table are relative to `/api/v1`, except the root `/health` endpoint noted above.

## Chat flow

`POST /chat` accepts a `ChatRequest` schema. It includes family context, the user's message, and optional conversation/member/document identifiers supported by the schema. The response contains the conversation ID, assistant message, tool calls, tool results, and a clarification flag. Retrieve earlier messages with `GET /chat/{conversation_id}?family_id=...`.

## Document flow

1. Upload a supported PDF, JPEG, or PNG document.
2. The backend validates/stores it and extracts document text/data.
3. The response includes the processing status and proposed fields.
4. Review the proposal and explicitly confirm it before creating a commitment.
5. If processing fails, retry with the process endpoint where appropriate.

## Errors and validation

The backend returns structured errors for domain failures and validates request/tool inputs with Pydantic. A successful HTTP response or model-generated text should still be checked against the actual returned data for state-changing actions. The OpenAPI schema shows the precise types and required fields for the checked-out revision.
