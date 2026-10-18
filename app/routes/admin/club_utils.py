from app.utils import parse_date


def read_club_spell(form):
    """Validate a player's club period from a form.

    Returns (club_id, join_date, leave_date, is_actual).
    Raises ValueError with a fixed message if invalid.
    """
    club_id = form.get("club_id", type=int)
    if club_id is None:
        raise ValueError("Please select a club")

    join_date = parse_date(form.get("join_date"))
    leave_date = parse_date(form.get("leave_date"))

    if join_date is None:
        raise ValueError("Join date is required")

    if leave_date and leave_date < join_date:
        raise ValueError("Leave date cannot be before join date")

    is_actual = 1 if form.get("is_actual") else 0

    # The current club must not have a leave date
    if is_actual:
        leave_date = None

    return club_id, join_date, leave_date, is_actual


def get_club_record(cursor, player_id, club_id, join_date):
    """Return the Player_Club row (Is_Actual only), or None."""
    cursor.execute("""
        SELECT Is_Actual
        FROM Player_Club
        WHERE Player_id = %s
          AND Club_id = %s
          AND Join_Date = %s
    """, (player_id, club_id, join_date))
    return cursor.fetchone()


def clear_current_club(cursor, player_id):
    """Remove the 'current club' flag from all the player's spells."""
    cursor.execute("""
        UPDATE Player_Club
        SET Is_Actual = 0
        WHERE Player_id = %s
    """, (player_id,))


def insert_club_spell(cursor, player_id, club_id,
                      join_date, leave_date, is_actual):
    if is_actual:
        clear_current_club(cursor, player_id)

    cursor.execute("""
        INSERT INTO Player_Club (
            Player_id, Club_id, Join_Date, Leave_Date, Is_Actual
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (player_id, club_id, join_date, leave_date, is_actual))


def update_club_spell(cursor, player_id, original_club_id, original_join_date,
                      club_id, join_date, leave_date, is_actual):
    # Check BEFORE clearing the current flag, so a wrong key never
    # leaves the player without a current club
    if get_club_record(cursor, player_id, original_club_id,
                       original_join_date) is None:
        raise ValueError("Club record not found")

    if is_actual:
        clear_current_club(cursor, player_id)

    cursor.execute("""
        UPDATE Player_Club
        SET
            Club_id = %s,
            Join_Date = %s,
            Leave_Date = %s,
            Is_Actual = %s
        WHERE Player_id = %s
          AND Club_id = %s
          AND Join_Date = %s
    """, (
        club_id, join_date, leave_date, is_actual,
        player_id, original_club_id, original_join_date
    ))