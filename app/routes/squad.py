from flask import Blueprint, render_template, request
from app.database import get_db_connection
from datetime import datetime


squad = Blueprint("squad", __name__)


def calculate_age(birth_date, reference_date):
    if not birth_date:
        return None
    
    try:
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()


        if birth_date > reference_date:
            return None
        
        age_in_days = (reference_date - birth_date).days
        
        
        age_decimal = age_in_days / 365.25
        
        return (int(age_decimal), age_decimal)
    except:
        return None

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

    # Get sorting parameters
    sort_by = request.args.get("sort_by", "position")
    sort_order = request.args.get("sort_order", "asc").upper()

    # Validate sort_order
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "ASC"

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

    # Get the selected season's details (for age calculation)
    season_details = None
    for season in seasons:
        if season["Season_Number"] == int(selected_season):
            season_details = season
            break

    # Load USMA squad for selected season
    cursor.execute("""
        SELECT
            ps.Player_id,
            pe.Person_Display_Name,
            pe.Person_Display_Name_ar,
            pe.Person_birth_date,
            c.Club_Current_Name,
            p.Position_id,
            p.Position_Code,
            p.Position_Name,
            p.Position_Category_id,
            pc.Category_Name,
            pc.Category_Name_ar,
            co.Country_Name,
            co.Country_Name_ar,
            co.ISO_Alpha2,
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

        JOIN Position_Category pc
            ON p.Position_Category_id = pc.Position_Category_id

        JOIN Country co
            ON pe.Country_id = co.Country_id

        WHERE ps.Club_id = 1
          AND ps.Season_Number = %s

        ORDER BY
            p.Position_Category_id,
            p.Position_id,
            ps.Jersey_Number
    """, (selected_season,))

    players_data = cursor.fetchall()

    # Calculate age for each player based on season dates
    players = []
    if season_details:
        reference_date = datetime(season_details["Start_Year"], 7, 1)
        
        for player in players_data:
            player["Age"] = calculate_age(player["Person_birth_date"], reference_date)
            players.append(player)
    else:
        players = players_data

    # =====================================================
    # SORTING LOGIC
    # =====================================================

    if sort_by == "jersey":
        # Sort by Jersey Number
        players.sort(
            key=lambda p: p["Jersey_Number"] if p["Jersey_Number"] else 999,
            reverse=(sort_order == "DESC")
        )
    
    elif sort_by == "age":
        players.sort(
            key=lambda p: p["Age"][1] if p["Age"] is not None else 999,
            reverse=(sort_order == "DESC")
        )
    
    elif sort_by == "name":
        # Sort by Player Name
        players.sort(
            key=lambda p: p["Person_Display_Name"],
            reverse=(sort_order == "DESC")
        )
    
    else:  # position (default)
        # Sort by Position Category and Position
        players.sort(
            key=lambda p: (p["Position_Category_id"], p["Position_id"]),
            reverse=(sort_order == "DESC")
        )
    # =====================================================
    # CALCULATE STATISTICS
    # =====================================================
    position_stats = {}
    for player in players:
        category_id = player["Position_Category_id"]
        category_name = player["Category_Name"]
        age = player["Age"]
        if category_id not in position_stats:
            position_stats[category_id] = {
                "category_name": category_name,
                "count": 0,
                "known_age_count": 0,
                "total_age": 0,
                "avg_age": 0
            }
        position_stats[category_id]["count"] += 1
        if age is not None:
            position_stats[category_id]["known_age_count"] += 1
            position_stats[category_id]["total_age"] += age[0]
    # حساب متوسط الأعمار لكل منصب
    for stats in position_stats.values():
        if stats["known_age_count"] > 0:
            stats["avg_age"] = round(
                stats["total_age"] / stats["known_age_count"],
                1
            )
        else:
            stats["avg_age"] = 0
    position_stats = dict(sorted(position_stats.items()))
    # =====================================================
    # TOTAL STATISTICS
    # =====================================================
    total_players = len(players)
    total_age = sum(
        p["Age"][0]
        for p in players
        if p["Age"] is not None
    )
    known_age_count = sum(
        1
        for p in players
        if p["Age"] is not None
    )
    avg_age_total = (
        round(total_age / known_age_count, 1)
        if known_age_count > 0
        else 0 
    )

        # =====================================================
    # USMA STAFF FOR THE SELECTED SEASON
    # =====================================================

    cursor.execute("""
        SELECT
            sa.Assignment_id,
            sa.Staff_Member_id,
            p.Person_Display_Name,
            co.Country_Name,
            sr.Role_name,
            sa.Start_Date,
            sa.End_Date

        FROM Staff_Assignment sa

        JOIN Staff_Assignment_Season sas
            ON sas.Assignment_id = sa.Assignment_id

        JOIN Staff_Member sm
            ON sa.Staff_Member_id = sm.Staff_Member_id

        JOIN Person p
            ON sm.Person_id = p.Person_id

        LEFT JOIN Country co
            ON p.Country_id = co.Country_id

        JOIN Staff_Role sr
            ON sa.Role_id = sr.Role_id

        WHERE sa.Club_id = 1
          AND sas.Season_Number = %s

        ORDER BY sa.Start_Date, sr.Role_id
    """, (selected_season,))

    staff = cursor.fetchall()

        # =====================================================
    # USMA TITLES WON IN THE SELECTED SEASON
    # =====================================================

    cursor.execute("""
        SELECT
            c.Competition_id,
            c.Competition_Name,
            c.Competition_Name_ar,
            c.Competition_Type
        FROM Competition_Season cs

        JOIN Competition c
            ON cs.Competition_id = c.Competition_id

        WHERE cs.Competition_Winner_Club_id = 1
          AND cs.Season_Number = %s

        ORDER BY c.Competition_id
    """, (selected_season,))

    titles = cursor.fetchall()

        
    cursor.close()
    connection.close()

    return render_template(
        "squad.html",
        Title="Squad",
        seasons=seasons,
        players=players,
        staff=staff,
        titles=titles,
        selected_season=int(selected_season) if selected_season else None,
        sort_by=sort_by,
        sort_order=sort_order.lower(),
        position_stats=position_stats,
        total_players=total_players,
        avg_age_total=avg_age_total
    )