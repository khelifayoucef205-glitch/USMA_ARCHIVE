from flask import Blueprint, current_app, render_template

from app.constants import USMA_CLUB_ID
from app.database import get_db_connection

dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/admin"
)

# Same definition of "latest season" as the squad page
LATEST_SEASON = """(
    SELECT Season_Number
    FROM Season
    ORDER BY Start_Year DESC, Season_Number DESC
    LIMIT 1
)"""

STATS_QUERY = f"""
    SELECT
        (SELECT COUNT(*) FROM Player) AS players_count,
        (SELECT COUNT(*) FROM Player WHERE Is_Active = 1)
            AS active_players_count,

        (SELECT COUNT(*) FROM Staff_Member) AS staff_members_count,
        -- staff members with an ongoing assignment (no End_Date)
        (SELECT COUNT(DISTINCT Staff_Member_id)
            FROM Staff_Assignment WHERE End_Date IS NULL)
            AS active_staff_members_count,

        (SELECT COUNT(*) FROM Club) AS clubs_count,
        (SELECT COUNT(*) FROM Club WHERE Club_Status = 'Active')
            AS active_clubs_count,

        (SELECT COUNT(*) FROM Player_Club) AS player_clubs_count,
        (SELECT COUNT(*) FROM Player_Club WHERE Is_Actual = 1)
            AS current_player_clubs_count,

        (SELECT COUNT(*) FROM Staff_Assignment) AS staff_assignments_count,
        (SELECT COUNT(*) FROM Staff_Assignment WHERE End_Date IS NULL)
            AS current_staff_assignments_count,

        (SELECT COUNT(*) FROM Player_Season) AS player_seasons_count,
        (SELECT COUNT(*) FROM Staff_Assignment_Season)
            AS staff_assignment_seasons_count,

        (SELECT COUNT(*) FROM City) AS cities_count,

        -- USMA squad size (latest season)
        (SELECT COUNT(*)
            FROM Player_Season
            WHERE Club_id = %s
              AND Season_Number = {LATEST_SEASON})
            AS usma_squad_count,

        -- USMA staff size (latest season): distinct people linked to it
        (SELECT COUNT(DISTINCT sa.Staff_Member_id)
            FROM Staff_Assignment sa
            JOIN Staff_Assignment_Season sas
                ON sas.Assignment_id = sa.Assignment_id
            WHERE sa.Club_id = %s
              AND sas.Season_Number = {LATEST_SEASON})
            AS usma_staff_count
"""


@dashboard.route("/")
def dashboard_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(STATS_QUERY, (USMA_CLUB_ID, USMA_CLUB_ID))
        stats = cursor.fetchone()

        return render_template(
            "admin/dashboard.html",
            Title="Admin Dashboard",
            **stats
        )

    except Exception:
        current_app.logger.exception("Error while loading dashboard")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()