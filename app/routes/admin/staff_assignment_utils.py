from datetime import datetime


def parse_date(value):
    """Accepts DD/MM/YYYY or YYYY-MM-DD. Returns a date or None."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date: {value}")


def has_overlap(cursor, staff_member_id, club_id, role_id,
                start_date, end_date, exclude_id=None):
    """True if the same person/club/role already has an overlapping period."""
    query = """
        SELECT 1
        FROM Staff_Assignment
        WHERE Staff_Member_id = %s
          AND Club_id = %s
          AND Role_id = %s
          AND Start_Date <= COALESCE(%s, '9999-12-31')
          AND COALESCE(End_Date, '9999-12-31') >= %s
    """
    params = [staff_member_id, club_id, role_id, end_date, start_date]

    if exclude_id is not None:
        query += " AND Assignment_id <> %s"
        params.append(exclude_id)

    query += " LIMIT 1"
    cursor.execute(query, params)
    return cursor.fetchone() is not None


def clean_season_ids(cursor, raw_ids):
    """Keeps only season numbers that really exist in the Season table."""
    ids = {int(x) for x in raw_ids if str(x).isdigit()}
    if not ids:
        return []
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"SELECT Season_Number FROM Season WHERE Season_Number IN ({placeholders})",
        tuple(ids)
    )
    return [row["Season_Number"] for row in cursor.fetchall()]

def valid_role_ids(cursor, raw_ids):
    """Keeps only role ids that really exist in Staff_Role."""
    ids = {int(x) for x in raw_ids if str(x).isdigit()}
    if not ids:
        return set()
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"SELECT Role_id FROM Staff_Role WHERE Role_id IN ({placeholders})",
        tuple(ids)
    )
    return {row["Role_id"] for row in cursor.fetchall()}