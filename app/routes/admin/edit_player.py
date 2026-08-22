from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection


edit_player = Blueprint("edit_player", __name__)


@edit_player.route("/player/<int:player_id>/edit", methods=["GET", "POST"])
def edit_player_page(player_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # =========================================================
    # GET PLAYER
    # =========================================================

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
        cursor.close()
        connection.close()
        return "Player not found", 404


    # =========================================================
    # POST
    # =========================================================

    if request.method == "POST":

        action = request.form.get("action")


        # =====================================================
        # UPDATE PLAYER INFORMATION
        # =====================================================

        if action == "update_player":

            # Person information
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            display_name = request.form.get("display_name")

            first_name_ar = request.form.get("first_name_ar")
            last_name_ar = request.form.get("last_name_ar")
            display_name_ar = request.form.get("display_name_ar")

            birth_date = request.form.get("birth_date") or None
            sex = request.form.get("sex")
            country_id = request.form.get("country_id")

            # Player information
            nickname = request.form.get("nickname")
            nickname_ar = request.form.get("nickname_ar")
            jersey_number = request.form.get("jersey_number") or None
            is_active = 1 if request.form.get("is_active") else 0

            position_id = request.form.get("position_id")


            # -------------------------------------------------
            # Update Person
            # -------------------------------------------------

            cursor.execute("""
                UPDATE Person
                SET
                    Person_First_Name = %s,
                    Person_Last_Name = %s,
                    Person_Display_Name = %s,
                    Person_First_Name_ar = %s,
                    Person_Last_Name_ar = %s,
                    Person_Display_Name_ar = %s,
                    Person_birth_date = %s,
                    Sex = %s,
                    Country_id = %s

                WHERE Person_id = %s
            """, (
                first_name,
                last_name,
                display_name,
                first_name_ar,
                last_name_ar,
                display_name_ar,
                birth_date,
                sex,
                country_id,
                player_data["Person_id"]
            ))


            # -------------------------------------------------
            # Update Player
            # -------------------------------------------------

            cursor.execute("""
                UPDATE Player
                SET
                    Player_Nickname = %s,
                    Player_Nickname_ar = %s,
                    Main_Jersey_Number = %s,
                    Is_Active = %s

                WHERE Player_id = %s
            """, (
                nickname,
                nickname_ar,
                jersey_number,
                is_active,
                player_id
            ))


            # -------------------------------------------------
            # Update Main Position
            # -------------------------------------------------

            if position_id:

                cursor.execute("""
                    UPDATE Player_Position
                    SET Is_Main = 0
                    WHERE Player_id = %s
                """, (player_id,))


                cursor.execute("""
                    INSERT INTO Player_Position (
                        Player_id,
                        Position_id,
                        Is_Main
                    )
                    VALUES (%s, %s, 1)

                    ON DUPLICATE KEY UPDATE
                        Is_Main = 1
                """, (
                    player_id,
                    position_id
                ))


            connection.commit()

            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # ADD PLAYER POSITION
        # =====================================================

        elif action == "add_position":

            position_id = request.form.get("new_position_id")

            if position_id:

                cursor.execute("""
                    SELECT Player_id, Position_id
                    FROM Player_Position
                    WHERE Player_id = %s
                    AND Position_id = %s
                """, (
                    player_id,
                    position_id
                ))

                existing_position = cursor.fetchone()

                if existing_position is None:

                    cursor.execute("""
                        INSERT INTO Player_Position (
                            Player_id,
                            Position_id,
                            Is_Main
                        )
                        VALUES (%s, %s, 0)
                    """, (
                        player_id,
                        position_id
                    ))

                    connection.commit()


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # MAKE POSITION MAIN
        # =====================================================

        elif action == "make_main_position":

            position_id = request.form.get("position_id")

            if position_id:

                cursor.execute("""
                    UPDATE Player_Position
                    SET Is_Main = 0
                    WHERE Player_id = %s
                """, (player_id,))


                cursor.execute("""
                    UPDATE Player_Position
                    SET Is_Main = 1
                    WHERE Player_id = %s
                    AND Position_id = %s
                """, (
                    player_id,
                    position_id
                ))

                connection.commit()


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # DELETE PLAYER POSITION
        # =====================================================

        elif action == "delete_position":

            position_id = request.form.get("position_id")

            if position_id:

                cursor.execute("""
                    SELECT Is_Main
                    FROM Player_Position
                    WHERE Player_id = %s
                    AND Position_id = %s
                """, (
                    player_id,
                    position_id
                ))

                position = cursor.fetchone()


                if position:

                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM Player_Position
                        WHERE Player_id = %s
                    """, (player_id,))

                    total_positions = cursor.fetchone()["total"]


                    # Do not allow deleting the only position
                    if total_positions > 1:

                        cursor.execute("""
                            DELETE FROM Player_Position
                            WHERE Player_id = %s
                            AND Position_id = %s
                        """, (
                            player_id,
                            position_id
                        ))


                        # If deleted position was Main,
                        # make another position Main.
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
                                """, (
                                    player_id,
                                    new_main["Position_id"]
                                ))


                        connection.commit()


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # ADD PLAYER CLUB
        # =====================================================

        elif action == "add_club":

            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")
            leave_date = request.form.get("leave_date") or None

            is_actual = 1 if request.form.get("is_actual") else 0


            # -------------------------------------------------
            # Validate dates
            # -------------------------------------------------

            if not join_date:

                cursor.close()
                connection.close()

                return "Join date is required", 400


            if leave_date and leave_date < join_date:

                cursor.close()
                connection.close()

                return "Leave date cannot be before Join date", 400


            # Current club must not have Leave_Date
            if is_actual:

                leave_date = None


                # Remove current status from other clubs
                cursor.execute("""
                    UPDATE Player_Club
                    SET Is_Actual = 0
                    WHERE Player_id = %s
                """, (player_id,))


            # -------------------------------------------------
            # Insert relation
            # -------------------------------------------------

            try:

                cursor.execute("""
                    INSERT INTO Player_Club (
                        Player_id,
                        Club_id,
                        Join_Date,
                        Leave_Date,
                        Is_Actual
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    player_id,
                    club_id,
                    join_date,
                    leave_date,
                    is_actual
                ))

                connection.commit()

            except Exception as error:

                connection.rollback()

                cursor.close()
                connection.close()

                return f"Could not add player club relationship: {error}", 400


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # EDIT PLAYER CLUB
        # =====================================================

        elif action == "edit_club":

            original_club_id = request.form.get("original_club_id")
            original_join_date = request.form.get("original_join_date")

            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")
            leave_date = request.form.get("leave_date") or None

            is_actual = 1 if request.form.get("is_actual") else 0


            if not join_date:

                cursor.close()
                connection.close()

                return "Join date is required", 400


            if leave_date and leave_date < join_date:

                cursor.close()
                connection.close()

                return "Leave date cannot be before Join date", 400


            # Current club
            if is_actual:

                leave_date = None

                cursor.execute("""
                    UPDATE Player_Club
                    SET Is_Actual = 0
                    WHERE Player_id = %s
                """, (player_id,))


            try:

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
                    club_id,
                    join_date,
                    leave_date,
                    is_actual,
                    player_id,
                    original_club_id,
                    original_join_date
                ))

                connection.commit()

            except Exception as error:

                connection.rollback()

                cursor.close()
                connection.close()

                return f"Could not update player club relationship: {error}", 400


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # MAKE CLUB CURRENT
        # =====================================================

        elif action == "make_current_club":

            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")


            # Remove current status from all clubs
            cursor.execute("""
                UPDATE Player_Club
                SET Is_Actual = 0
                WHERE Player_id = %s
            """, (player_id,))


            # Make selected club current
            cursor.execute("""
                UPDATE Player_Club
                SET
                    Is_Actual = 1,
                    Leave_Date = NULL

                WHERE Player_id = %s
                AND Club_id = %s
                AND Join_Date = %s
            """, (
                player_id,
                club_id,
                join_date
            ))

            connection.commit()

            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # =====================================================
        # DELETE PLAYER CLUB
        # =====================================================

        elif action == "delete_club":

            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")


            cursor.execute("""
                SELECT Is_Actual
                FROM Player_Club
                WHERE Player_id = %s
                AND Club_id = %s
                AND Join_Date = %s
            """, (
                player_id,
                club_id,
                join_date
            ))

            club_relation = cursor.fetchone()


            if club_relation:

                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM Player_Club
                    WHERE Player_id = %s
                """, (player_id,))

                total_clubs = cursor.fetchone()["total"]


                # Delete relation
                cursor.execute("""
                    DELETE FROM Player_Club
                    WHERE Player_id = %s
                    AND Club_id = %s
                    AND Join_Date = %s
                """, (
                    player_id,
                    club_id,
                    join_date
                ))


                # If the deleted club was current,
                # make the most recent previous club current.
                if club_relation["Is_Actual"] and total_clubs > 1:

                    cursor.execute("""
                        SELECT
                            Club_id,
                            Join_Date
                        FROM Player_Club
                        WHERE Player_id = %s
                        ORDER BY Join_Date DESC
                        LIMIT 1
                    """, (player_id,))

                    previous_club = cursor.fetchone()

                    if previous_club:

                        cursor.execute("""
                            UPDATE Player_Club
                            SET
                                Is_Actual = 1,
                                Leave_Date = NULL
                            WHERE Player_id = %s
                            AND Club_id = %s
                            AND Join_Date = %s
                        """, (
                            player_id,
                            previous_club["Club_id"],
                            previous_club["Join_Date"]
                        ))


                connection.commit()


            cursor.close()
            connection.close()

            return redirect(
                url_for(
                    "edit_player.edit_player_page",
                    player_id=player_id
                )
            )


        # Unknown action
        else:

            cursor.close()
            connection.close()

            return "Unknown action", 400


    # =========================================================
    # COUNTRIES
    # =========================================================

    cursor.execute("""
        SELECT
            Country_id,
            Country_Name
        FROM Country
        ORDER BY Country_Name
    """)

    countries = cursor.fetchall()


    # =========================================================
    # POSITIONS
    # =========================================================

    cursor.execute("""
        SELECT
            Position_id,
            Position_Code,
            Position_Name
        FROM Position
        ORDER BY Position_Category_id, Position_id
    """)

    positions = cursor.fetchall()


    # =========================================================
    # CURRENT MAIN POSITION
    # =========================================================

    cursor.execute("""
        SELECT Position_id
        FROM Player_Position
        WHERE Player_id = %s
        AND Is_Main = 1
    """, (player_id,))

    current_position = cursor.fetchone()

    if current_position:
        current_position_id = current_position["Position_id"]
    else:
        current_position_id = None


    # =========================================================
    # PLAYER POSITIONS
    # =========================================================

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


    # =========================================================
    # CLUBS
    # =========================================================

    cursor.execute("""
        SELECT
            Club_id,
            Club_Current_Name
        FROM Club
        ORDER BY Club_Current_Name
    """)

    clubs = cursor.fetchall()


    # =========================================================
    # PLAYER CLUB HISTORY
    # =========================================================

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

        ORDER BY
            pc.Is_Actual DESC,
            pc.Join_Date DESC
    """, (player_id,))

    player_clubs = cursor.fetchall()


    cursor.close()
    connection.close()


    # =========================================================
    # RENDER
    # =========================================================

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
