from flask import Blueprint, abort, render_template

from app.constants import USMA_CLUB_ID
from app.database import get_db_connection
from app.utils import calculate_age

player = Blueprint("player", __name__)


def get_player_status(player_data):
    """Classify the player for display purposes."""
    if player_data.get("Person_death_date"):
        return "deceased"

    if not player_data.get("Is_Active"):
        return "retired"

    if player_data.get("usma_current"):
        return "active_with_usma"

    if player_data.get("usma_history"):
        return "former_usma"

    return "active_no_club"

@player.route("/player/<int:player_id>")
def player_page(player_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # 1. Basic player data
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
                c.Country_Name,
                c.Country_Name_ar,
                pl.Player_id,
                pl.Player_Nickname,
                pl.Player_Nickname_ar,
                pl.Is_Active
            FROM Player pl
            JOIN Person p ON pl.Person_id = p.Person_id
            LEFT JOIN Country c ON p.Country_id = c.Country_id
            WHERE pl.Player_id = %s
        """, (player_id,))

        player_data = cursor.fetchone()

        if player_data is None:
            abort(404)

        # 2. Positions
        cursor.execute("""
            SELECT
                po.Position_id,
                po.Position_Code,
                po.Position_Name,
                po.Position_Name_ar,
                pc.Category_Name,
                pc.Category_Name_ar,
                pp.Is_Main
            FROM Player_Position pp
            JOIN Position po ON pp.Position_id = po.Position_id
            JOIN Position_Category pc
                ON po.Position_Category_id = pc.Position_Category_id
            WHERE pp.Player_id = %s
            ORDER BY pp.Is_Main DESC, po.Position_id
        """, (player_id,))

        positions = cursor.fetchall()

        # 3. Club history (USMA and other clubs)
        cursor.execute("""
            SELECT
                pc.Club_id,
                c.Club_Current_Name,
                c.Club_Short_Name,
                ci.City_Name,
                pc.Join_Date,
                pc.Leave_Date,
                pc.Is_Actual
            FROM Player_Club pc
            JOIN Club c ON pc.Club_id = c.Club_id
            LEFT JOIN City ci ON c.City_id = ci.City_id
            WHERE pc.Player_id = %s
            ORDER BY pc.Join_Date DESC
        """, (player_id,))

        club_records = cursor.fetchall()

        usma_records = [r for r in club_records if r["Club_id"] == USMA_CLUB_ID]
        other_clubs = [r for r in club_records if r["Club_id"] != USMA_CLUB_ID]

        # Records are ordered newest first: the first ongoing spell is the
        # current one. Any additional ongoing spell (a data inconsistency)
        # is kept in the history instead of being dropped.
        usma_current = None
        usma_history = []

        for record in usma_records:
            is_ongoing = record["Is_Actual"] == 1 and record["Leave_Date"] is None

            if is_ongoing and usma_current is None:
                usma_current = record
            else:
                usma_history.append(record)

        # 4. USMA seasons
        cursor.execute("""
            SELECT
                ps.Season_Number,
                s.Season_Name,
                s.Start_Year,
                s.End_Year,
                po.Position_Code,
                po.Position_Name,
                po.Position_Name_ar,
                ps.Jersey_Number
            FROM Player_Season ps
            JOIN Season s ON ps.Season_Number = s.Season_Number
            JOIN Position po ON ps.Position_id = po.Position_id
            WHERE ps.Player_id = %s
              AND ps.Club_id = %s
            ORDER BY s.Start_Year DESC
        """, (player_id, USMA_CLUB_ID))

        usma_seasons = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    # Derived values used by the template
    player_data["usma_current"] = usma_current
    player_data["usma_history"] = usma_history
    player_data["age"] = calculate_age(
        player_data["Person_birth_date"],
        player_data["Person_death_date"]
    )

    return render_template(
        "player.html",
        Title=player_data["Person_Display_Name"],
        player=player_data,
        positions=positions,
        usma_current=usma_current,
        usma_history=usma_history,
        usma_seasons=usma_seasons,
        other_clubs=other_clubs,
        player_status=get_player_status(player_data)
    )