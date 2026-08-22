from flask import Blueprint, render_template, redirect, url_for
from app.database import get_db_connection


players = Blueprint("players", __name__)


@players.route("/players")
def players_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pl.Player_id,
            p.Person_Display_Name,
            c.Country_Name,
            po.Position_Code,
            po.Position_Name,
            pl.Main_Jersey_Number,
            pl.Is_Active

        FROM Player pl

        JOIN Person p
            ON pl.Person_id = p.Person_id

        JOIN Country c
            ON p.Country_id = c.Country_id

        JOIN Player_Position pp
            ON pl.Player_id = pp.Player_id

        JOIN Position po
            ON pp.Position_id = po.Position_id

        WHERE pp.Is_Main = 1

        ORDER BY p.Person_Display_Name
    """)

    players_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin/players/players.html",
        Title="Players",
        players=players_list
    )


@players.route("/players/delete/<int:player_id>", methods=["POST"])
def delete_player(player_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Get Person_id before deleting the Player
        cursor.execute("""
            SELECT Person_id
            FROM Player
            WHERE Player_id = %s
        """, (player_id,))

        result = cursor.fetchone()

        if result is None:
            return "Player not found", 404

        person_id = result[0]

        # Delete Player_Position relations
        cursor.execute("""
            DELETE FROM Player_Position
            WHERE Player_id = %s
        """, (player_id,))

        # Delete Player
        cursor.execute("""
            DELETE FROM Player
            WHERE Player_id = %s
        """, (player_id,))

        # Delete Person
        cursor.execute("""
            DELETE FROM Person
            WHERE Person_id = %s
        """, (person_id,))

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()
        connection.close()

    return redirect(url_for("players.players_page"))