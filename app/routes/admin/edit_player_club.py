from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from mysql.connector import IntegrityError

from app.database import get_db_connection
from app.utils import parse_date
from app.routes.admin.club_utils import read_club_spell, update_club_spell


edit_player_club = Blueprint(
    "edit_player_club",
    __name__,
    url_prefix="/admin/player-club"
)


@edit_player_club.route(
    "/<int:player_id>/<int:club_id>/<join_date>/edit",
    methods=["GET", "POST"]
)
def edit_player_club_page(player_id, club_id, join_date):
    try:
        old_join_date = parse_date(join_date)
    except ValueError as error:
        return str(error), 400

    if old_join_date is None:
        return "Invalid join date", 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Load the record first, for both GET and POST
        cursor.execute("""
            SELECT
                pc.Player_id,
                pc.Club_id,
                pc.Join_Date,
                pc.Leave_Date,
                pc.Is_Actual,
                pe.Person_Display_Name,
                c.Club_Current_Name

            FROM Player_Club pc

            JOIN Player p
                ON pc.Player_id = p.Player_id

            JOIN Person pe
                ON p.Person_id = pe.Person_id

            JOIN Club c
                ON pc.Club_id = c.Club_id

            WHERE pc.Player_id = %s
              AND pc.Club_id = %s
              AND pc.Join_Date = %s
        """, (player_id, club_id, old_join_date))

        relationship = cursor.fetchone()

        if relationship is None:
            return "Player-club relationship not found", 404

        # =================================================
        # POST - Update
        # =================================================

        if request.method == "POST":
            try:
                new_club_id, new_join_date, leave_date, is_actual = (
                    read_club_spell(request.form)
                )
                update_club_spell(
                    cursor, player_id,
                    club_id, old_join_date,
                    new_club_id, new_join_date, leave_date, is_actual
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
                    return "Invalid club", 400
                raise

            return redirect(url_for("player_club.player_club_page"))

        # =================================================
        # GET
        # =================================================

        cursor.execute("""
            SELECT
                p.Player_id,
                pe.Person_Display_Name
            FROM Player p

            JOIN Person pe
                ON p.Person_id = pe.Person_id

            ORDER BY pe.Person_Display_Name
        """)
        players = cursor.fetchall()

        cursor.execute("""
            SELECT Club_id, Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)
        clubs = cursor.fetchall()

        return render_template(
            "admin/player_club/edit_player_club.html",
            Title="Edit Player Club",
            relationship=relationship,
            players=players,
            clubs=clubs
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while editing player club")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()