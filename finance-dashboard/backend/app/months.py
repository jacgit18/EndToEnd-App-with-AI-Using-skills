"""Month strings (YYYY-MM) shared by the transactions, budgets and dashboard APIs."""

from datetime import date

# YYYY-MM with a real month (01-12). ASCII digits only ([0-9], not \d, which also
# matches other scripts' digits), and no year 0000 (Python's date can't hold it).
MONTH_PATTERN = r"^[1-9][0-9]{3}-(0[1-9]|1[0-2])$"


def month_range(month: str) -> tuple[date, date | None]:
    """[first of month, first of next month). The upper bound is exclusive, so the
    last day of the month is in and the 1st of the next is out whatever the month's
    length. None for 9999-12, which has no next month a `date` can hold."""
    year, mon = int(month[:4]), int(month[5:])
    start = date(year, mon, 1)
    if mon == 12:
        return start, (date(year + 1, 1, 1) if year < 9999 else None)
    return start, date(year, mon + 1, 1)
