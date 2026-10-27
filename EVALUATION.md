# Evaluation and Test Status

This document distinguishes automated test coverage present in the repository from quantitative benchmark results. It does not report a pass rate or accuracy score because no committed evaluation dataset/results were present in the inspected `main` branch: `evaluation/datasets/` and `evaluation/results/` contained placeholders only.

## Automated test coverage in the repository

### Backend unit tests

Under `backend/tests/unit/`, the suite includes tests for:

- AI model client response/error handling
- Tool registry validation and agent-tool errors
- Clarification and commitment workflows
- Expense date handling
- Priority-service behavior
- Repository queries
- Chat/document interactions and upload validation
- Document/notification repositories

### Backend integration tests

Under `backend/tests/integration/`, test modules cover:

- Agent decision/tool correctness and PostgreSQL integration
- Family/member scoping
- Chat API, chat flows, and conversation lifecycle
- Commitment lifecycle and acceptance
- Dependency/priority lifecycle
- Document processing flow
- Scheduled deadline checks and scheduler lifecycle
- Error/failure handling and tool integration

### Scenario tests

`backend/tests/scenarios/` contains core scenario and Judge Mode tests.

### Frontend tests

The frontend uses Vitest, jsdom, and Testing Library. Test modules cover critical UI journeys, Judge Mode, and timeline/API interaction behavior. Run `npm test` in `frontend/`.

## Reproduce the checks

From the repository root, configure the test database and environment first. Then run:

```bash
pip install -r backend/requirements-dev.txt
pytest
```

Frontend checks:

```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
```

A live Nebius API key and network connectivity may be needed for manual, end-to-end AI checks; automated tests may use fakes/mocks to avoid provider dependencies. Database integration tests need an available database and correct test settings.

## Suggested manual acceptance checklist

Record the date, commit SHA, environment, prompt, expected outcome, observed outcome, and pass/fail for each test:

1. Start Docker Compose and confirm API/database health.
2. List demo scenarios and load the Nair Family scenario.
3. Ask for household priorities and compare results with the stored commitments/dependencies.
4. Record an expense, then verify amount/category/member/date and summary totals in the UI/API/database.
5. Create a dated commitment; verify the persisted due date and assignment.
6. Update an existing commitment and confirm the existing record changed instead of a duplicate being created.
7. Create a prerequisite dependency and verify the timeline/priority explanation.
8. Upload a PDF or image, inspect the proposed extracted fields, and confirm it before creating a commitment.
9. Test missing fields, ambiguous matching commitments, provider timeout/authentication errors, and unsupported requests.
10. Reset Judge Mode and confirm the intended synthetic scenario is restored.

## Reporting results

When a real evaluation is performed, save the cases/expected answers in `evaluation/datasets/` and the observed results/summary in `evaluation/results/`. Report the number of cases, correct/partial/failed results, failure categories, model identifier, and run date. Do not call an unexecuted test passing or infer an aggregate score from the presence of test files alone.
