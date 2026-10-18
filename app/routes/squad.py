from flask import Blueprint, render_template, request

from app.constants import USMA_CLUB_ID
from app.database import get_db_connection
from app.utils import calculate_age, season_reference_date, to_date

squad = Blueprint("squad", __name__)

VALID_SORTS = ("position", "jersey", "age", "name")


# =====================================================
# QUERIES
# =====================================================

def get_seasons(cursor):
    """All seasons, latest first."""
    cursor.execute("""
        SELECT
            Season_Number,
            Season_Name,
            Start_Year,
            End_Year
        FROM Season
        ORDER BY Start_Year DESC
    """)
    return cursor.fetchall()


def get_squad(cursor, season_number):
    """USMA players for a season."""
    cursor.execute("""
        SELECT
            ps.Player_id,
            pe.Person_Display_Name,
            pe.Person_Display_Name_ar,
            pe.Person_birth_date,
            c.Club_Current_Name,
            p.Position_id,
            p.Position_Code,
            p.Position_Name,
            p.Position_Category_id,
            pc.Category_Name,
            pc.Category_Name_ar,
            co.Country_Name,
            co.Country_Name_ar,
            co.ISO_Alpha2,
            ps.Jersey_Number
        FROM Player_Season ps

        JOIN Player pl
            ON ps.Player_id = pl.Player_id

        JOIN Person pe
            ON pl.Person_id = pe.Person_id

        JOIN Club c
            ON ps.Club_id = c.Club_id

        JOIN Position p
            ON ps.Position_id = p.Position_id

        JOIN Position_Category pc
            ON p.Position_Category_id = pc.Position_Category_id

        LEFT JOIN Country co
            ON pe.Country_id = co.Country_id

        WHERE ps.Club_id = %s
          AND ps.Season_Number = %s

        ORDER BY
            p.Position_Category_id,
            p.Position_id,
            ps.Jersey_Number
    """, (USMA_CLUB_ID, season_number))
    return cursor.fetchall()


def get_staff(cursor, season_number):
    """USMA staff for a season."""
    cursor.execute("""
        SELECT
            sa.Assignment_id,
            sa.Staff_Member_id,
            p.Person_Display_Name,
            co.Country_Name,
            sr.Role_name,
            sa.Start_Date,
            sa.End_Date

        FROM Staff_Assignment sa

        JOIN Staff_Assignment_Season sas
            ON sas.Assignment_id = sa.Assignment_id

        JOIN Staff_Member sm
            ON sa.Staff_Member_id = sm.Staff_Member_id

        JOIN Person p
            ON sm.Person_id = p.Person_id

        LEFT JOIN Country co
            ON p.Country_id = co.Country_id

        JOIN Staff_Role sr
            ON sa.Role_id = sr.Role_id

        WHERE sa.Club_id = %s
          AND sas.Season_Number = %s

        ORDER BY sa.Start_Date, sr.Role_id
    """, (USMA_CLUB_ID, season_number))
    return cursor.fetchall()


def get_titles(cursor, season_number):
    """Titles won by USMA in a season."""
    cursor.execute("""
        SELECT
            c.Competition_id,
            c.Competition_Name,
            c.Competition_Name_ar,
            c.Competition_Type
        FROM Competition_Season cs

        JOIN Competition c
            ON cs.Competition_id = c.Competition_id

        WHERE cs.Competition_Winner_Club_id = %s
          AND cs.Season_Number = %s

        ORDER BY c.Competition_id
    """, (USMA_CLUB_ID, season_number))
    return cursor.fetchall()


# =====================================================
# HELPERS
# =====================================================

def pick_season(seasons, requested_number):
    """Return the requested season, or the latest one if missing/invalid."""
    for season in seasons:
        if season["Season_Number"] == requested_number:
            return season
    return seasons[0] if seasons else None


def sort_players(players, sort_by, descending):
    """Sort players. Unknown values (jersey / birth date) always go last."""
    if sort_by == "jersey":
        known = [p for p in players if p["Jersey_Number"] is not None]
        unknown = [p for p in players if p["Jersey_Number"] is None]
        known.sort(key=lambda p: p["Jersey_Number"], reverse=descending)
        return known + unknown

    if sort_by == "age":
        known = [p for p in players if p["Person_birth_date"]]
        unknown = [p for p in players if not p["Person_birth_date"]]
        # Youngest first (ascending age) = latest birth date first
        known.sort(
            key=lambda p: to_date(p["Person_birth_date"]),
            reverse=not descending
        )
        return known + unknown

    if sort_by == "name":
        players.sort(
            key=lambda p: (p["Person_Display_Name"] or "").casefold(),
            reverse=descending
        )
        return players

    # position (default). The sort is stable, so players in the same
    # position keep the query order (jersey number ascending).
    players.sort(
        key=lambda p: (p["Position_Category_id"], p["Position_id"]),
        reverse=descending
    )
    return players


def compute_stats(players):
    """Return (position_stats, total_players, avg_age_total)."""
    position_stats = {}

    for p in players:
        stats = position_stats.setdefault(p["Position_Category_id"], {
            "category_name": p["Category_Name"],
            "count": 0,
            "known_age_count": 0,
            "total_age": 0,
            "avg_age": 0
        })

        stats["count"] += 1
        if p["Age"] is not None:
            stats["known_age_count"] += 1
            stats["total_age"] += p["Age"]

    for stats in position_stats.values():
        if stats["known_age_count"] > 0:
            stats["avg_age"] = round(
                stats["total_age"] / stats["known_age_count"], 1
            )

    total_known = sum(s["known_age_count"] for s in position_stats.values())
    total_age = sum(s["total_age"] for s in position_stats.values())
    avg_age_total = round(total_age / total_known, 1) if total_known else 0

    return dict(sorted(position_stats.items())), len(players), avg_age_total


# =====================================================
# ROUTE
# =====================================================

@squad.route("/squad")
def squad_page():
    # Sorting parameters (validated)
    sort_by = request.args.get("sort_by", "position")
    if sort_by not in VALID_SORTS:
        sort_by = "position"

    sort_order = request.args.get("sort_order", "asc").lower()
    if sort_order not in ("asc", "desc"):
        sort_order = "asc"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        seasons = get_seasons(cursor)

        # type=int returns None for a missing or invalid value
        season_details = pick_season(
            seasons, request.args.get("season", type=int)
        )

        if season_details:
            season_number = season_details["Season_Number"]
            players = get_squad(cursor, season_number)
            staff = get_staff(cursor, season_number)
            titles = get_titles(cursor, season_number)
        else:
            season_number = None
            players, staff, titles = [], [], []

    finally:
        cursor.close()
        connection.close()

    # Age is computed at 1 July of the season's start year
    if season_details:
        reference_date = season_reference_date(season_details["Start_Year"])
        for p in players:
            p["Age"] = calculate_age(p["Person_birth_date"], reference_date)

    players = sort_players(players, sort_by, descending=(sort_order == "desc"))
    position_stats, total_players, avg_age_total = compute_stats(players)

    return render_template(
        "squad.html",
        Title="Squad",
        seasons=seasons,
        players=players,
        staff=staff,
        titles=titles,
        selected_season=season_number,
        sort_by=sort_by,
        sort_order=sort_order,
        position_stats=position_stats,
        total_players=total_players,
        avg_age_total=avg_age_total
    )