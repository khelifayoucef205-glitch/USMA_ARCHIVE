from flask import Blueprint, render_template
from app.database import get_db_connection


dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/admin"
)


@dashboard.route("/")
def dashboard_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =========================
        # Players Count
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player
        """)

        players_count = cursor.fetchone()["count"]

        # Active Players
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player
            WHERE Is_Active = 1
        """)

        active_players_count = cursor.fetchone()["count"]


        # =========================
        # Clubs Count
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Club
        """)

        clubs_count = cursor.fetchone()["count"]

        # Active Clubs
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Club
            WHERE Club_Status = 'Active'
        """)

        active_clubs_count = cursor.fetchone()["count"]


        # =========================
        # Player Clubs Count
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Club
        """)

        player_clubs_count = cursor.fetchone()["count"]

        # Current Player Clubs
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Club
            WHERE Is_Actual = 1
        """)

        current_player_clubs_count = cursor.fetchone()["count"]


        # =========================
        # Player Seasons Count
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Season
        """)

        player_seasons_count = cursor.fetchone()["count"]


        # =========================
        # Cities Count
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM City
        """)

        cities_count = cursor.fetchone()["count"]

        # =========================
        # USMA Squad Size (Current Season)
        # =========================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Season ps
            WHERE ps.Club_id = 1
            AND ps.Season_Number = (
                SELECT MAX(Season_Number) FROM Season
            )
        """)

        usma_squad_count = cursor.fetchone()["count"]


        return render_template(
            "admin/dashboard.html",
            Title="Admin Dashboard",

            players_count=players_count,
            active_players_count=active_players_count,
            clubs_count=clubs_count,
            active_clubs_count=active_clubs_count,
            player_clubs_count=player_clubs_count,
            current_player_clubs_count=current_player_clubs_count,
            player_seasons_count=player_seasons_count,
            cities_count=cities_count,
            usma_squad_count=usma_squad_count
        )

    except Exception as error:

        return f"Error: {error}", 500

    finally:

        cursor.close()
        connection.close()