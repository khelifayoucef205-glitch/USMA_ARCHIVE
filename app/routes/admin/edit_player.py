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
from app.routes.admin.person_utils import update_person
from app.utils import parse_date, parse_int, clean_text
from app.routes.admin.club_utils import (
    clear_current_club,
    get_club_record,
    insert_club_spell,
    read_club_spell,
    update_club_spell,
)

edit_player = Blueprint("edit_player", __name__)


# =====================================================
# POSITION HELPERS
# =====================================================

def set_main_position(cursor, player_id, position_id):
    cursor.execute("""
        UPDATE Player_Position
        SET Is_Main = 0
        WHERE Player_id = %s
    """, (player_id,))

    cursor.execute("""
        INSERT INTO Player_Position (Player_id, Position_id, Is_Main)
        VALUES (%s, %s, 1)
        ON DUPLICATE KEY UPDATE Is_Main = 1
    """, (player_id, position_id))


def player_has_position(cursor, player_id, position_id):
    cursor.execute("""
        SELECT Is_Main
        FROM Player_Position
        WHERE Player_id = %s
          AND Position_id = %s
    """, (player_id, position_id))
    return cursor.fetchone()

# =====================================================
# ACTIONS (each one runs inside the route's transaction)
# =====================================================

def do_update_person(cursor, player, form):
    update_person(cursor, player["Person_id"], form)


def do_update_player(cursor, player, form):
    player_id = player["Player_id"]

    jersey_number = parse_int(form.get("jersey_number"), "Jersey number", minimum=0)
    position_id = form.get("position_id", type=int)

    cursor.execute("""
        UPDATE Player
        SET
            Player_Nickname = %s,
            Player_Nickname_ar = %s,
            Main_Jersey_Number = %s,
            Is_Active = %s
        WHERE Player_id = %s
    """, (
        clean_text(form.get("nickname")),
        clean_text(form.get("nickname_ar")),
        jersey_number,
        1 if form.get("is_active") else 0,
        player_id
    ))

    if position_id is not None:
        set_main_position(cursor, player_id, position_id)


def do_add_position(cursor, player, form):
    player_id = player["Player_id"]

    position_id = form.get("new_position_id", type=int)
    if position_id is None:
        raise ValueError("Please select a position")

    if player_has_position(cursor, player_id, position_id) is None:
        cursor.execute("""
            INSERT INTO Player_Position (Player_id, Position_id, Is_Main)
            VALUES (%s, %s, 0)
        """, (player_id, position_id))


def do_make_main_position(cursor, player, form):
    player_id = player["Player_id"]

    position_id = form.get("position_id", type=int)
    if position_id is None:
        raise ValueError("Please select a position")

    # Check BEFORE resetting the flags, so the player never ends up
    # without a main position
    if player_has_position(cursor, player_id, position_id) is None:
        raise ValueError("This player does not have that position")

    set_main_position(cursor, player_id, position_id)


def do_delete_position(cursor, player, form):
    player_id = player["Player_id"]

    position_id = form.get("position_id", type=int)
    if position_id is None:
        raise ValueError("Please select a position")

    position = player_has_position(cursor, player_id, position_id)
    if position is None:
        raise ValueError("This player does not have that position")

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM Player_Position
        WHERE Player_id = %s
    """, (player_id,))

    if cursor.fetchone()["total"] <= 1:
        raise ValueError("Cannot delete the only position of a player")

    cursor.execute("""
        DELETE FROM Player_Position
        WHERE Player_id = %s
          AND Position_id = %s
    """, (player_id, position_id))

    # If the deleted position was the main one, promote another
    if position["Is_Main"]:
        cursor.execute("""
            SELECT Position_id
            FROM Player_Position
            WHERE Player_id = %s
            ORDER BY Position_id
            LIMIT 1
        """, (player_id,))

        new_main = cursor.fetchone()

        if new_main:
            cursor.execute("""
                UPDATE Player_Position
                SET Is_Main = 1
                WHERE Player_id = %s
                  AND Position_id = %s
            """, (player_id, new_main["Position_id"]))


def do_add_club(cursor, player, form):
    club_id, join_date, leave_date, is_actual = read_club_spell(form)
    insert_club_spell(
        cursor, player["Player_id"], club_id,
        join_date, leave_date, is_actual
    )


def do_edit_club(cursor, player, form):
    original_club_id = form.get("original_club_id", type=int)
    original_join_date = parse_date(form.get("original_join_date"))

    if original_club_id is None or original_join_date is None:
        raise ValueError("Invalid club record")

    club_id, join_date, leave_date, is_actual = read_club_spell(form)

    update_club_spell(
        cursor, player["Player_id"],
        original_club_id, original_join_date,
        club_id, join_date, leave_date, is_actual
    )

def do_make_current_club(cursor, player, form):
    player_id = player["Player_id"]

    club_id = form.get("club_id", type=int)
    join_date = parse_date(form.get("join_date"))

    if club_id is None or join_date is None:
        raise ValueError("Invalid club record")

    # Check BEFORE clearing the current flag
    if get_club_record(cursor, player_id, club_id, join_date) is None:
        raise ValueError("Club record not found")

    clear_current_club(cursor, player_id)

    cursor.execute("""
        UPDATE Player_Club
        SET Is_Actual = 1, Leave_Date = NULL
        WHERE Player_id = %s
          AND Club_id = %s
          AND Join_Date = %s
    """, (player_id, club_id, join_date))


def do_delete_club(cursor, player, form):
    player_id = player["Player_id"]

    club_id = form.get("club_id", type=int)
    join_date = parse_date(form.get("join_date"))

    if club_id is None or join_date is None:
        raise ValueError("Invalid club record")

    record = get_club_record(cursor, player_id, club_id, join_date)
    if record is None:
        raise ValueError("Club record not found")

    cursor.execute("""
        DELETE FROM Player_Club
        WHERE Player_id = %s
          AND Club_id = %s
          AND Join_Date = %s
    """, (player_id, club_id, join_date))

    # If the deleted club was current, make the most recent one current
    if record["Is_Actual"]:
        cursor.execute("""
            SELECT Club_id, Join_Date
            FROM Player_Club
            WHERE Player_id = %s
            ORDER BY Join_Date DESC
            LIMIT 1
        """, (player_id,))

        previous_club = cursor.fetchone()

        if previous_club:
            cursor.execute("""
                UPDATE Player_Club
                SET Is_Actual = 1, Leave_Date = NULL
                WHERE Player_id = %s
                  AND Club_id = %s
                  AND Join_Date = %s
            """, (player_id, previous_club["Club_id"],
                  previous_club["Join_Date"]))


ACTIONS = {
    "update_person": do_update_person,
    "update_player": do_update_player,
    "add_position": do_add_position,
    "make_main_position": do_make_main_position,
    "delete_position": do_delete_position,
    "add_club": do_add_club,
    "edit_club": do_edit_club,
    "make_current_club": do_make_current_club,
    "delete_club": do_delete_club,
}


# =====================================================
# ROUTE
# =====================================================

@edit_player.route("/player/<int:player_id>/edit", methods=["GET", "POST"])
def edit_player_page(player_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                p.Person_id,
                p.Person_First_Name,
                p.Person_Last_Name,
                p.Person_Display_Name,
                p.Person_First_Name_ar,
                p.Person_Last_Name_ar,
                p.Person_Display_Name_ar,
                p.Person_birth_date,
                p.Person_death_date,
                p.Sex,
                p.Country_id,

                pl.Player_id,
                pl.Player_Nickname,
                pl.Player_Nickname_ar,
                pl.Main_Jersey_Number,
                pl.Is_Active

            FROM Player pl

            JOIN Person p
                ON pl.Person_id = p.Person_id

            WHERE pl.Player_id = %s
        """, (player_id,))

        player_data = cursor.fetchone()

        if player_data is None:
            return "Player not found", 404

        # =================================================
        # POST
        # =================================================

        if request.method == "POST":
            handler = ACTIONS.get(request.form.get("action"))

            if handler is None:
                return "Unknown action", 400

            try:
                handler(cursor, player_data, request.form)
                connection.commit()

            except ValueError as error:
                # Messages are fixed strings: user input is never echoed
                connection.rollback()
                return str(error), 400

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate entry
                    return "This record already exists", 400
                if error.errno == 1452:      # foreign key failure
                    return "Invalid club, position or country", 400
                raise

            return redirect(
                url_for("edit_player.edit_player_page", player_id=player_id)
            )

        # =================================================
        # GET
        # =================================================

        cursor.execute("""
            SELECT Country_id, Country_Name
            FROM Country
            ORDER BY Country_Name
        """)
        countries = cursor.fetchall()

        cursor.execute("""
            SELECT Position_id, Position_Code, Position_Name
            FROM Position
            ORDER BY Position_Category_id, Position_id
        """)
        positions = cursor.fetchall()

        cursor.execute("""
            SELECT
                pp.Position_id,
                pp.Is_Main,
                po.Position_Code,
                po.Position_Name
            FROM Player_Position pp

            JOIN Position po
                ON pp.Position_id = po.Position_id

            WHERE pp.Player_id = %s

            ORDER BY pp.Is_Main DESC, po.Position_id
        """, (player_id,))
        player_positions = cursor.fetchall()

        current_position_id = next(
            (p["Position_id"] for p in player_positions if p["Is_Main"]),
            None
        )

        cursor.execute("""
            SELECT Club_id, Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)
        clubs = cursor.fetchall()

        cursor.execute("""
            SELECT
                pc.Player_id,
                pc.Club_id,
                pc.Join_Date,
                pc.Leave_Date,
                pc.Is_Actual,
                c.Club_Current_Name
            FROM Player_Club pc

            JOIN Club c
                ON pc.Club_id = c.Club_id

            WHERE pc.Player_id = %s

            ORDER BY pc.Is_Actual DESC, pc.Join_Date DESC
        """, (player_id,))
        player_clubs = cursor.fetchall()

        return render_template(
            "admin/players/edit_player.html",
            Title="Edit Player",
            player=player_data,
            countries=countries,
            positions=positions,
            current_position_id=current_position_id,
            player_positions=player_positions,
            clubs=clubs,
            player_clubs=player_clubs
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in edit player page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()