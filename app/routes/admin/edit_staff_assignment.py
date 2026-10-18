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
from app.routes.admin.staff_assignment_utils import (
    clean_season_ids,
    has_overlap,
    parse_date,
    valid_role_ids,
)

edit_staff_assignment = Blueprint(
    "edit_staff_assignment",
    __name__,
    url_prefix="/admin/staff-assignment"
)


@edit_staff_assignment.route("/<int:assignment_id>/edit", methods=["GET", "POST"])
def edit_staff_assignment_page(assignment_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Load the assignment (needed for both GET and POST)
        cursor.execute("""
            SELECT
                sa.Assignment_id,
                sa.Staff_Member_id,
                sa.Club_id,
                sa.Role_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name

            FROM Staff_Assignment sa

            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id

            WHERE sa.Assignment_id = %s
        """, (assignment_id,))

        assignment = cursor.fetchone()

        if assignment is None:
            return "Assignment not found", 404

        # =================================================
        # POST - Update
        # =================================================

        if request.method == "POST":
            new_club_id = request.form.get("club_id", type=int)
            new_role_id = request.form.get("role_id", type=int)

            if new_club_id is None or new_role_id is None:
                return "Club and role are required", 400

            if not valid_role_ids(cursor, [new_role_id]):
                return "Please select a valid role", 400

            try:
                new_start = parse_date(request.form.get("start_date"))
                new_end = parse_date(request.form.get("end_date"))
            except ValueError as error:
                return str(error), 400

            if not new_start:
                return "Start date is required", 400

            if new_end and new_end < new_start:
                return "End date cannot be before Start date", 400

            if has_overlap(cursor, assignment["Staff_Member_id"], new_club_id,
                           new_role_id, new_start, new_end,
                           exclude_id=assignment_id):
                return ("This person already has an overlapping assignment "
                        "with the same club and role"), 400

            season_ids = clean_season_ids(
                cursor, request.form.getlist("season_ids")
            )

            try:
                cursor.execute("""
                    UPDATE Staff_Assignment
                    SET Club_id = %s,
                        Role_id = %s,
                        Start_Date = %s,
                        End_Date = %s
                    WHERE Assignment_id = %s
                """, (new_club_id, new_role_id, new_start, new_end,
                      assignment_id))

                # Replace the seasons
                cursor.execute("""
                    DELETE FROM Staff_Assignment_Season
                    WHERE Assignment_id = %s
                """, (assignment_id,))

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
                    return "Invalid club or role", 400
                raise

            return redirect(url_for("staff_assignment.staff_assignment_page"))

        # =================================================
        # GET
        # =================================================

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

        cursor.execute("""
            SELECT Season_Number
            FROM Staff_Assignment_Season
            WHERE Assignment_id = %s
        """, (assignment_id,))
        selected_seasons = [row["Season_Number"] for row in cursor.fetchall()]

        return render_template(
            "admin/staff_assignment/edit_staff_assignment.html",
            Title="Edit Staff Assignment",
            assignment=assignment,
            clubs=clubs,
            roles=roles,
            seasons=seasons,
            selected_seasons=selected_seasons
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while editing staff assignment")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()