"""Timezone-aware date helpers."""

import calendar
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


_MONTH_NAMES = "|".join(
    sorted(
        {name.casefold() for name in calendar.month_name[1:]}
        | {name.casefold() for name in calendar.month_abbr[1:]},
        key=len,
        reverse=True,
    )
)
_DAY_NUMBER = r"\d{1,2}(?:st|nd|rd|th)?"
_YEAR = r"(?:,?\s+\d{4})?"
_NATURAL_DATE = (
    rf"(?:{_DAY_NUMBER}\s+(?:{_MONTH_NAMES}){_YEAR}|"
    rf"(?:{_MONTH_NAMES})\s+{_DAY_NUMBER}{_YEAR})"
)
_NUMERIC_DATE = r"(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})"
_EXPLICIT_DATE_RE = re.compile(
    rf"(?<!\w)(?:{_NUMERIC_DATE}|{_NATURAL_DATE})(?!\w)", re.IGNORECASE
)
_RELATIVE_BASE_RE = re.compile(
    rf"(?P<count>-?\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    rf"days?\s+(?P<direction>after|before)\s+(?P<base>{_NUMERIC_DATE}|{_NATURAL_DATE})",
    re.IGNORECASE,
)
_COUNT = r"-?\d+|one|two|three|four|five|six|seven|eight|nine|ten"
_RELATIVE_AMOUNT_RE = re.compile(
    rf"(?:(?:in\s+(?P<in_count>{_COUNT})\s+(?P<in_unit>days?|weeks?))|"
    rf"(?:after\s+(?P<after_count>{_COUNT})\s+(?P<after_unit>days?|weeks?))|"
    rf"(?:(?P<from_count>{_COUNT})\s+(?P<from_unit>days?|weeks?)\s+from\s+(?:now|today))|"
    rf"(?:(?P<past_count>{_COUNT})\s+(?P<past_unit>days?|weeks?)\s+(?:ago|back)))",
    re.IGNORECASE,
)
_COMPOUND_RELATIVE_RE = re.compile(
    r"\bthe\s+day\s+(before\s+yesterday|after\s+tomorrow)\b",
    re.IGNORECASE,
)
_RELATIVE_WORD_RE = re.compile(r"\b(today|yesterday|tomorrow|last\s+week|next\s+week)\b", re.IGNORECASE)
_UNSUPPORTED_RELATIVE_RE = re.compile(
    r"\b(?:last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|month)|"
    r"next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|month)|"
    r"end\s+of\s+(?:the\s+)?(?:month|week)|"
    r"a\s+couple\s+of\s+days\s+ago|"
    r"a\s+few\s+days\s+ago|"
    r"\d+\s+days?\s+(?:ago|back)|"
    r"\d+\s+weeks?\s+(?:ago|back)|"
    r"(?:in|after)\s+-\d+\s+(?:days?|weeks?))\b",
    re.IGNORECASE,
)
_MALFORMED_NUMERIC_DATE_RE = re.compile(r"(?<!\d)\d{1,4}[/-]\d{1,2}[/-]\d{1,4}(?!\d)")
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def today_in(timezone: str) -> date:
    """Return today's date in the family's timezone, not the server's."""

    return datetime.now(ZoneInfo(timezone)).date()


def _parse_count(value: str) -> int:
    count = _NUMBER_WORDS.get(value.casefold())
    if count is None:
        count = int(value)
    if count <= 0:
        raise ValueError("Relative date offsets must be positive.")
    return count


def _parse_explicit_date(value: str, reference_date: date) -> date:
    candidate = value.strip().rstrip(",")
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(candidate, date_format).date()
        except ValueError:
            pass

    natural = re.fullmatch(
        rf"(?:(?P<day>{_DAY_NUMBER})\s+(?P<month>{_MONTH_NAMES})(?:\s+(?P<year>\d{{4}}))?|"
        rf"(?P<month2>{_MONTH_NAMES})\s+(?P<day2>{_DAY_NUMBER})(?:,?\s+(?P<year2>\d{{4}}))?)",
        candidate,
        re.IGNORECASE,
    )
    if natural:
        day_text = natural.group("day") or natural.group("day2")
        month_text = natural.group("month") or natural.group("month2")
        year_text = natural.group("year") or natural.group("year2")
        day = int(re.sub(r"(?:st|nd|rd|th)$", "", day_text, flags=re.IGNORECASE))
        month = next(
            number
            for number in range(1, 13)
            if calendar.month_name[number].casefold().startswith(month_text.casefold())
            or calendar.month_abbr[number].casefold() == month_text.casefold()
        )
        # For month/day wording without a year, use the current family-local year.
        year = int(year_text) if year_text else reference_date.year
        try:
            return date(year, month, day)
        except ValueError as exc:
            raise ValueError(f"Invalid expense date: {candidate}") from exc

    raise ValueError(f"Invalid or unsupported expense date: {candidate}")


def resolve_expense_date(
    user_message: str,
    timezone: str,
    *,
    today: date | None = None,
) -> date:
    """Resolve supported expense dates from user text and family-local today.

    Month/day phrases without a year use the family-local current year. Relative
    week offsets mean fixed seven-day intervals. Unsupported or conflicting
    expressions raise ``ValueError`` rather than silently choosing a date.
    ``today`` is exposed for deterministic tests; production callers omit it.
    """

    reference_date = today if today is not None else today_in(timezone)
    matches: list[tuple[tuple[int, int], date]] = []
    consumed_spans: list[tuple[int, int]] = []

    for match in _RELATIVE_BASE_RE.finditer(user_message):
        count = _parse_count(match.group("count"))
        base = _parse_explicit_date(match.group("base"), reference_date)
        offset = count if match.group("direction").casefold() == "after" else -count
        matches.append((match.span(), base + timedelta(days=offset)))
        consumed_spans.append(match.span("base"))

    for match in _RELATIVE_AMOUNT_RE.finditer(user_message):
        count_name = next(name for name in ("in_count", "after_count", "from_count", "past_count") if match.group(name) is not None)
        unit_name = next(name for name in ("in_unit", "after_unit", "from_unit", "past_unit") if match.group(name) is not None)
        count = _parse_count(match.group(count_name))
        unit = match.group(unit_name).casefold()
        is_past = count_name == "past_count"
        offset = count * (7 if unit.startswith("week") else 1)
        if is_past:
            offset = -offset
        matches.append((match.span(), reference_date + timedelta(days=offset)))
        consumed_spans.append(match.span())

    for match in _COMPOUND_RELATIVE_RE.finditer(user_message):
        offset = -2 if match.group(1).casefold().startswith("before") else 2
        matches.append((match.span(), reference_date + timedelta(days=offset)))
        consumed_spans.append(match.span())

    for match in _RELATIVE_WORD_RE.finditer(user_message):
        if any(start <= match.start() and match.end() <= end for start, end in consumed_spans):
            continue
        expression = re.sub(r"\s+", " ", match.group().casefold())
        offsets = {"today": 0, "yesterday": -1, "tomorrow": 1, "last week": -7, "next week": 7}
        matches.append((match.span(), reference_date + timedelta(days=offsets[expression])))
        consumed_spans.append(match.span())

    for match in _EXPLICIT_DATE_RE.finditer(user_message):
        if any(start <= match.start() and match.end() <= end for start, end in consumed_spans):
            continue
        parsed = _parse_explicit_date(match.group(), reference_date)
        matches.append((match.span(), parsed))

    for match in _MALFORMED_NUMERIC_DATE_RE.finditer(user_message):
        if not any(start <= match.start() and match.end() <= end for start, end in consumed_spans):
            if not any(span[0] <= match.start() and match.end() <= span[1] for span, _ in matches):
                raise ValueError(f"Malformed expense date: {match.group()}")

    if _UNSUPPORTED_RELATIVE_RE.search(user_message):
        # Recognized relative expressions have already been consumed; this
        # catches unsupported expressions such as "a couple of days ago".
        unsupported = _UNSUPPORTED_RELATIVE_RE.search(user_message)
        if unsupported and not any(start <= unsupported.start() and unsupported.end() <= end for start, end in consumed_spans):
            raise ValueError("Unsupported relative expense date expression.")

    resolved = {value for _, value in matches}
    if len(resolved) > 1:
        raise ValueError("Conflicting expense dates were provided.")
    if resolved:
        return next(iter(resolved))
    return reference_date


def describe_due(due_date: date, today: date) -> str:
    """Human-readable distance to a due date, e.g. 'due tomorrow', 'overdue by 3 days'."""

    days = (due_date - today).days
    if days < 0:
        overdue = -days
        return f"overdue by {overdue} day{'s' if overdue != 1 else ''}"
    if days == 0:
        return "due today"
    if days == 1:
        return "due tomorrow"
    return f"due in {days} days"
