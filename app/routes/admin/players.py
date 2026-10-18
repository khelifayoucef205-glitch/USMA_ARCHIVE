from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from mysql.connector import IntegrityError

from app.constants import USMA_CLUB_ID
from app.database import get_db_connection
from app.utils import escape_like

players = Blueprint("players", __name__)

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


# USMA_CLUB_ID is a constant integer, never user input, so it is safe
# to place it in the SQL text.
USMA_CURRENT_SQL = f"""
    EXISTS (
        SELECT 1
        FROM Player_Club pc
        WHERE pc.Player_id = pl.Player_id
          AND pc.Club_id = {int(USMA_CLUB_ID)}
          AND pc.Is_Actual = 1
          AND pc.Leave_Date IS NULL
    )
"""

USMA_ANY_SQL = f"""
    EXISTS (
        SELECT 1
        FROM Player_Club pc
        WHERE pc.Player_id = pl.Player_id
          AND pc.Club_id = {int(USMA_CLUB_ID)}
    )
"""

# Must stay consistent with get_player_status above
ACTIVE_ALIVE = "pl.Is_Active = 1 AND p.Person_death_date IS NULL"

STATUS_CONDITIONS = {
    "deceased": "p.Person_death_date IS NOT NULL",
    "retired": "pl.Is_Active = 0 AND p.Person_death_date IS NULL",
    "active_with_usma": f"{ACTIVE_ALIVE} AND {USMA_CURRENT_SQL}",
    "former_usma": (
        f"{ACTIVE_ALIVE} AND {USMA_ANY_SQL} AND NOT {USMA_CURRENT_SQL}"
    ),
    "active_no_club": f"{ACTIVE_ALIVE} AND NOT {USMA_ANY_SQL}",
}

# Whitelist: user input only selects a key, never goes into the SQL
SORT_COLUMNS = {
    "id": ["pl.Player_id"],
    "name": ["p.Person_Display_Name"],
    "nationality": ["c.Country_Name"],
    "position": ["po.Position_Category_id", "po.Position_id"],
    "jersey": ["pl.Main_Jersey_Number"],
}


@players.route("/players")
def players_page():
    search = request.args.get("search", "").strip()
    position_filter = request.args.get("position_filter", "").strip()
    status_filter = request.args.get("status_filter", "").strip()
    nationality_filter = request.args.get("nationality_filter", "").strip()

    sort_by = request.args.get("sort_by", "name")
    if sort_by not in SORT_COLUMNS:
        sort_by = "name"

    sort_order = request.args.get("sort_order", "asc").lower()
    if sort_order not in ("asc", "desc"):
        sort_order = "asc"

    # Only fixed SQL fragments are added here; values go in params
    conditions = []
    params = []

    if search:
        conditions.append("p.Person_Display_Name LIKE %s")
        params.append(f"%{escape_like(search)}%")

    if position_filter:
        # The dropdown lists position codes while this used to compare the
        # category name: both are accepted until the template is checked.
        conditions.append("(po.Position_Code = %s OR poc.Category_Name = %s)")
        params.extend([position_filter, position_filter])

    if nationality_filter.isdigit():
        conditions.append("p.Country_id = %s")
        params.append(int(nationality_filter))

    if status_filter in STATUS_CONDITIONS:
        conditions.append(f"({STATUS_CONDITIONS[status_filter]})")

    direction = sort_order.upper()
    order_by = ", ".join(f"{col} {direction}" for col in SORT_COLUMNS[sort_by])

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
            {USMA_CURRENT_SQL} AS usma_current,
            {USMA_ANY_SQL} AS usma_history

        FROM Player pl

        JOIN Person p
            ON pl.Person_id = p.Person_id

        LEFT JOIN Country c
            ON p.Country_id = c.Country_id

        LEFT JOIN Player_Position pp
            ON pl.Player_id = pp.Player_id
            AND pp.Is_Main = 1

        LEFT JOIN Position po
            ON pp.Position_id = po.Position_id

        LEFT JOIN Position_Category poc
            ON po.Position_Category_id = poc.Position_Category_id
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY {order_by}, pl.Player_id"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params)
        players_list = cursor.fetchall()

        for player_data in players_list:
            player_data["status"] = get_player_status(player_data)

        # Positions for the filter dropdown
        cursor.execute("""
            SELECT Position_Code
            FROM Position
            ORDER BY Position_Code
        """)
        positions = [row["Position_Code"] for row in cursor.fetchall()]

        # Nationalities for the filter dropdown
        cursor.execute("""
            SELECT DISTINCT c.Country_id, c.Country_Name
            FROM Country c
            JOIN Person p ON c.Country_id = p.Country_id
            JOIN Player pl ON p.Person_id = pl.Person_id
            ORDER BY c.Country_Name
        """)
        nationalities = cursor.fetchall()

        return render_template(
            "admin/players/players.html",
            Title="Players",
            players=players_list,
            search=search,
            position_filter=position_filter,
            status_filter=status_filter,
            nationality_filter=nationality_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            positions=positions,
            nationalities=nationalities
        )

    except Exception:
        current_app.logger.exception("Error in players page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


@players.route("/players/delete/<int:player_id>", methods=["POST"])
def delete_player(player_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT Person_id
            FROM Player
            WHERE Player_id = %s
        """, (player_id,))

        result = cursor.fetchone()

        if result is None:
            return "Player not found", 404

        person_id = result["Person_id"]

        cursor.execute("""
            DELETE FROM Player_Position
            WHERE Player_id = %s
        """, (player_id,))

        cursor.execute("""
            DELETE FROM Player
            WHERE Player_id = %s
        """, (player_id,))

        # Keep the Person if he is also a staff member
        cursor.execute("""
            SELECT 1
            FROM Staff_Member
            WHERE Person_id = %s
        """, (person_id,))

        if cursor.fetchone() is None:
            cursor.execute("""
                DELETE FROM Person
                WHERE Person_id = %s
            """, (person_id,))

        connection.commit()
        return redirect(url_for("players.players_page"))

    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1451:      # still referenced by other rows
            return (
                "This player cannot be deleted because he still has "
                "club or season records. Delete those first.",
                400
            )
        current_app.logger.exception("Error while deleting player")
        return "Something went wrong", 500

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting player")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()