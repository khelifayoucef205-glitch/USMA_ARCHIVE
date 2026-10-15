from flask import Blueprint, render_template, redirect, url_for, request
from app.database import get_db_connection


staff_members = Blueprint("staff_members", __name__)


USMA_CURRENT_SQL = """
    EXISTS (
        SELECT 1
        FROM Staff_Assignment sa
        WHERE sa.Staff_Member_id = sm.Staff_Member_id
          AND sa.Club_id = 1
          AND sa.End_Date IS NULL
    )
"""

USMA_HISTORY_SQL = """
    EXISTS (
        SELECT 1
        FROM Staff_Assignment sa
        WHERE sa.Staff_Member_id = sm.Staff_Member_id
          AND sa.Club_id = 1
    )
"""


def get_staff_member_status(staff_member_data):

    if staff_member_data.get('Person_death_date'):
        return 'deceased'

    if staff_member_data.get('usma_current'):
        return 'active_with_usma'

    if staff_member_data.get('usma_history'):
        return 'former_usma'

    return 'no_club'


@staff_members.route("/staff-members")
def staff_members_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        search = request.args.get("search", "").strip()
        role_filter = request.args.get("role_filter", "")
        status_filter = request.args.get("status_filter", "")
        nationality_filter = request.args.get("nationality_filter", "")
        sort_by = request.args.get("sort_by", "name")
        sort_order = request.args.get("sort_order", "asc").upper()

        if sort_order not in ["ASC", "DESC"]:
            sort_order = "ASC"

        where_clauses = []
        params = []

        if search:
            where_clauses.append("p.Person_Display_Name LIKE %s")
            params.append(f"%{search}%")

        # Filter by MAIN role (Staff_Member_Role.Is_Main = 1)
        if role_filter and role_filter.isdigit():
            where_clauses.append("""
                EXISTS (
                    SELECT 1
                    FROM Staff_Member_Role smr
                    WHERE smr.Staff_Member_id = sm.Staff_Member_id
                      AND smr.Is_Main = 1
                      AND smr.Role_id = %s
                )
            """)
            params.append(int(role_filter))

        if nationality_filter and nationality_filter.isdigit():
            where_clauses.append("p.Country_id = %s")
            params.append(int(nationality_filter))

        if status_filter == "deceased":

            where_clauses.append("p.Person_death_date IS NOT NULL")

        elif status_filter == "active_with_usma":

            where_clauses.append(f"""
                p.Person_death_date IS NULL
                AND {USMA_CURRENT_SQL}
            """)

        elif status_filter == "former_usma":

            where_clauses.append(f"""
                p.Person_death_date IS NULL
                AND {USMA_HISTORY_SQL}
                AND NOT {USMA_CURRENT_SQL}
            """)

        elif status_filter == "no_club":

            where_clauses.append(f"""
                p.Person_death_date IS NULL
                AND NOT {USMA_HISTORY_SQL}
            """)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        if sort_by == "id":
            order_by = "sm.Staff_Member_id"
        elif sort_by == "name":
            order_by = "p.Person_Display_Name"
        elif sort_by == "nationality":
            order_by = "c.Country_Name"
        elif sort_by == "role":
            order_by = "Role"
        else:
            sort_by = "name"
            order_by = "p.Person_Display_Name"

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

            WHERE {where_clause}

            ORDER BY {order_by} {sort_order}
        """

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
            sort_order=sort_order.lower(),
            roles=roles,
            nationalities=nationalities
        )

    finally:
        cursor.close()
        connection.close()


@staff_members.route("/staff-members/delete/<int:staff_member_id>", methods=["POST"])
def delete_staff_member(staff_member_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT Person_id
            FROM Staff_Member
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        result = cursor.fetchone()

        if result is None:
            return "Staff Member not found", 404

        person_id = result[0]

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
            SELECT 1 FROM Player WHERE Person_id = %s LIMIT 1
        """, (person_id,))
        is_also_player = cursor.fetchone() is not None

        if not is_also_player:
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

    return redirect(url_for("staff_members.staff_members_page"))