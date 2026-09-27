from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection


player_club = Blueprint("player_club", __name__)


@player_club.route("/player-club", methods=["GET", "POST"])
def player_club_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        try:

            player_id = request.form.get("player_id")
            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")
            leave_date = request.form.get("leave_date") or None
            is_actual = 1 if request.form.get("is_actual") else 0


            # --------------------------------
            # Validate dates
            # --------------------------------

            if not join_date:
                cursor.close()
                connection.close()
                return "Join date is required", 400

            if leave_date and leave_date < join_date:
                cursor.close()
                connection.close()
                return "Leave date cannot be before Join date", 400

            # تحويل من DD/MM/YYYY إلى YYYY-MM-DD
            if join_date and '/' in join_date:
                date_parts = join_date.split('/')
                join_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"

            if leave_date and '/' in leave_date:
                date_parts = leave_date.split('/')
                leave_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"


            # Current club must not have Leave_Date
            if is_actual:
                leave_date = None

                # Remove current status from other clubs
                cursor.execute("""
                    UPDATE Player_Club
                    SET Is_Actual = 0
                    WHERE Player_id = %s
                """, (player_id,))


            # --------------------------------
            # Insert relation
            # --------------------------------

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
                url_for("player_club.player_club_page")
            )


        except Exception as error:
            connection.rollback()
            cursor.close()
            connection.close()
            return f"Error: {error}", 500


        # ========================================
    # GET REQUEST
    # ========================================

    # Get filter parameters
    search_player = request.args.get("search_player", "").strip()
    search_club = request.args.get("search_club", "").strip()
    status_filter = request.args.get("status_filter", "")

    # --------------------------------
    # Get last added player
    # --------------------------------

    cursor.execute("""
        SELECT Player_id
        FROM Player
        ORDER BY Player_id DESC
        LIMIT 1
    """)

    last_player = cursor.fetchone()
    last_player_id = last_player["Player_id"] if last_player else None


    # --------------------------------
    # Get USMA club ID (assuming Club_id = 1)
    # --------------------------------

    cursor.execute("""
        SELECT Club_id
        FROM Club
        WHERE Club_Current_Name = 'USM Alger'
        LIMIT 1
    """)

    usma_club = cursor.fetchone()
    usma_club_id = usma_club["Club_id"] if usma_club else 1


    # --------------------------------
    # Load all players
    # --------------------------------

    cursor.execute("""
        SELECT
            Player_id,
            Person_Display_Name
        FROM Player
        JOIN Person ON Player.Person_id = Person.Person_id
        ORDER BY Person_Display_Name
    """)

    players = cursor.fetchall()


    # --------------------------------
    # Load all clubs
    # --------------------------------

    cursor.execute("""
        SELECT
            Club_id,
            Club_Current_Name
        FROM Club
        ORDER BY Club_Current_Name
    """)

    clubs = cursor.fetchall()


    # --------------------------------
    # Load player club history with filters
    # --------------------------------

    where_clauses = []
    params = []

    if search_player:
        where_clauses.append("p.Person_Display_Name LIKE %s")
        params.append(f"%{search_player}%")

    if search_club:
        where_clauses.append("c.Club_Current_Name LIKE %s")
        params.append(f"%{search_club}%")

    if status_filter:
        if status_filter == "active":
            where_clauses.append("pc.Is_Actual = 1")
        elif status_filter == "inactive":
            where_clauses.append("pc.Is_Actual = 0")

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    query = f"""
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

        WHERE {where_clause}

        ORDER BY
            pc.Is_Actual DESC,
            pc.Join_Date DESC
    """

    cursor.execute(query, params)
    player_clubs = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "admin/player_club/player_club.html",
        Title="Player Club Management",
        players=players,
        clubs=clubs,
        player_clubs=player_clubs,
        last_player_id=last_player_id,
        usma_club_id=usma_club_id,
        search_player=search_player,
        search_club=search_club,
        status_filter=status_filter
    )


@player_club.route("/player-club/delete/<int:player_id>/<int:club_id>/<join_date>", methods=["POST"])
def delete_player_club(player_id, club_id, join_date):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

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

        connection.commit()

    except Exception as error:
        connection.rollback()
        cursor.close()
        connection.close()
        return f"Error deleting: {error}", 500

    cursor.close()
    connection.close()

    return redirect(
        url_for("player_club.player_club_page")
    )