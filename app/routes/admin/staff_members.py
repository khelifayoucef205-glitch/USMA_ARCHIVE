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

staff_members = Blueprint("staff_members", __name__)

def get_staff_member_status(staff_member_data):
    """Classify the staff member for display purposes."""
    if staff_member_data.get("Person_death_date"):
        return "deceased"

    if staff_member_data.get("usma_current"):
        return "active_with_usma"

    if staff_member_data.get("usma_history"):
        return "former_usma"

    return "no_club"


# USMA_CLUB_ID is a constant integer, never user input, so it is safe
# to place it in the SQL text.
USMA_CURRENT_SQL = f"""
    EXISTS (
        SELECT 1
        FROM Staff_Assignment sa
        WHERE sa.Staff_Member_id = sm.Staff_Member_id
          AND sa.Club_id = {int(USMA_CLUB_ID)}
          AND sa.End_Date IS NULL
    )
"""

USMA_HISTORY_SQL = f"""
    EXISTS (
        SELECT 1
        FROM Staff_Assignment sa
        WHERE sa.Staff_Member_id = sm.Staff_Member_id
          AND sa.Club_id = {int(USMA_CLUB_ID)}
    )
"""

# Must stay consistent with get_staff_member_status above
STATUS_CONDITIONS = {
    "deceased": "p.Person_death_date IS NOT NULL",
    "active_with_usma": f"p.Person_death_date IS NULL AND {USMA_CURRENT_SQL}",
    "former_usma": (
        "p.Person_death_date IS NULL "
        f"AND {USMA_HISTORY_SQL} AND NOT {USMA_CURRENT_SQL}"
    ),
    "no_club": f"p.Person_death_date IS NULL AND NOT {USMA_HISTORY_SQL}",
}

# Whitelist: user input only selects a key, never goes into the SQL
SORT_COLUMNS = {
    "id": "sm.Staff_Member_id",
    "name": "p.Person_Display_Name",
    "nationality": "c.Country_Name",
    "role": "Role",
}


@staff_members.route("/staff-members")
def staff_members_page():
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role_filter", "").strip()
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

    # Filter by MAIN role (Staff_Member_Role.Is_Main = 1)
    if role_filter.isdigit():
        conditions.append("""
            EXISTS (
                SELECT 1
                FROM Staff_Member_Role smr
                WHERE smr.Staff_Member_id = sm.Staff_Member_id
                  AND smr.Is_Main = 1
                  AND smr.Role_id = %s
            )
        """)
        params.append(int(role_filter))

    if nationality_filter.isdigit():
        conditions.append("p.Country_id = %s")
        params.append(int(nationality_filter))

    if status_filter in STATUS_CONDITIONS:
        conditions.append(f"({STATUS_CONDITIONS[status_filter]})")

    query = f"""
        SELECT
            sm.Staff_Member_id,
            p.Person_Display_Name,
            p.Country_id,
            c.Country_Name,
            sm.Specialty,
            p.Person_death_date,

            (
                SELECT sr.Role_name
                FROM Staff_Member_Role smr
                JOIN Staff_Role sr ON smr.Role_id = sr.Role_id
                WHERE smr.Staff_Member_id = sm.Staff_Member_id
                  AND smr.Is_Main = 1
                ORDER BY sr.Role_id
                LIMIT 1
            ) AS Role,

            {USMA_CURRENT_SQL} AS usma_current,
            {USMA_HISTORY_SQL} AS usma_history

        FROM Staff_Member sm

        JOIN Person p
            ON sm.Person_id = p.Person_id

        LEFT JOIN Country c
            ON p.Country_id = c.Country_id
    """

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += (
        f" ORDER BY {SORT_COLUMNS[sort_by]} {sort_order.upper()}, "
        "sm.Staff_Member_id"
    )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params)
        staff_members_list = cursor.fetchall()

        for staff_data in staff_members_list:
            staff_data["status"] = get_staff_member_status(staff_data)

        cursor.execute("""
            SELECT Role_id, Role_name
            FROM Staff_Role
            ORDER BY Role_id
        """)
        roles = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT c.Country_id, c.Country_Name
            FROM Country c
            JOIN Person p ON c.Country_id = p.Country_id
            JOIN Staff_Member sm ON p.Person_id = sm.Person_id
            ORDER BY c.Country_Name
        """)
        nationalities = cursor.fetchall()

        return render_template(
            "admin/staff_members/staff_members.html",
            Title="Staff Members",
            staff_members=staff_members_list,
            search=search,
            role_filter=role_filter,
            status_filter=status_filter,
            nationality_filter=nationality_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            roles=roles,
            nationalities=nationalities
        )

    finally:
        cursor.close()
        connection.close()


@staff_members.route(
    "/staff-members/delete/<int:staff_member_id>",
    methods=["POST"]
)
def delete_staff_member(staff_member_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT Person_id
            FROM Staff_Member
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        result = cursor.fetchone()

        if result is None:
            return "Staff Member not found", 404

        person_id = result["Person_id"]

        # Refuse if match history exists (it would be lost or blocked by the FK)
        cursor.execute("""
            SELECT 1
            FROM Staff_Member_Football_Match
            WHERE Staff_Member_id = %s
            LIMIT 1
        """, (staff_member_id,))

        if cursor.fetchone():
            return (
                "Cannot delete: this staff member is linked to matches. "
                "Remove those match records first.",
                400
            )

        # Assignments (Staff_Assignment_Season rows go with them via CASCADE)
        cursor.execute("""
            DELETE FROM Staff_Assignment
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        cursor.execute("""
            DELETE FROM Staff_Member_Role
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        cursor.execute("""
            DELETE FROM Staff_Member
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        # Delete Person only if no other role remains (e.g. Player)
        cursor.execute("""
            SELECT 1
            FROM Player
            WHERE Person_id = %s
            LIMIT 1
        """, (person_id,))

        if cursor.fetchone() is None:
            cursor.execute("""
                DELETE FROM Person
                WHERE Person_id = %s
            """, (person_id,))

        connection.commit()
        return redirect(url_for("staff_members.staff_members_page"))

    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1451:      # still referenced by other rows
            return (
                "Cannot delete this staff member because other records "
                "still reference him.",
                400
            )
        current_app.logger.exception("Error while deleting staff member")
        return "Something went wrong", 500

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting staff member")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()