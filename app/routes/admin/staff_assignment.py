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
from app.routes.admin.staff_assignment_utils import (
    clean_season_ids,
    has_overlap,
    parse_date,
    valid_role_ids,
)

staff_assignment = Blueprint("staff_assignment", __name__)


@staff_assignment.route("/staff-assignment", methods=["GET", "POST"])
def staff_assignment_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Add assignment
        # =================================================

        if request.method == "POST":
            staff_member_id = request.form.get("staff_member_id", type=int)
            club_id = request.form.get("club_id", type=int)
            role_id = request.form.get("role_id", type=int)

            if None in (staff_member_id, club_id, role_id):
                return "Staff member, club and role are required", 400

            if not valid_role_ids(cursor, [role_id]):
                return "Please select a valid role", 400

            try:
                start_date = parse_date(request.form.get("start_date"))
                end_date = parse_date(request.form.get("end_date"))
            except ValueError as error:
                return str(error), 400

            if not start_date:
                return "Start date is required", 400

            if end_date and end_date < start_date:
                return "End date cannot be before Start date", 400

            if has_overlap(cursor, staff_member_id, club_id, role_id,
                           start_date, end_date):
                return ("This person already has an overlapping assignment "
                        "with the same club and role"), 400

            season_ids = clean_season_ids(
                cursor, request.form.getlist("season_ids")
            )

            try:
                cursor.execute("""
                    INSERT INTO Staff_Assignment (
                        Staff_Member_id,
                        Club_id,
                        Role_id,
                        Start_Date,
                        End_Date
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (staff_member_id, club_id, role_id, start_date, end_date))

                assignment_id = cursor.lastrowid

                for season_number in season_ids:
                    cursor.execute("""
                        INSERT INTO Staff_Assignment_Season
                            (Assignment_id, Season_Number)
                        VALUES (%s, %s)
                    """, (assignment_id, season_number))

                connection.commit()

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1452:      # foreign key failure
                    return "Invalid staff member or club", 400
                raise

            return redirect(url_for("staff_assignment.staff_assignment_page"))

        # =================================================
        # GET
        # =================================================

        search_staff_member = request.args.get("search_staff_member", "").strip()
        search_club = request.args.get("search_club", "").strip()
        role_filter = request.args.get("role_filter", "").strip()
        status_filter = request.args.get("status_filter", "").strip()

        # Last added staff member (pre-selected in the form)
        cursor.execute("""
            SELECT Staff_Member_id
            FROM Staff_Member
            ORDER BY Staff_Member_id DESC
            LIMIT 1
        """)
        last_staff_member = cursor.fetchone()
        last_staff_member_id = (
            last_staff_member["Staff_Member_id"] if last_staff_member else None
        )

        cursor.execute("""
            SELECT sm.Staff_Member_id, p.Person_Display_Name
            FROM Staff_Member sm
            JOIN Person p ON sm.Person_id = p.Person_id
            ORDER BY p.Person_Display_Name
        """)
        staff_members = cursor.fetchall()

        cursor.execute("""
            SELECT Club_id, Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)
        clubs = cursor.fetchall()

        cursor.execute("""
            SELECT Role_id, Role_name
            FROM Staff_Role
            ORDER BY Role_id
        """)
        roles = cursor.fetchall()

        cursor.execute("""
            SELECT Season_Number, Season_Name
            FROM Season
            ORDER BY Start_Year DESC, Season_Number DESC
        """)
        seasons = cursor.fetchall()

        # Only fixed SQL fragments are added here; values go in params
        conditions = []
        params = []

        if search_staff_member:
            conditions.append("p.Person_Display_Name LIKE %s")
            params.append(f"%{escape_like(search_staff_member)}%")

        if search_club:
            conditions.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{escape_like(search_club)}%")

        if role_filter.isdigit():
            conditions.append("sa.Role_id = %s")
            params.append(int(role_filter))

        if status_filter == "current":
            conditions.append("sa.End_Date IS NULL")
        elif status_filter == "former":
            conditions.append("sa.End_Date IS NOT NULL")

        query = """
            SELECT
                sa.Assignment_id,
                sa.Staff_Member_id,
                sa.Club_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name,
                GROUP_CONCAT(s.Season_Name ORDER BY s.Start_Year SEPARATOR ', ') AS Seasons

            FROM Staff_Assignment sa

            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
            LEFT JOIN Staff_Assignment_Season sas ON sas.Assignment_id = sa.Assignment_id
            LEFT JOIN Season s ON s.Season_Number = sas.Season_Number
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            GROUP BY
                sa.Assignment_id,
                sa.Staff_Member_id,
                sa.Club_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name

            ORDER BY
                (sa.End_Date IS NULL) DESC,
                sa.Start_Date DESC
        """

        cursor.execute(query, params)
        assignments = cursor.fetchall()

        return render_template(
            "admin/staff_assignment/staff_assignment.html",
            Title="Staff Assignments",
            staff_members=staff_members,
            clubs=clubs,
            roles=roles,
            seasons=seasons,
            assignments=assignments,
            last_staff_member_id=last_staff_member_id,
            usma_club_id=USMA_CLUB_ID,
            search_staff_member=search_staff_member,
            search_club=search_club,
            role_filter=role_filter,
            status_filter=status_filter
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in staff assignment page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


@staff_assignment.route(
    "/staff-assignment/delete/<int:assignment_id>",
    methods=["POST"]
)
def delete_staff_assignment(assignment_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Staff_Assignment_Season rows are removed by ON DELETE CASCADE
        cursor.execute("""
            DELETE FROM Staff_Assignment
            WHERE Assignment_id = %s
        """, (assignment_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            return "Assignment not found", 404

        connection.commit()
        return redirect(url_for("staff_assignment.staff_assignment_page"))

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting staff assignment")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()