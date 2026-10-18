from datetime import date

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
from app.utils import escape_like

staff_assignment_season = Blueprint(
    "staff_assignment_season",
    __name__,
    url_prefix="/admin/staff-assignment-season"
)

def season_outside_range(assignment, season):
    """True if the assignment's years do not overlap the season's years."""
    if season["Start_Year"] is None or season["End_Year"] is None:
        return False

    start_year = assignment["Start_Date"].year
    end_year = (
        assignment["End_Date"].year
        if assignment["End_Date"]
        else date.today().year
    )

    return end_year < season["Start_Year"] or start_year > season["End_Year"]


def load_assignment(cursor, assignment_id):
    cursor.execute("""
        SELECT Assignment_id, Start_Date, End_Date
        FROM Staff_Assignment
        WHERE Assignment_id = %s
    """, (assignment_id,))
    return cursor.fetchone()


def load_season(cursor, season_number):
    cursor.execute("""
        SELECT Season_Number, Season_Name, Start_Year, End_Year
        FROM Season
        WHERE Season_Number = %s
    """, (season_number,))
    return cursor.fetchone()


# =====================================================
# CREATE & READ
# =====================================================

@staff_assignment_season.route("/", methods=["GET", "POST"])
def staff_assignment_season_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Link assignment to season
        # =================================================

        if request.method == "POST":
            assignment_id = request.form.get("assignment_id", type=int)
            season_number = request.form.get("season_number", type=int)
            confirm_outside = request.form.get("confirm_outside")

            if assignment_id is None or season_number is None:
                return "Assignment and season are required", 400

            assignment = load_assignment(cursor, assignment_id)
            season = load_season(cursor, season_number)

            if assignment is None or season is None:
                return "Assignment or season not found", 404

            cursor.execute("""
                SELECT 1
                FROM Staff_Assignment_Season
                WHERE Assignment_id = %s
                  AND Season_Number = %s
            """, (assignment_id, season_number))

            if cursor.fetchone():
                return "This assignment is already linked to this season", 400

            if season_outside_range(assignment, season) and not confirm_outside:
                return (
                    "This season does not overlap the assignment dates. "
                    "Tick 'Confirm outside range' if this is intentional.",
                    400
                )

            try:
                cursor.execute("""
                    INSERT INTO Staff_Assignment_Season (Assignment_id, Season_Number)
                    VALUES (%s, %s)
                """, (assignment_id, season_number))
                connection.commit()

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate (race condition)
                    return "This assignment is already linked to this season", 400
                raise

            return redirect(
                url_for("staff_assignment_season.staff_assignment_season_page")
            )

        # =================================================
        # GET
        # =================================================

        search_staff_member = request.args.get("search_staff_member", "").strip()
        search_club = request.args.get("search_club", "").strip()
        season_filter = request.args.get("season_filter", "").strip()
        role_filter = request.args.get("role_filter", "").strip()

        # All assignments (for the add form dropdown)
        cursor.execute("""
            SELECT
                sa.Assignment_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name

            FROM Staff_Assignment sa

            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id

            ORDER BY p.Person_Display_Name, sa.Start_Date DESC
        """)
        assignments = cursor.fetchall()

        cursor.execute("""
            SELECT Season_Number, Season_Name, Start_Year, End_Year
            FROM Season
            ORDER BY Start_Year DESC, Season_Number DESC
        """)
        seasons = cursor.fetchall()

        cursor.execute("""
            SELECT Role_id, Role_name
            FROM Staff_Role
            ORDER BY Role_id
        """)
        roles = cursor.fetchall()

        # Only fixed SQL fragments are added here; values go in params
        conditions = []
        params = []

        if search_staff_member:
            conditions.append("p.Person_Display_Name LIKE %s")
            params.append(f"%{escape_like(search_staff_member)}%")

        if search_club:
            conditions.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{escape_like(search_club)}%")

        if season_filter.isdigit():
            conditions.append("sas.Season_Number = %s")
            params.append(int(season_filter))

        if role_filter.isdigit():
            conditions.append("sa.Role_id = %s")
            params.append(int(role_filter))

        query = """
            SELECT
                sas.Assignment_id,
                sas.Season_Number,
                s.Season_Name,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name

            FROM Staff_Assignment_Season sas

            JOIN Staff_Assignment sa ON sas.Assignment_id = sa.Assignment_id
            JOIN Season s ON sas.Season_Number = s.Season_Number
            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            ORDER BY
                sa.Start_Date DESC,
                s.Start_Year DESC,
                p.Person_Display_Name
        """

        cursor.execute(query, params)
        links = cursor.fetchall()

        return render_template(
            "admin/staff_assignment_season/staff_assignment_season.html",
            Title="Staff Assignment Seasons",
            assignments=assignments,
            seasons=seasons,
            roles=roles,
            links=links,
            search_staff_member=search_staff_member,
            search_club=search_club,
            season_filter=season_filter,
            role_filter=role_filter
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in staff assignment season page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# EDIT (change the season of an existing link)
# =====================================================

@staff_assignment_season.route(
    "/<int:assignment_id>/<int:season_number>/edit",
    methods=["GET", "POST"]
)
def edit_staff_assignment_season(assignment_id, season_number):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                sas.Assignment_id,
                sas.Season_Number,
                s.Season_Name,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name

            FROM Staff_Assignment_Season sas

            JOIN Staff_Assignment sa ON sas.Assignment_id = sa.Assignment_id
            JOIN Season s ON sas.Season_Number = s.Season_Number
            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id

            WHERE sas.Assignment_id = %s
              AND sas.Season_Number = %s
        """, (assignment_id, season_number))

        link = cursor.fetchone()

        if link is None:
            return "Assignment-season record not found", 404

        # =================================================
        # POST - Update
        # =================================================

        if request.method == "POST":
            new_season_number = request.form.get("season_number", type=int)
            confirm_outside = request.form.get("confirm_outside")

            if new_season_number is None:
                return "Season is required", 400

            new_season = load_season(cursor, new_season_number)

            if new_season is None:
                return "Season not found", 404

            if new_season_number != season_number:

                cursor.execute("""
                    SELECT 1
                    FROM Staff_Assignment_Season
                    WHERE Assignment_id = %s
                      AND Season_Number = %s
                """, (assignment_id, new_season_number))

                if cursor.fetchone():
                    return "This assignment is already linked to that season", 400

                assignment = load_assignment(cursor, assignment_id)

                if season_outside_range(assignment, new_season) and not confirm_outside:
                    return (
                        "This season does not overlap the assignment dates. "
                        "Tick 'Confirm outside range' if this is intentional.",
                        400
                    )

                try:
                    cursor.execute("""
                        UPDATE Staff_Assignment_Season
                        SET Season_Number = %s
                        WHERE Assignment_id = %s
                          AND Season_Number = %s
                    """, (new_season_number, assignment_id, season_number))
                    connection.commit()

                except IntegrityError as error:
                    connection.rollback()
                    if error.errno == 1062:  # duplicate (race condition)
                        return "This assignment is already linked to that season", 400
                    raise

            return redirect(
                url_for("staff_assignment_season.staff_assignment_season_page")
            )

        # =================================================
        # GET
        # =================================================

        cursor.execute("""
            SELECT Season_Number, Season_Name, Start_Year, End_Year
            FROM Season
            ORDER BY Start_Year DESC, Season_Number DESC
        """)
        seasons = cursor.fetchall()

        return render_template(
            "admin/staff_assignment_season/edit_staff_assignment_season.html",
            Title="Edit Assignment Season",
            link=link,
            seasons=seasons
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while editing assignment season")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# DELETE (unlink only)
# =====================================================

@staff_assignment_season.route(
    "/<int:assignment_id>/<int:season_number>/delete",
    methods=["POST"]
)
def delete_staff_assignment_season(assignment_id, season_number):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM Staff_Assignment_Season
            WHERE Assignment_id = %s
              AND Season_Number = %s
        """, (assignment_id, season_number))

        if cursor.rowcount == 0:
            connection.rollback()
            return "Assignment-season record not found", 404

        connection.commit()
        return redirect(
            url_for("staff_assignment_season.staff_assignment_season_page")
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting assignment season")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()