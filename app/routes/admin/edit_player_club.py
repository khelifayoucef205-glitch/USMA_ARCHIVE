from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection

edit_player_club = Blueprint(
    "edit_player_club",
    __name__,
    url_prefix="/admin/player-club"
)

# =====================================================
# EDIT PLAYER CLUB
# =====================================================

@edit_player_club.route("/<int:player_id>/<int:club_id>/<join_date>/edit", methods=["GET", "POST"])
def edit_player_club_page(player_id, club_id, join_date):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Update
        # =================================================

        if request.method == "POST":

            new_club_id = request.form.get("club_id")
            new_join_date = request.form.get("join_date")
            leave_date = request.form.get("leave_date") or None
            is_actual = 1 if request.form.get("is_actual") else 0

            # Check if relationship exists
            cursor.execute("""
                SELECT Player_id, Club_id, Join_Date
                FROM Player_Club
                WHERE Player_id = %s
                  AND Club_id = %s
                  AND Join_Date = %s
            """, (player_id, club_id, join_date))

            relationship = cursor.fetchone()

            if relationship is None:
                return "Player-club relationship not found", 404

            # Delete old record
            cursor.execute("""
                DELETE FROM Player_Club
                WHERE Player_id = %s
                  AND Club_id = %s
                  AND Join_Date = %s
            """, (player_id, club_id, join_date))

            # Insert new record
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
                new_club_id,
                new_join_date,
                leave_date,
                is_actual
            ))

            connection.commit()

            return redirect(url_for("player_club.player_club_page"))

        # =================================================
        # GET - Load Relationship
        # =================================================

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
        """, (player_id, club_id, join_date))

        relationship = cursor.fetchone()

        if relationship is None:
            return "Player-club relationship not found", 404

        # Load Players
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

        # Load Clubs
        cursor.execute("""
            SELECT
                Club_id,
                Club_Current_Name

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

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()