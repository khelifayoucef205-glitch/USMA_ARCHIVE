from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from mysql.connector import IntegrityError

from app.database import get_db_connection
from app.routes.admin.person_utils import update_person
from app.routes.admin.staff_assignment_utils import (
    clean_season_ids,
    has_overlap,
    parse_date,
    valid_role_ids,
)

edit_staff_member = Blueprint("edit_staff_member", __name__)


@edit_staff_member.route(
    "/staff-member/<int:staff_member_id>/edit",
    methods=["GET", "POST"]
)
def edit_staff_member_page(staff_member_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =========================================================
        # LOAD STAFF MEMBER
        # =========================================================

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
                p.Country_id,

                sm.Staff_Member_id,
                sm.Specialty

            FROM Staff_Member sm

            JOIN Person p
                ON sm.Person_id = p.Person_id

            WHERE sm.Staff_Member_id = %s
        """, (staff_member_id,))

        staff_data = cursor.fetchone()

        if staff_data is None:
            return "Staff Member not found", 404

        edit_url = url_for(
            "edit_staff_member.edit_staff_member_page",
            staff_member_id=staff_member_id
        )

        # =========================================================
        # POST
        # =========================================================

        if request.method == "POST":
            action = request.form.get("action")

            try:

                # -------------------------------------------------
                # UPDATE PERSON
                # -------------------------------------------------

                if action == "update_person":

                    try:
                        update_person(
                            cursor, staff_data["Person_id"], request.form
                        )
                    except ValueError as error:
                        return str(error), 400

                    connection.commit()
                    return redirect(edit_url)

                # -------------------------------------------------
                # UPDATE STAFF INFO (specialty + career roles)
                # -------------------------------------------------

                elif action == "update_staff_member":

                    specialty = (
                        request.form.get("specialty") or ""
                    ).strip() or None
                    main_role_id = request.form.get("role_id", type=int)

                    if main_role_id is None or not valid_role_ids(
                        cursor, [main_role_id]
                    ):
                        return "Please select a valid main role", 400

                    other_valid = valid_role_ids(
                        cursor, request.form.getlist("other_role_ids")
                    )
                    other_valid.discard(main_role_id)

                    cursor.execute("""
                        UPDATE Staff_Member
                        SET Specialty = %s
                        WHERE Staff_Member_id = %s
                    """, (specialty, staff_member_id))

                    cursor.execute("""
                        DELETE FROM Staff_Member_Role
                        WHERE Staff_Member_id = %s
                    """, (staff_member_id,))

                    cursor.execute("""
                        INSERT INTO Staff_Member_Role
                            (Staff_Member_id, Role_id, Is_Main)
                        VALUES (%s, %s, TRUE)
                    """, (staff_member_id, main_role_id))

                    for role_id in sorted(other_valid):
                        cursor.execute("""
                            INSERT INTO Staff_Member_Role
                                (Staff_Member_id, Role_id, Is_Main)
                            VALUES (%s, %s, FALSE)
                        """, (staff_member_id, role_id))

                    connection.commit()
                    return redirect(edit_url)

                # -------------------------------------------------
                # ADD ASSIGNMENT
                # -------------------------------------------------

                elif action == "add_assignment":

                    club_id = request.form.get("club_id", type=int)
                    role_id = request.form.get("assignment_role_id", type=int)

                    if club_id is None:
                        return "Club is required", 400

                    if role_id is None or not valid_role_ids(cursor, [role_id]):
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
                        return ("This person already has an overlapping "
                                "assignment with the same club and role"), 400

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
                    """, (staff_member_id, club_id, role_id,
                          start_date, end_date))

                    assignment_id = cursor.lastrowid

                    for season_number in season_ids:
                        cursor.execute("""
                            INSERT INTO Staff_Assignment_Season
                                (Assignment_id, Season_Number)
                            VALUES (%s, %s)
                        """, (assignment_id, season_number))

                    connection.commit()
                    return redirect(edit_url)

                # -------------------------------------------------
                # DELETE ASSIGNMENT
                # -------------------------------------------------

                elif action == "delete_assignment":

                    assignment_id = request.form.get("assignment_id", type=int)

                    if assignment_id is None:
                        return "Assignment is required", 400

                    # Only delete assignments that belong to this member
                    cursor.execute("""
                        DELETE FROM Staff_Assignment
                        WHERE Assignment_id = %s
                          AND Staff_Member_id = %s
                    """, (assignment_id, staff_member_id))

                    if cursor.rowcount == 0:
                        connection.rollback()
                        return "Assignment not found", 404

                    connection.commit()
                    return redirect(edit_url)

                else:
                    return "Unknown action", 400

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1452:      # foreign key failure
                    return "Invalid club or role", 400
                raise

        # =========================================================
        # GET
        # =========================================================

        cursor.execute("""
            SELECT Country_id, Country_Name
            FROM Country
            ORDER BY Country_Name
        """)
        countries = cursor.fetchall()

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

        # Career roles
        cursor.execute("""
            SELECT Role_id, Is_Main
            FROM Staff_Member_Role
            WHERE Staff_Member_id = %s
        """, (staff_member_id,))

        main_role_id = None
        other_role_ids = []

        for row in cursor.fetchall():
            if row["Is_Main"] and main_role_id is None:
                main_role_id = row["Role_id"]
            else:
                other_role_ids.append(row["Role_id"])

        # Assignments
        cursor.execute("""
            SELECT
                sa.Assignment_id,
                sa.Start_Date,
                sa.End_Date,
                c.Club_Current_Name,
                sr.Role_name,
                GROUP_CONCAT(s.Season_Name ORDER BY s.Start_Year SEPARATOR ', ') AS Seasons

            FROM Staff_Assignment sa

            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
            LEFT JOIN Staff_Assignment_Season sas ON sas.Assignment_id = sa.Assignment_id
            LEFT JOIN Season s ON s.Season_Number = sas.Season_Number

            WHERE sa.Staff_Member_id = %s

            GROUP BY
                sa.Assignment_id,
                sa.Start_Date,
                sa.End_Date,
                c.Club_Current_Name,
                sr.Role_name

            ORDER BY
                (sa.End_Date IS NULL) DESC,
                sa.Start_Date DESC
        """, (staff_member_id,))

        assignments = cursor.fetchall()

        return render_template(
            "admin/staff_members/edit_staff_member.html",
            Title="Edit Staff Member",
            staff_member=staff_data,
            countries=countries,
            clubs=clubs,
            roles=roles,
            seasons=seasons,
            main_role_id=main_role_id,
            other_role_ids=other_role_ids,
            assignments=assignments
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in edit staff member page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()