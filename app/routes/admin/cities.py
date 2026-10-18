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

cities = Blueprint("cities", __name__)



@cities.route("/cities", methods=["GET", "POST"])
def cities_page():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if request.method == "POST":
            city_name = (request.form.get("city_name") or "").strip()
            city_name_ar = (request.form.get("city_name_ar") or "").strip() or None
            country_id = request.form.get("country_id", type=int)

            if not city_name:
                return "City name is required", 400

            if country_id is None:
                return "Please select a country", 400

            try:
                cursor.execute("""
                    INSERT INTO City (City_Name, City_Name_ar, Country_id)
                    VALUES (%s, %s, %s)
                """, (city_name, city_name_ar, country_id))
                connection.commit()

            except IntegrityError as error:
                connection.rollback()
                if error.errno == 1062:      # duplicate entry
                    return "This city already exists", 400
                if error.errno == 1452:      # foreign key failure
                    return "Invalid country", 400
                raise

            return redirect(url_for("cities.cities_page"))

        # ========================================
        # GET
        # ========================================

        search = request.args.get("search", "").strip()

        cursor.execute("""
            SELECT Country_id, Country_Name
            FROM Country
            ORDER BY Country_Name
        """)
        countries = cursor.fetchall()

        query = """
            SELECT
                c.City_id,
                c.City_Name,
                c.City_Name_ar,
                c.Country_id,
                co.Country_Name
            FROM City c
            LEFT JOIN Country co
                ON c.Country_id = co.Country_id
        """
        params = []

        if search:
            pattern = f"%{escape_like(search)}%"
            query += " WHERE c.City_Name LIKE %s OR c.City_Name_ar LIKE %s"
            params = [pattern, pattern]

        query += " ORDER BY c.City_Name"

        cursor.execute(query, params)
        city_list = cursor.fetchall()

        return render_template(
            "admin/cities/cities.html",
            Title="Cities",
            countries=countries,
            cities=city_list,
            search=search
        )

    except Exception:
        connection.rollback()
        current_app.logger.exception("Error in cities page")
        return "Something went wrong", 500

    finally:
        cursor.close()
        connection.close()