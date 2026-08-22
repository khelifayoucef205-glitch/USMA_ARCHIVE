from flask import Blueprint, render_template, request
from app.database import get_db_connection


squad = Blueprint("squad", __name__)


@squad.route("/squad")
def squad_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get selected season
    selected_season = request.args.get("season")

    # If no season is selected, use the latest season
    if selected_season is None:
        cursor.execute("""
            SELECT Season_Number
            FROM Season
            ORDER BY Start_Year DESC
            LIMIT 1
        """)

        latest_season = cursor.fetchone()

        if latest_season:
            selected_season = latest_season["Season_Number"]

    # Load all seasons
    cursor.execute("""
        SELECT
            Season_Number,
            Season_Name,
            Start_Year,
            End_Year
        FROM Season
        ORDER BY Start_Year DESC
    """)

    seasons = cursor.fetchall()

    # Load USMA squad for selected season
    cursor.execute("""
        SELECT
            ps.Player_id,
            pe.Person_Display_Name,
            pe.Person_Display_Name_ar,
            pe.Person_birth_date,
            c.Club_Current_Name,
            p.Position_Code,
            p.Position_Name,
            ps.Jersey_Number
        FROM Player_Season ps

        JOIN Player pl
            ON ps.Player_id = pl.Player_id

        JOIN Person pe
            ON pl.Person_id = pe.Person_id

        JOIN Club c
            ON ps.Club_id = c.Club_id

        JOIN Position p
            ON ps.Position_id = p.Position_id

        WHERE ps.Club_id = 1
          AND ps.Season_Number = %s

        ORDER BY
            p.Position_Category_id,
            p.Position_id,
            ps.Jersey_Number
    """, (selected_season,))

    players = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "squad.html",
        Title="Squad",
        seasons=seasons,
        players=players,
        selected_season=int(selected_season) if selected_season else None
    )