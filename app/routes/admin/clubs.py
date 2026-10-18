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
from app.utils import escape_like, parse_date

clubs = Blueprint("clubs", __name__)


@clubs.route("/clubs", methods=["GET", "POST"])
def clubs_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
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
                founding_date = parse_date(request.form.get("founding_date"))
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
                    INSERT INTO Club (
                        Club_Current_Name,
                        Club_Short_Name,
                        City_id,
                        Club_Founding_Date,
                        Dissolution_Date,
                        Club_Status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    club_current_name,
                    club_short_name,
                    city_id,
                    founding_date,
                    dissolution_date,
                    club_status
                ))
                connection.commit()

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate entry
                    return "This club already exists", 400
                if error.errno == 1452:      # foreign key failure
                    return "Invalid city", 400
                raise

            return redirect(url_for("clubs.clubs_page"))

        # ========================================
        # GET
        # ========================================

        search = request.args.get("search", "").strip()
        status_filter = request.args.get("status_filter", "").strip()

        cursor.execute("""
            SELECT City_id, City_Name, Country_id
            FROM City
            ORDER BY City_Name
        """)
        city_list = cursor.fetchall()

        # Only fixed SQL fragments are added here; values go in params
        conditions = []
        params = []

        if search:
            conditions.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{escape_like(search)}%")

        if status_filter:
            conditions.append("c.Club_Status = %s")
            params.append(status_filter)

        query = """
            SELECT
                c.Club_id,
                c.Club_Current_Name,
                c.Club_Short_Name,
                c.City_id,
                c.Club_Founding_Date,
                c.Dissolution_Date,
                c.Club_Status,
                ci.City_Name
            FROM Club c
            LEFT JOIN City ci
                ON c.City_id = ci.City_id
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY c.Club_Current_Name"

        cursor.execute(query, params)
        club_list = cursor.fetchall()

        return render_template(
            "admin/clubs/clubs.html",
            Title="Clubs",
            cities=city_list,
            clubs=club_list,
            search=search,
            status_filter=status_filter
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in clubs page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()