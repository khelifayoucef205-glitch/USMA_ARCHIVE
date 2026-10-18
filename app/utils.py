from datetime import date, datetime

DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


# =====================================================
# DATES
# =====================================================

def to_date(value):
    """Convert a date, datetime or ISO string (YYYY-MM-DD) to a date.

    For values read from the database, not for user input.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_date(value):
    """Accepts DD/MM/YYYY or YYYY-MM-DD. Returns a date or None.

    Raises ValueError with a fixed message: the user's input is never
    echoed back, since error messages are returned to the browser.
    """
    if not value or not value.strip():
        return None

    value = value.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError("Invalid date, expected DD/MM/YYYY or YYYY-MM-DD")


def calculate_age(birth_date, reference_date=None):
    """Age in full years at reference_date (today if omitted).

    Pass the death date as reference_date for deceased people.
    Returns None if the birth date is missing or after the reference date.
    """
    birth_date = to_date(birth_date)
    if birth_date is None:
        return None

    reference_date = to_date(reference_date) or date.today()
    age = reference_date.year - birth_date.year

    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age if age >= 0 else None


def season_reference_date(start_year):
    """Date used to compute players' ages for a season (1 July)."""
    return date(start_year, 7, 1)


# =====================================================
# FORM VALUES
# =====================================================

def clean_text(value):
    """Strip a text value; an empty value becomes None."""
    return (value or "").strip() or None


def parse_int(value, label, minimum=None):
    """Return an int, or None if the value is empty.

    Raises ValueError with a fixed message (the input is never echoed).
    """
    if value is None or str(value).strip() == "":
        return None

    try:
        number = int(value)
    except ValueError:
        raise ValueError(f"{label} must be a number")

    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be at least {minimum}")

    return number


# =====================================================
# SEARCH
# =====================================================

def escape_like(text):
    """Escape LIKE wildcards so the search text is matched literally."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")