from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection

player_club = Blueprint(
    "player_club",
    __name__,
    url_prefix="/admin/player-club"
)

# =====================================================
# PLAYER CLUB - CREATE & READ
# =====================================================

@player_club.route("/", methods=["GET", "POST"])
def player_club_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Add Player Club
        # =================================================

        if request.method == "POST":

            player_id = request.form.get("player_id")
            club_id = request.form.get("club_id")
            join_date = request.form.get("join_date")
            leave_date = request.form.get("leave_date") or None

            is_actual = (
                1 if request.form.get("is_actual") else 0
            )

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

            return redirect(
                url_for("player_club.player_club_page")
            )

        # =================================================
        # Load Players
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

        # =================================================
        # Load Clubs
        # =================================================

        cursor.execute("""
            SELECT
                Club_id,
                Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)

        clubs = cursor.fetchall()

        # =================================================
        # Load Player Club Relationships
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

            ORDER BY pc.Join_Date DESC
        """)

        player_clubs = cursor.fetchall()

        return render_template(
            "admin/player_club/player_club.html",
            Title="Player Clubs",
            players=players,
            clubs=clubs,
            player_clubs=player_clubs
        )

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# DELETE PLAYER CLUB
# =====================================================

@player_club.route("/<int:player_id>/<int:club_id>/<join_date>/delete", methods=["POST"])
def delete_player_club(player_id, club_id, join_date):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # Delete Relationship
        # =================================================

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

        return redirect(
            url_for("player_club.player_club_page")
        )

    except Exception as error:
        connection.rollback()
        return f"Error deleting player-club relationship: {error}", 500

    finally:
        cursor.close()
        connection.close()