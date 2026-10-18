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
from app.utils import parse_date



edit_clubs = Blueprint(
    "edit_clubs",
    __name__,
    url_prefix="/admin/clubs"
)


# =====================================================
# EDIT CLUB - GET & POST
# =====================================================

@edit_clubs.route("/<int:club_id>/edit", methods=["GET", "POST"])
def edit_club_page(club_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Load the club first, for both GET and POST
        cursor.execute("""
            SELECT
                Club_id,
                Club_Current_Name,
                Club_Short_Name,
                City_id,
                Club_Founding_Date,
                Dissolution_Date,
                Club_Status
            FROM Club
            WHERE Club_id = %s
        """, (club_id,))

        club = cursor.fetchone()

        if club is None:
            return "Club not found", 404

        # =================================================
        # POST - Update Club
        # =================================================

        if request.method == "POST":
            club_current_name = (
                request.form.get("club_current_name") or ""
            ).strip()
            club_short_name = (
                request.form.get("club_short_name") or ""
            ).strip() or None
            city_id = request.form.get("city_id", type=int)
            club_status = (request.form.get("club_status") or "").strip()

            if not club_current_name:
                return "Club name is required", 400

            if city_id is None:
                return "Please select a city", 400

            if not club_status:
                return "Please select a club status", 400

            try:
                founding_date = parse_date(
                    request.form.get("club_founding_date")
                )
                dissolution_date = parse_date(
                    request.form.get("dissolution_date")
                )
            except ValueError as error:
                return str(error), 400

            if (founding_date and dissolution_date
                    and dissolution_date < founding_date):
                return "Dissolution date cannot be before founding date", 400

            try:
                cursor.execute("""
                    UPDATE Club
                    SET
                        Club_Current_Name = %s,
                        Club_Short_Name = %s,
                        City_id = %s,
                        Club_Founding_Date = %s,
                        Dissolution_Date = %s,
                        Club_Status = %s
                    WHERE Club_id = %s
                """, (
                    club_current_name,
                    club_short_name,
                    city_id,
                    founding_date,
                    dissolution_date,
                    club_status,
                    club_id
                ))
                connection.commit()

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate entry
                    return "This club already exists", 400
                if error.errno == 1452:      # foreign key failure
                    return "Invalid city", 400
                raise

            return redirect(
                url_for("edit_clubs.edit_club_page", club_id=club_id)
            )

        # =================================================
        # GET - Load Cities
        # =================================================

        cursor.execute("""
            SELECT City_id, City_Name
            FROM City
            ORDER BY City_Name
        """)
        cities = cursor.fetchall()

        return render_template(
            "admin/clubs/edit_club.html",
            Title="Edit Club",
            club=club,
            cities=cities
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while editing club")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# DELETE CLUB
# =====================================================

@edit_clubs.route("/<int:club_id>/delete", methods=["POST"])
def delete_club(club_id):
    # The main club of the archive must never be deleted
    if club_id == USMA_CLUB_ID:
        return "The USMA club cannot be deleted", 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM Player_Club WHERE Club_id = %s)
              + (SELECT COUNT(*) FROM Player_Season WHERE Club_id = %s)
              + (SELECT COUNT(*) FROM Staff_Assignment WHERE Club_id = %s)
                AS total
        """, (club_id, club_id, club_id))

        if cursor.fetchone()["total"] > 0:
            return (
                "Cannot delete this club because it has associated "
                "player or staff records.",
                400
            )

        cursor.execute("""
            DELETE FROM Club
            WHERE Club_id = %s
        """, (club_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            return "Club not found", 404

        connection.commit()
        return redirect(url_for("clubs.clubs_page"))

    except IntegrityError as error:
        connection.rollback()
        if error.errno == 1451:      # still referenced elsewhere
            return (
                "Cannot delete this club because other records "
                "still reference it.",
                400
            )
        current_app.logger.exception("Error while deleting club")
        return "Something went wrong", 500

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error while deleting club")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()