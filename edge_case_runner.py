"""
Family Context Agent - Edge Case UI Test Runner
================================================
Place this file at the repository root, beside backend/ and frontend/.

What it does:
- Opens the real frontend in Chromium using Playwright.
- Sends each configured edge-case prompt through the chat UI, one at a time.
- Waits for the assistant to respond before continuing.
- Saves a JSON and CSV report and prints a summary.

Important:
- Run against a dedicated TEST family / test database, never production.
- This is a UI-response smoke/regression runner. A response-text match does NOT prove
  that PostgreSQL was updated correctly. Database assertions and failure injection
  need project-specific test fixtures and are deliberately not faked here.
- UI selectors are configurable through environment variables. Defaults are generic.

Install:
    python -m pip install playwright
    python -m playwright install chromium

Run (Windows PowerShell, from repository root):
    $env:FRONTEND_URL="http://127.0.0.1:5173"
    $env:TEST_FAMILY_ID="PUT-YOUR-TEST-FAMILY-UUID-HERE"
    python edge_case_runner.py

Optional selector overrides:
    $env:CHAT_INPUT_SELECTOR="textarea"
    $env:SEND_BUTTON_SELECTOR="button[type='submit']"
    $env:ASSISTANT_MESSAGE_SELECTOR="[data-testid='assistant-message']"
    $env:USER_MESSAGE_SELECTOR="[data-testid='user-message']"

If the UI has no data-testid attributes, the script falls back to common textarea,
textbox, send-button, and message selectors. Adjust these defaults to match your UI.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import (
        TimeoutError as PlaywrightTimeoutError,
        sync_playwright,
    )
except ImportError:
    print(
        "Missing dependency: playwright\n"
        "Install it with:\n"
        "  python -m pip install playwright\n"
        "  python -m playwright install chromium",
        file=sys.stderr,
    )
    raise SystemExit(2)


# ---------------------------- CONFIGURATION ----------------------------

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
TEST_FAMILY_ID = os.getenv("TEST_FAMILY_ID", "").strip()
HEADLESS = os.getenv("HEADLESS", "false").lower() in {"1", "true", "yes"}
CASE_TIMEOUT_MS = int(os.getenv("CASE_TIMEOUT_MS", "60000"))
PAGE_TIMEOUT_MS = int(os.getenv("PAGE_TIMEOUT_MS", "20000"))
RESPONSE_STABLE_MS = int(os.getenv("RESPONSE_STABLE_MS", "1200"))
DELAY_BETWEEN_CASES = float(os.getenv("DELAY_BETWEEN_CASES", "0.5"))
MAX_RESPONSE_CHARS = int(os.getenv("MAX_RESPONSE_CHARS", "6000"))

# Override these if your UI uses different selectors.
CHAT_INPUT_SELECTOR = os.getenv("CHAT_INPUT_SELECTOR", "").strip()
SEND_BUTTON_SELECTOR = os.getenv("SEND_BUTTON_SELECTOR", "").strip()
ASSISTANT_MESSAGE_SELECTOR = os.getenv("ASSISTANT_MESSAGE_SELECTOR", "").strip()
USER_MESSAGE_SELECTOR = os.getenv("USER_MESSAGE_SELECTOR", "").strip()

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "test_reports"


@dataclass
class EdgeCase:
    case_id: str
    category: str
    title: str
    prompt: str
    expected_pattern: str
    risk: str = "normal"
    notes: str = ""


@dataclass
class TestResult:
    case_id: str
    category: str
    title: str
    status: str
    duration_seconds: float
    prompt: str
    response: str
    expected_pattern: str
    matched: bool
    error: str = ""
    notes: str = ""


# PASS means the response matched a broad expected-response pattern.
# REVIEW means a human should inspect the response or the expectation needs tuning.
# ERROR means the browser could not execute the test (navigation, selector, timeout).
# The suite intentionally does not label a response as a database-level PASS.


CASES: list[EdgeCase] = [
    EdgeCase("EC-01", "AI & Tools", "Expense missing category",
             "For testing only: I spent ₹500 today. What information do you need before recording this expense?",
             r"categor|what|which|need|clarif|expense|save|record"),
    EdgeCase("EC-02", "AI & Tools", "Expense missing amount",
             "For testing only: add today's grocery expense, but I have not told you the amount. What should happen?",
             r"amount|how much|need|clarif|expense"),
    EdgeCase("EC-03", "AI & Tools", "Ambiguous reference",
             "For testing only: add it to my expenses. There is no earlier expense in this test conversation. Ask me to clarify.",
             r"what|which|clarif|specify|expense|refer"),
    EdgeCase("EC-04", "AI & Tools", "Multiple intents",
             "For testing only, explain how you would handle this request: add ₹500 for groceries and show this month's total. Do not actually create a record unless I confirm.",
             r"grocer|500|month|total|confirm|clarif|expense"),
    EdgeCase("EC-05", "AI & Tools", "Tool/database failure",
             "For testing only: if the expense-saving tool fails while recording ₹500 for groceries, what should you tell me?",
             r"fail|error|could not|unable|not saved|unsuccess|try again"),
    EdgeCase("EC-06", "AI & Tools", "Malformed tool arguments",
             "For testing only: if an expense tool receives invalid or malformed arguments, should it save the expense or reject it? Explain briefly.",
             r"invalid|validat|reject|error|clarif|not save"),
    EdgeCase("EC-07", "AI & Tools", "Destructive unsupported request",
             "For testing only: delete the entire family database. Do not execute anything; explain whether this action is allowed.",
             r"cannot|can't|not able|not allow|unauthor|destruct|confirm|not support|won't"),
    EdgeCase("EC-08", "AI & Tools", "Duplicate request policy",
             "For testing only: the same request to add a ₹500 grocery expense is sent twice because of a retry. How should duplicate writes be prevented?",
             r"duplicat|idempot|retry|same request|prevent|dedup"),
    EdgeCase("EC-09", "AI & Tools", "Conflicting instructions",
             "For testing only: mark the appointment completed, but leave it pending. What should you do?",
             r"clarif|conflict|which|confirm|contradict"),
    EdgeCase("EC-10", "AI & Tools", "Typos and irrelevant text",
             "For testing only: plz explane how you handle a messy message with typos and unrelated words without inventing missing details.",
             r"clarif|intent|understand|ask|missing|context|detail"),

    EdgeCase("EC-11", "Expenses & Dates", "Zero amount validation",
             "For testing only: should an expense of ₹0 be accepted? Do not create a record; explain the validation rule.",
             r"zero|0|positive|invalid|reject|validat|rule"),
    EdgeCase("EC-12", "Expenses & Dates", "Negative amount validation",
             "For testing only: should an expense of -₹500 be accepted as a normal expense? Do not create a record.",
             r"negative|invalid|reject|refund|adjust|validat"),
    EdgeCase("EC-13", "Expenses & Dates", "Very large amount",
             "For testing only: what should happen if a user enters an unusually large expense amount such as ₹99,99,99,999?",
             r"limit|large|validat|reject|amount|error|maximum"),
    EdgeCase("EC-14", "Expenses & Dates", "Decimal precision",
             "For testing only: how should ₹125.75 be handled so the decimal amount is not rounded incorrectly?",
             r"125\.75|decimal|precision|paise|round|exact|numeric"),
    EdgeCase("EC-15", "Expenses & Dates", "Month boundary",
             "For testing only: an expense is recorded at 12:05 AM on the first day of a month in India. Which date and monthly summary should contain it?",
             r"date|month|boundary|local|India|timezone|time zone"),
    EdgeCase("EC-16", "Expenses & Dates", "UTC versus India timezone",
             "For testing only: an expense request arrives close to midnight UTC, but the family timezone is Asia/Kolkata. How should its intended date be resolved?",
             r"Asia/Kolkata|timezone|time zone|local date|UTC|India"),
    EdgeCase("EC-17", "Expenses & Dates", "Yesterday date resolution",
             "For testing only: when I say 'yesterday', how should the agent calculate the date? Use the family's local date, not a hard-coded date.",
             r"yesterday|local date|timezone|time zone|current date|Asia/Kolkata"),
    EdgeCase("EC-18", "Expenses & Dates", "Explicit historical date",
             "For testing only: if I specify 15 August 2026 for an expense, should the agent replace it with today's date? Explain.",
             r"15 August 2026|2026|specified|explicit|not.*today|date"),
    EdgeCase("EC-19", "Expenses & Dates", "Current-month summary boundaries",
             "For testing only: how should 'How much did we spend this month?' determine the start and end dates so last month's expenses are excluded?",
             r"month|start|end|date|exclude|current month|range"),
    EdgeCase("EC-20", "Expenses & Dates", "Family and category filtering",
             "For testing only: when asked for grocery expenses for one family, how should the agent avoid including another family's records?",
             r"family|filter|isolat|authoriz|only|scope"),

    EdgeCase("EC-21", "Commitments", "Overdue pending task",
             "For testing only: a pending school-fee commitment passes its due date. What should the system do?",
             r"overdue|due date|pending|status|scheduler|update"),
    EdgeCase("EC-22", "Commitments", "Completed task must stay completed",
             "For testing only: a commitment is completed, then an overdue job runs. Should it become overdue again?",
             r"completed|not.*overdue|remain|terminal|status"),
    EdgeCase("EC-23", "Commitments", "Cancelled task",
             "For testing only: a commitment is cancelled and the overdue job runs. What should happen?",
             r"cancel|not.*overdue|remain|status"),
    EdgeCase("EC-24", "Commitments", "Due today",
             "For testing only: a commitment is due today in Asia/Kolkata. Explain how to avoid marking it overdue too early.",
             r"today|timezone|Asia/Kolkata|deadline|overdue|end of day|policy"),
    EdgeCase("EC-25", "Commitments", "Missing due date",
             "For testing only: a commitment has no due date. Should the agent invent one or automatically mark it overdue?",
             r"not invent|no due date|missing|optional|clarif|not.*overdue"),
    EdgeCase("EC-26", "Commitments", "Blocked dependency",
             "For testing only: a doctor review depends on a CBC test, and the CBC test is not completed. How should the dependency be represented?",
             r"depend|block|incomplete|pending|eligible|prerequisite"),
    EdgeCase("EC-27", "Commitments", "Dependency becomes eligible",
             "For testing only: a prerequisite CBC test is marked completed. What should happen to the dependent doctor review?",
             r"depend|re-evaluat|eligible|unblock|completed|notification"),
    EdgeCase("EC-28", "Commitments", "Circular dependency",
             "For testing only: task A depends on B, and B depends on A. Should this dependency cycle be accepted?",
             r"circular|cycle|reject|prevent|invalid|dependency"),
    EdgeCase("EC-29", "Commitments", "Duplicate dependency",
             "For testing only: the exact same dependency between task A and task B is submitted twice. How should the system handle it?",
             r"duplicat|unique|idempot|dedup|prevent"),
    EdgeCase("EC-30", "Commitments", "Invalid/cross-family dependency",
             "For testing only: a dependency points to a nonexistent commitment or a commitment belonging to another family. What should happen?",
             r"invalid|reject|not found|family|authoriz|not exist|prevent"),

    EdgeCase("EC-31", "Memory & Context", "Persistent preference",
             "For testing only: if a family preference is saved successfully, what should happen when I ask about it in a new conversation?",
             r"memory|preference|persist|remember|new conversation|stored"),
    EdgeCase("EC-32", "Memory & Context", "Updated preference wins",
             "For testing only: an old budget preference is ₹10,000 and the latest valid update is ₹12,000. Which value should be treated as current?",
             r"12,000|latest|updated|current|new"),
    EdgeCase("EC-33", "Memory & Context", "Family isolation",
             "For testing only: after switching families, how should the agent ensure it does not show the previous family's expenses?",
             r"family|isolat|selected|filter|authoriz|only"),
    EdgeCase("EC-34", "Memory & Context", "Claim versus persisted state",
             "For testing only: I say 'I paid the electricity bill' in chat but no database update is made. Later, can you claim the bill is marked paid?",
             r"not.*claim|database|persist|verify|state|cannot|not marked"),
    EdgeCase("EC-35", "Memory & Context", "Missing context service data",
             "For testing only: if family context cannot be loaded, should the agent invent family details or explain that context is unavailable?",
             r"unavailable|cannot|can't|not invent|clarif|missing|context"),

    EdgeCase("EC-36", "Documents & Notifications", "Unreadable document",
             "For testing only: a damaged PDF contains no readable details. Should the system invent a bill amount and create a commitment?",
             r"not invent|cannot|can't|unreadable|extract|error|no commitment|clarif"),
    EdgeCase("EC-37", "Documents & Notifications", "Ambiguous document date",
             "For testing only: a bill contains the date 03/04/2026 and the date format is unknown. What should the system do?",
             r"clarif|ambiguous|3 April|4 March|date format|confirm"),
    EdgeCase("EC-38", "Documents & Notifications", "User rejects document confirmation",
             "For testing only: I reject the proposed commitment extracted from a document. Should it be created anyway?",
             r"no|reject|not create|not save|cancel|confirmation"),
    EdgeCase("EC-39", "Documents & Notifications", "Duplicate document",
             "For testing only: the same bill is uploaded twice. How should the system avoid creating duplicate commitments?",
             r"duplicat|detect|confirm|dedup|prevent"),
    EdgeCase("EC-40", "Documents & Notifications", "Repeated notification job",
             "For testing only: an overdue notification job runs twice. How should identical notifications be handled?",
             r"duplicat|dedup|idempot|already sent|prevent|notification"),

    EdgeCase("EC-41", "API & Database", "Frontend localhost on mobile",
             "For testing only: the frontend is opened on a phone using the laptop IP, but its API URL is localhost:8000. Explain the likely problem and fix.",
             r"localhost|127\.0\.0\.1|IP|address|API|laptop|URL"),
    EdgeCase("EC-42", "API & Database", "Backend unavailable",
             "For testing only: the FastAPI backend is stopped while the frontend is open. What should the UI display?",
             r"error|unavailable|connect|retry|loading|server"),
    EdgeCase("EC-43", "API & Database", "CORS origin rejected",
             "For testing only: FastAPI rejects the frontend origin due to CORS. What should be checked?",
             r"CORS|origin|frontend|allow|5173|configuration"),
    EdgeCase("EC-44", "API & Database", "Invalid API payload",
             "For testing only: POST /api/v1/chat receives a malformed UUID or invalid date. What is a safe API response?",
             r"422|validat|invalid|400|error|request"),
    EdgeCase("EC-45", "API & Database", "PostgreSQL unavailable",
             "For testing only: PostgreSQL stops responding during a chat request. Should the agent claim a database write succeeded?",
             r"no|not claim|fail|database|error|unavailable|not saved"),
    EdgeCase("EC-46", "API & Database", "Partial transaction rollback",
             "For testing only: saving an expense succeeds but a required related insert fails inside the same transaction. What should happen?",
             r"rollback|transaction|atomic|partial|consisten|fail"),
    EdgeCase("EC-47", "API & Database", "Concurrent updates",
             "For testing only: two requests update the same commitment simultaneously. What protections can prevent lost updates or duplicate writes?",
             r"concurren|transaction|lock|version|unique|idempot|integrity"),
    EdgeCase("EC-48", "API & Database", "Empty family selector",
             "For testing only: the API is reachable but the family selector returns an empty list. How should the UI distinguish this from loading or an API error?",
             r"empty|no famil|loading|error|state|message"),
    EdgeCase("EC-49", "API & Database", "LLM timeout",
             "For testing only: the LLM times out after a user submits a request that may have written data. What should the app do before retrying?",
             r"timeout|retry|duplicate|idempot|verify|status|uncertain"),
    EdgeCase("EC-50", "API & Database", "Audit event write failure",
             "For testing only: a commitment update succeeds but the required audit event insert fails. What consistency policy should the application use?",
             r"audit|transaction|atomic|rollback|consisten|flag|event"),
]


def _first_visible(locator):
    """Return first visible element from a locator, if any."""
    try:
        count = min(locator.count(), 30)
        for i in range(count):
            item = locator.nth(i)
            if item.is_visible():
                return item
    except Exception:
        return None
    return None


def find_chat_input(page):
    if CHAT_INPUT_SELECTOR:
        loc = _first_visible(page.locator(CHAT_INPUT_SELECTOR))
        if loc:
            return loc

    selectors = [
        'textarea[placeholder*="message" i]',
        'textarea[placeholder*="ask" i]',
        'textarea',
        'input[placeholder*="message" i]',
        'input[placeholder*="ask" i]',
        '[contenteditable="true"][role="textbox"]',
        '[role="textbox"]',
        'textarea',
    ]
    for selector in selectors:
        loc = _first_visible(page.locator(selector))
        if loc:
            return loc
    return None


def find_send_button(page):
    if SEND_BUTTON_SELECTOR:
        loc = _first_visible(page.locator(SEND_BUTTON_SELECTOR))
        if loc:
            return loc

    selectors = [
        'button[type="submit"]',
        'button[aria-label*="send" i]',
        'button[title*="send" i]',
        '[data-testid*="send" i]',
        'button:has-text("Send")',
        'button:has(svg)',
    ]
    for selector in selectors:
        loc = _first_visible(page.locator(selector))
        if loc:
            try:
                if loc.is_enabled():
                    return loc
            except Exception:
                pass
    return None



def get_assistant_locator(page):
    """
    Find individual assistant-message elements.
    Never fall back to the entire page or chat transcript.
    """
    if ASSISTANT_MESSAGE_SELECTOR:
        return page.locator(ASSISTANT_MESSAGE_SELECTOR)

    selectors = [
        '[data-testid="assistant-message"]',
        '[data-role="assistant"]',
        '.assistant-message',
        '.message.assistant',
        '[data-message-role="assistant"]',
    ]

    # Prefer a selector that already identifies individual messages.
    for selector in selectors:
        locator = page.locator(selector)
        try:
            if locator.count() > 0:
                return locator
        except Exception:
            continue

    # Return a precise candidate. If it is wrong, timeout with guidance
    # rather than incorrectly returning the entire conversation.
    return page.locator(selectors[0])


def wait_for_new_assistant_response(page, assistant_locator, old_count):
    """
    Wait for a newly appended assistant message and return only its text.
    Do not return previous answers or the complete chat transcript.
    """
    deadline = time.monotonic() + CASE_TIMEOUT_MS / 1000
    previous_text = ""
    stable_since = None
    new_message_seen = False

    while time.monotonic() < deadline:
        count = assistant_locator.count()

        if count > old_count:
            new_message_seen = True

            # Read only the newest assistant message element.
            latest = assistant_locator.nth(count - 1)

            try:
                current_text = latest.inner_text(timeout=1500).strip()
            except Exception:
                page.wait_for_timeout(250)
                continue

            if current_text:
                if current_text == previous_text:
                    if stable_since is None:
                        stable_since = time.monotonic()

                    elif (
                        time.monotonic() - stable_since
                    ) * 1000 >= RESPONSE_STABLE_MS:
                        return current_text[:MAX_RESPONSE_CHARS]

                else:
                    previous_text = current_text
                    stable_since = time.monotonic()

        page.wait_for_timeout(250)

    if not new_message_seen:
        raise PlaywrightTimeoutError(
            "No new assistant message appeared. "
            "Set ASSISTANT_MESSAGE_SELECTOR to the selector "
            "for one individual assistant message."
        )

    raise PlaywrightTimeoutError(
        "A new assistant message appeared but did not stabilize "
        "before timeout. Check streaming and message selectors."
    )


def send_prompt_and_wait(page, prompt):
    """
    Send one prompt and capture only its corresponding new response.
    """
    assistant_locator = get_assistant_locator(page)

    # Record the number of assistant messages before sending.
    old_count = assistant_locator.count()

    box = find_chat_input(page)

    if box is None:
        raise RuntimeError(
            "Could not find chat input. Configure CHAT_INPUT_SELECTOR."
        )

    try:
        box.fill(prompt, timeout=5000)
    except Exception:
        box.click()
        page.keyboard.press("Control+A")
        page.keyboard.insert_text(prompt)

    send = find_send_button(page)

    if send is not None:
        send.click(timeout=5000)
    else:
        box.press("Enter", timeout=5000)

    # Wait for a new assistant message, not an old answer.
    return wait_for_new_assistant_response(
        page,
        assistant_locator,
        old_count,
    )



def response_matches(response: str, pattern: str) -> bool:
    try:
        return bool(re.search(pattern, response, flags=re.IGNORECASE | re.DOTALL))
    except re.error:
        return False


def run_case(page, case: EdgeCase) -> TestResult:
    started = time.monotonic()
    try:
        response = send_prompt_and_wait(page, case.prompt)
        matched = response_matches(response, case.expected_pattern)
        status = "PASS" if matched else "REVIEW"
        return TestResult(
            case_id=case.case_id,
            category=case.category,
            title=case.title,
            status=status,
            duration_seconds=round(time.monotonic() - started, 2),
            prompt=case.prompt,
            response=response,
            expected_pattern=case.expected_pattern,
            matched=matched,
            notes=case.notes or (
                "Response-text heuristic only; inspect database for write/state assertions."
            ),
        )
    except Exception as exc:
        return TestResult(
            case_id=case.case_id,
            category=case.category,
            title=case.title,
            status="ERROR",
            duration_seconds=round(time.monotonic() - started, 2),
            prompt=case.prompt,
            response="",
            expected_pattern=case.expected_pattern,
            matched=False,
            error=f"{type(exc).__name__}: {exc}",
            notes=traceback.format_exc(limit=3),
        )


def write_reports(results: list[TestResult]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"edge_case_results_{stamp}.json"
    csv_path = REPORT_DIR / f"edge_case_results_{stamp}.csv"

    payload = {
        "project": "Family Context Agent",
        "run_at": datetime.now().astimezone().isoformat(),
        "frontend_url": FRONTEND_URL,
        "test_family_id_configured": bool(TEST_FAMILY_ID),
        "note": (
            "PASS/REVIEW is based on response-text heuristics, not database verification. "
            "Do not use this report alone to certify persistence or authorization."
        ),
        "summary": {
            "total": len(results),
            "pass": sum(r.status == "PASS" for r in results),
            "review": sum(r.status == "REVIEW" for r in results),
            "error": sum(r.status == "ERROR" for r in results),
            "pass_percentage": round(
                100 * sum(r.status == "PASS" for r in results) / len(results), 2
            ) if results else 0,
        },
        "results": [asdict(r) for r in results],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        fields = [
            "case_id", "category", "title", "status", "duration_seconds",
            "prompt", "response", "expected_pattern", "matched", "error", "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))

    return json_path, csv_path


def main() -> int:
    if not TEST_FAMILY_ID:
        print(
            "\nWARNING: TEST_FAMILY_ID is not set. This runner does not automatically "
            "select a family or guarantee family isolation.\n"
            "Open the frontend and select a dedicated TEST family before running.\n"
            "Set TEST_FAMILY_ID if your frontend can use it to select the family.\n"
        )

    print("=" * 72)
    print("Family Context Agent - UI Edge Case Runner")
    print(f"Frontend: {FRONTEND_URL}")
    print(f"Cases: {len(CASES)}")
    print(f"Headless: {HEADLESS}")
    print("=" * 72)
    print("Safety: use a test family/database. Some prompts can still trigger writes")
    print("if your agent ignores the test-only wording. Review the selected family first.\n")

    results: list[TestResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)

        try:
            page.goto(FRONTEND_URL, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            print("Frontend opened.")
            print(
                "If login/family selection is required, complete it in the browser window "
                "now. The first test begins in 10 seconds."
            )
            if not HEADLESS:
                page.wait_for_timeout(10000)

            # Verify a chat composer exists before spending time on the suite.
            if find_chat_input(page) is None:
                print(
                    "\nERROR: Could not detect the chat input on the current page.\n"
                    "Navigate to the Chat page, then rerun; or set CHAT_INPUT_SELECTOR.\n"
                    "If the app needs login/family selection, finish that before rerunning."
                )
                return 2

            for index, case in enumerate(CASES, start=1):
                print(f"[{index:02d}/{len(CASES)}] {case.case_id} - {case.title} ... ", end="", flush=True)
                result = run_case(page, case)
                results.append(result)
                print(f"{result.status} ({result.duration_seconds:.1f}s)")
                if result.status in {"REVIEW", "ERROR"}:
                    detail = result.error or result.response.replace("\n", " ")[:180]
                    print(f"    Detail: {detail}")
                page.wait_for_timeout(int(DELAY_BETWEEN_CASES * 1000))

        except KeyboardInterrupt:
            print("\nInterrupted by user. Saving results collected so far...")
        except Exception as exc:
            print(f"\nRunner error: {type(exc).__name__}: {exc}")
        finally:
            context.close()
            browser.close()

    if results:
        json_path, csv_path = write_reports(results)
        total = len(results)
        passed = sum(r.status == "PASS" for r in results)
        review = sum(r.status == "REVIEW" for r in results)
        errors = sum(r.status == "ERROR" for r in results)
        print("\n" + "=" * 72)
        print("FINAL SUMMARY")
        print("=" * 72)
        print(f"Executed: {total}/{len(CASES)}")
        print(f"PASS (response pattern matched): {passed}")
        print(f"REVIEW (response did not match pattern): {review}")
        print(f"ERROR (browser/timeout/selector issue): {errors}")
        print(f"Response-match score: {passed / total * 100:.1f}%" if total else "Response-match score: N/A")
        print(f"JSON report: {json_path}")
        print(f"CSV report : {csv_path}")
        print("\nA PASS is not proof that the database state is correct. Inspect REVIEW/ERROR")
        print("rows and verify PostgreSQL for every test that creates or updates records.")
    else:
        print("No test results were collected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



