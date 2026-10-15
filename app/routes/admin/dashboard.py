from flask import Blueprint, render_template
from app.database import get_db_connection


dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/admin"
)


def count(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()["count"]


@dashboard.route("/")
def dashboard_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Players
        players_count = count(cursor, "SELECT COUNT(*) AS count FROM Player")
        active_players_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Player WHERE Is_Active = 1"
        )

        # Staff members
        staff_members_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Staff_Member"
        )

        # Staff members with an ongoing assignment (no End_Date)
        active_staff_members_count = count(cursor, """
            SELECT COUNT(DISTINCT Staff_Member_id) AS count
            FROM Staff_Assignment
            WHERE End_Date IS NULL
        """)

        # Clubs
        clubs_count = count(cursor, "SELECT COUNT(*) AS count FROM Club")
        active_clubs_count = count(
            cursor,
            "SELECT COUNT(*) AS count FROM Club WHERE Club_Status = 'Active'"
        )

        # Player clubs
        player_clubs_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Player_Club"
        )
        current_player_clubs_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Player_Club WHERE Is_Actual = 1"
        )

        # Staff assignments
        staff_assignments_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Staff_Assignment"
        )
        current_staff_assignments_count = count(
            cursor,
            "SELECT COUNT(*) AS count FROM Staff_Assignment WHERE End_Date IS NULL"
        )

        # Player seasons
        player_seasons_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Player_Season"
        )

        # Assignment-season links
        staff_assignment_seasons_count = count(
            cursor, "SELECT COUNT(*) AS count FROM Staff_Assignment_Season"
        )

        # Cities
        cities_count = count(cursor, "SELECT COUNT(*) AS count FROM City")

        # USMA squad size (latest season)
        usma_squad_count = count(cursor, """
            SELECT COUNT(*) AS count
            FROM Player_Season ps
            WHERE ps.Club_id = 1
              AND ps.Season_Number = (SELECT MAX(Season_Number) FROM Season)
        """)

        # USMA staff size (latest season): distinct people linked to it
        usma_staff_count = count(cursor, """
            SELECT COUNT(DISTINCT sa.Staff_Member_id) AS count
            FROM Staff_Assignment sa
            JOIN Staff_Assignment_Season sas
                ON sas.Assignment_id = sa.Assignment_id
            WHERE sa.Club_id = 1
              AND sas.Season_Number = (SELECT MAX(Season_Number) FROM Season)
        """)

        return render_template(
            "admin/dashboard.html",
            Title="Admin Dashboard",

            players_count=players_count,
            active_players_count=active_players_count,
            staff_members_count=staff_members_count,
            active_staff_members_count=active_staff_members_count,
            clubs_count=clubs_count,
            active_clubs_count=active_clubs_count,
            player_clubs_count=player_clubs_count,
            current_player_clubs_count=current_player_clubs_count,
            staff_assignments_count=staff_assignments_count,
            current_staff_assignments_count=current_staff_assignments_count,
            player_seasons_count=player_seasons_count,
            staff_assignment_seasons_count=staff_assignment_seasons_count,
            cities_count=cities_count,
            usma_squad_count=usma_squad_count,
            usma_staff_count=usma_staff_count
        )

    except Exception as error:

        return f"Error: {error}", 500

    finally:

        cursor.close()
        connection.close()