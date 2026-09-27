from flask import Blueprint, render_template, redirect, url_for, request
from app.database import get_db_connection


players = Blueprint("players", __name__)


def get_player_status(player_data):

    # تحقق من الوفاة
    if player_data.get('Person_death_date'):
        return 'deceased'
    
    # تحقق من النشاط
    if not player_data.get('Is_Active'):
        return 'retired'
    
    # تحقق من USMA الحالي
    if player_data.get('usma_current'):
        return 'active_with_usma'
    
    # إذا كان نشطاً لكن ليس مع USMA
    if player_data.get('usma_history'):
        return 'former_usma'
    
    # نشط لكن لا تاريخ مع USMA
    return 'active_no_club'


@players.route("/players")
def players_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get filter and search parameters
    search = request.args.get("search", "").strip()
    position_filter = request.args.get("position_filter", "")
    status_filter = request.args.get("status_filter", "")
    nationality_filter = request.args.get("nationality_filter", "")
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc").upper()
    
    # Validate sort_order
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "ASC"
    
    # Build WHERE clause dynamically
    where_clauses = ["(pp.Is_Main = 1 OR pp.Is_Main IS NULL)"]
    params = []
    
    # Search by player name
    if search:
        where_clauses.append("p.Person_Display_Name LIKE %s")
        params.append(f"%{search}%")
    
    # Filter by position
    if position_filter:
        where_clauses.append("poc.Category_Name = %s")
        params.append(position_filter)
    
    # Filter by nationality
    if nationality_filter and nationality_filter.isdigit():
        where_clauses.append("p.Country_id = %s")
        params.append(int(nationality_filter))
    
    if status_filter:

        if status_filter == "deceased":

            where_clauses.append("""
                p.Person_death_date IS NOT NULL
            """)

        elif status_filter == "retired":

            where_clauses.append("""
                pl.Is_Active = 0
                AND p.Person_death_date IS NULL
            """)

        elif status_filter == "active_with_usma":

            where_clauses.append("""
                pl.Is_Active = 1
                AND p.Person_death_date IS NULL
                AND EXISTS (
                    SELECT 1
                    FROM Player_Club pc
                    WHERE pc.Player_id = pl.Player_id
                      AND pc.Club_id = 1
                      AND pc.Is_Actual = 1
                      AND pc.Leave_Date IS NULL
                )
            """)

        elif status_filter == "former_usma":

            where_clauses.append("""
                pl.Is_Active = 1
                AND p.Person_death_date IS NULL

                AND EXISTS (
                    SELECT 1
                    FROM Player_Club pc
                    WHERE pc.Player_id = pl.Player_id
                      AND pc.Club_id = 1
                )

                AND NOT EXISTS (
                    SELECT 1
                    FROM Player_Club pc
                    WHERE pc.Player_id = pl.Player_id
                      AND pc.Club_id = 1
                      AND pc.Is_Actual = 1
                      AND pc.Leave_Date IS NULL
                )
            """)

        elif status_filter == "active_no_club":

            where_clauses.append("""
                pl.Is_Active = 1
                AND p.Person_death_date IS NULL

                AND NOT EXISTS (
                    SELECT 1
                    FROM Player_Club pc
                    WHERE pc.Player_id = pl.Player_id
                      AND pc.Club_id = 1
                )
            """)
    where_clause = " AND ".join(where_clauses)

    # Build ORDER BY clause
    if sort_by == "id":
        order_by = "pl.Player_id"

    elif sort_by == "name":
        order_by = "p.Person_Display_Name"

    elif sort_by == "nationality":
        order_by = "c.Country_Name"

    elif sort_by == "position":
        order_by = "po.Position_id"

    elif sort_by == "jersey":
        order_by = "pl.Main_Jersey_Number"

    else:
        sort_by = "name"
        order_by = "p.Person_Display_Name"

    query = f"""
        SELECT
            pl.Player_id,
            p.Person_Display_Name,
            p.Country_id,
            c.Country_Name,
            po.Position_Category_id,
            po.Position_Code,
            po.Position_Name,
            poc.Category_Name,
            pl.Main_Jersey_Number,
            pl.Is_Active,
            p.Person_death_date,

            EXISTS (
                SELECT 1
                FROM Player_Club pc
                WHERE pc.Player_id = pl.Player_id
                  AND pc.Club_id = 1
                  AND pc.Is_Actual = 1
                  AND pc.Leave_Date IS NULL
            ) AS usma_current,

            EXISTS (
                SELECT 1
                FROM Player_Club pc
                WHERE pc.Player_id = pl.Player_id
                  AND pc.Club_id = 1
            ) AS usma_history

        FROM Player pl

        JOIN Person p
            ON pl.Person_id = p.Person_id

        LEFT JOIN Country c
            ON p.Country_id = c.Country_id

        LEFT JOIN Player_Position pp
            ON pl.Player_id = pp.Player_id

        LEFT JOIN Position po
            ON pp.Position_id = po.Position_id

        LEFT JOIN Position_Category poc
            ON po.Position_Category_id = poc.Position_Category_id

        WHERE {where_clause}

        ORDER BY {order_by} {sort_order}
    """
    cursor.execute(query, params)
    players_list = cursor.fetchall()
    for player_data in players_list:
        player_data["status"] = get_player_status(player_data)

    # Get all unique positions for filter dropdown
    cursor.execute("""
        SELECT DISTINCT po.Position_Code
        FROM Position po
        ORDER BY po.Position_Code
    """)
    positions = [row["Position_Code"] for row in cursor.fetchall()]

    # Get all unique nationalities for filter dropdown
    cursor.execute("""
        SELECT DISTINCT c.Country_id, c.Country_Name
        FROM Country c
        JOIN Person p ON c.Country_id = p.Country_id
        JOIN Player pl ON p.Person_id = pl.Person_id
        ORDER BY c.Country_Name
    """)

    nationalities = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin/players/players.html",
        Title="Players",
        players=players_list,
        search=search,
        position_filter=position_filter,
        status_filter=status_filter,
        nationality_filter=nationality_filter,
        sort_by=sort_by,
        sort_order=sort_order.lower(),
        positions=positions,
        nationalities=nationalities
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