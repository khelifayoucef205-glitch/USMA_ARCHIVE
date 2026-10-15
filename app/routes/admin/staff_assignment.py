from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection
from app.routes.admin.staff_assignment_utils import parse_date, has_overlap, clean_season_ids

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

            staff_member_id = request.form.get("staff_member_id")
            club_id = request.form.get("club_id")
            role_id = request.form.get("role_id")

            try:
                start_date = parse_date(request.form.get("start_date"))
                end_date = parse_date(request.form.get("end_date"))
            except ValueError as error:
                return str(error), 400

            if not (staff_member_id and club_id and role_id):
                return "Staff member, club and role are required", 400

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
                    INSERT INTO Staff_Assignment_Season (Assignment_id, Season_Number)
                    VALUES (%s, %s)
                """, (assignment_id, season_number))

            connection.commit()

            return redirect(url_for("staff_assignment.staff_assignment_page"))

        # =================================================
        # GET
        # =================================================

        search_staff_member = request.args.get("search_staff_member", "").strip()
        search_club = request.args.get("search_club", "").strip()
        role_filter = request.args.get("role_filter", "")
        status_filter = request.args.get("status_filter", "")

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

        # USMA club id
        cursor.execute("""
            SELECT Club_id
            FROM Club
            WHERE Club_Current_Name = 'USM Alger'
            LIMIT 1
        """)
        usma_club = cursor.fetchone()
        usma_club_id = usma_club["Club_id"] if usma_club else 1

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

        # Filters
        where_clauses = []
        params = []

        if search_staff_member:
            where_clauses.append("p.Person_Display_Name LIKE %s")
            params.append(f"%{search_staff_member}%")

        if search_club:
            where_clauses.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{search_club}%")

        if role_filter and role_filter.isdigit():
            where_clauses.append("sa.Role_id = %s")
            params.append(int(role_filter))

        if status_filter == "current":
            where_clauses.append("sa.End_Date IS NULL")
        elif status_filter == "former":
            where_clauses.append("sa.End_Date IS NOT NULL")

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
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

            WHERE {where_clause}

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
            usma_club_id=usma_club_id,
            search_staff_member=search_staff_member,
            search_club=search_club,
            role_filter=role_filter,
            status_filter=status_filter
        )

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()


@staff_assignment.route("/staff-assignment/delete/<int:assignment_id>", methods=["POST"])
def delete_staff_assignment(assignment_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Staff_Assignment_Season rows are removed by ON DELETE CASCADE
        cursor.execute("""
            DELETE FROM Staff_Assignment
            WHERE Assignment_id = %s
        """, (assignment_id,))

        connection.commit()

    except Exception as error:
        connection.rollback()
        return f"Error deleting: {error}", 500

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("staff_assignment.staff_assignment_page"))