from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from mysql.connector import IntegrityError

from app.constants import USMA_CLUB_ID
from app.database import get_db_connection
from app.routes.admin.club_utils import insert_club_spell, read_club_spell
from app.utils import escape_like, parse_date

player_club = Blueprint("player_club", __name__)


@player_club.route("/player-club", methods=["GET", "POST"])
def player_club_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # ========================================
        # POST
        # ========================================

        if request.method == "POST":
            player_id = request.form.get("player_id", type=int)

            if player_id is None:
                return "Please select a player", 400

            try:
                # Validates club, dates and the "current club" flag
                club_id, join_date, leave_date, is_actual = read_club_spell(
                    request.form
                )

                # Clears the player's other current club when needed
                insert_club_spell(
                    cursor, player_id, club_id,
                    join_date, leave_date, is_actual
                )
                connection.commit()

            except ValueError as error:
                connection.rollback()
                return str(error), 400

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate entry
                    return "This record already exists", 400
                if error.errno == 1452:      # foreign key failure
                    return "Invalid player or club", 400
                raise

            return redirect(url_for("player_club.player_club_page"))

        # ========================================
        # GET
        # ========================================

        search_player = request.args.get("search_player", "").strip()
        search_club = request.args.get("search_club", "").strip()
        status_filter = request.args.get("status_filter", "").strip()

        # Last added player (pre-selected in the form)
        cursor.execute("""
            SELECT Player_id
            FROM Player
            ORDER BY Player_id DESC
            LIMIT 1
        """)
        last_player = cursor.fetchone()
        last_player_id = last_player["Player_id"] if last_player else None

        cursor.execute("""
            SELECT
                pl.Player_id,
                p.Person_Display_Name
            FROM Player pl
            JOIN Person p ON pl.Person_id = p.Person_id
            ORDER BY p.Person_Display_Name
        """)
        players = cursor.fetchall()

        cursor.execute("""
            SELECT Club_id, Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)
        clubs = cursor.fetchall()

        # Only fixed SQL fragments are added here; values go in params
        conditions = []
        params = []

        if search_player:
            conditions.append("p.Person_Display_Name LIKE %s")
            params.append(f"%{escape_like(search_player)}%")

        if search_club:
            conditions.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{escape_like(search_club)}%")

        if status_filter == "active":
            conditions.append("pc.Is_Actual = 1")
        elif status_filter == "inactive":
            conditions.append("pc.Is_Actual = 0")

        query = """
            SELECT
                pc.Player_id,
                pc.Club_id,
                pc.Join_Date,
                pc.Leave_Date,
                pc.Is_Actual,
                p.Person_Display_Name,
                c.Club_Current_Name
            FROM Player_Club pc

            JOIN Player pl
                ON pc.Player_id = pl.Player_id

            JOIN Person p
                ON pl.Person_id = p.Person_id

            JOIN Club c
                ON pc.Club_id = c.Club_id
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY pc.Is_Actual DESC, pc.Join_Date DESC"

        cursor.execute(query, params)
        player_clubs = cursor.fetchall()

        return render_template(
            "admin/player_club/player_club.html",
            Title="Player Club Management",
            players=players,
            clubs=clubs,
            player_clubs=player_clubs,
            last_player_id=last_player_id,
            usma_club_id=USMA_CLUB_ID,
            search_player=search_player,
            search_club=search_club,
            status_filter=status_filter
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in player club page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


@player_club.route(
    "/player-club/delete/<int:player_id>/<int:club_id>/<join_date>",
    methods=["POST"]
)
def delete_player_club(player_id, club_id, join_date):
    try:
        join_date = parse_date(join_date)
    except ValueError as error:
        return str(error), 400

    if join_date is None:
        return "Invalid join date", 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            DELETE FROM Player_Club
            WHERE Player_id = %s
              AND Club_id = %s
              AND Join_Date = %s
        """, (player_id, club_id, join_date))

        if cursor.rowcount == 0:
            connection.rollback()
            return "Record not found", 404

        connection.commit()
        return redirect(url_for("player_club.player_club_page"))

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting player club record")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()