from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)

from app.database import get_db_connection
from app.routes.admin.person_utils import create_person
from app.utils import clean_text, parse_int

add_player = Blueprint("add_player", __name__)


@add_player.route("/add-player", methods=["GET", "POST"])
def add_player_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if request.method == "POST":
            form = request.form

            # --------------------------------
            # Validate player data first (nothing is written yet)
            # --------------------------------

            try:
                position_id = parse_int(form.get("position_id"), "Main position")
                jersey_number = parse_int(
                    form.get("jersey_number"), "Jersey number", minimum=0
                )
                other_positions = {
                    parse_int(value, "Other position")
                    for value in form.getlist("other_positions")
                    if value
                }
            except ValueError as error:
                return str(error), 400

            if position_id is None:
                return "Please select a main position", 400

            # The main position must not be inserted twice
            other_positions.discard(position_id)

            # Make sure every selected position really exists
            wanted_positions = {position_id} | other_positions
            placeholders = ", ".join(["%s"] * len(wanted_positions))

            cursor.execute(
                f"SELECT Position_id FROM Position "
                f"WHERE Position_id IN ({placeholders})",
                tuple(wanted_positions)
            )

            if len(cursor.fetchall()) != len(wanted_positions):
                return "One or more selected positions are invalid", 400

            nickname = form.get("nickname") or None
            nickname_ar = form.get("nickname_ar") or None
            is_active = 1 if form.get("is_active") else 0

            # --------------------------------
            # Existing person or new person
            # --------------------------------

            if form.get("person_source", "new") == "existing":
                existing_person_id = form.get("existing_person_id")

                if not existing_person_id:
                    return "Please select an existing person", 400

                cursor.execute("""
                    SELECT p.Person_id
                    FROM Person p
                    LEFT JOIN Player pl
                        ON pl.Person_id = p.Person_id
                    WHERE p.Person_id = %s
                      AND pl.Player_id IS NULL
                """, (existing_person_id,))

                person = cursor.fetchone()

                if person is None:
                    return "Invalid person or person is already a player", 400

                person_id = person["Person_id"]

            else:
                try:
                    person_id = create_person(cursor, form)
                except ValueError as error:
                    return str(error), 400

            # --------------------------------
            # Create Player
            # --------------------------------

            cursor.execute("""
                INSERT INTO Player (
                    Person_id,
                    Player_Nickname,
                    Player_Nickname_ar,
                    Main_Jersey_Number,
                    Is_Active
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                person_id,
                nickname,
                nickname_ar,
                jersey_number,
                is_active
            ))

            player_id = cursor.lastrowid

            # --------------------------------
            # Positions (main + others)
            # --------------------------------

            cursor.execute("""
                INSERT INTO Player_Position (Player_id, Position_id, Is_Main)
                VALUES (%s, %s, 1)
            """, (player_id, position_id))

            for other_id in sorted(other_positions):
                cursor.execute("""
                    INSERT INTO Player_Position (Player_id, Position_id, Is_Main)
                    VALUES (%s, %s, 0)
                """, (player_id, other_id))

            connection.commit()

            return redirect(url_for("players.players_page"))

        # ========================================
        # GET
        # ========================================

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
                p.Person_id,
                p.Person_Display_Name,
                p.Person_Display_Name_ar,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM Staff_Member sm
                        WHERE sm.Person_id = p.Person_id
                    )
                    THEN 1
                    ELSE 0
                END AS is_staff

            FROM Person p

            WHERE NOT EXISTS (
                SELECT 1
                FROM Player pl
                WHERE pl.Person_id = p.Person_id
            )

            ORDER BY p.Person_Display_Name
        """)
        existing_persons = cursor.fetchall()

        return render_template(
            "admin/players/add_player.html",
            Title="Add Player",
            countries=countries,
            positions=positions,
            existing_persons=existing_persons
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while adding player")
        return "Error while adding player", 500

    finally:
        cursor.close()
        connection.close()