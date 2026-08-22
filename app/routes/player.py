from flask import Blueprint, render_template
from app.database import get_db_connection


player = Blueprint("player", __name__)


@player.route("/player/<int:player_id>")
def player_page(player_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

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
            c.Country_Name,

            pl.Player_id,
            pl.Player_Nickname,
            pl.Player_Nickname_ar,
            pl.Main_Jersey_Number,
            pl.Is_Active

        FROM Player pl

        JOIN Person p
            ON pl.Person_id = p.Person_id

        JOIN Country c
            ON p.Country_id = c.Country_id

        WHERE pl.Player_id = %s
    """, (player_id,))

    player_data = cursor.fetchone()

    if player_data is None:
        cursor.close()
        connection.close()
        return "Player not found", 404


    cursor.execute("""
        SELECT
            po.Position_id,
            po.Position_Code,
            po.Position_Name,
            po.Position_Name_ar,
            pp.Is_Main

        FROM Player_Position pp

        JOIN Position po
            ON pp.Position_id = po.Position_id

        WHERE pp.Player_id = %s

        ORDER BY pp.Is_Main DESC, po.Position_id
    """, (player_id,))

    positions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "player.html",
        Title=player_data["Person_Display_Name"],
        player=player_data,
        positions=positions
    )