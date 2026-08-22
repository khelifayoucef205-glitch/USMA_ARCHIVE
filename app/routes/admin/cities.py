from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection


cities = Blueprint("cities", __name__)


@cities.route("/cities", methods=["GET", "POST"])
def cities_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        city_name = request.form.get("city_name")
        city_name_ar = request.form.get("city_name_ar")
        country_id = request.form.get("country_id")

        cursor.execute("""
            INSERT INTO City (
                City_Name,
                City_Name_ar,
                Country_id
            )
            VALUES (%s, %s, %s)
        """, (
            city_name,
            city_name_ar,
            country_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("cities.cities_page"))


    # Load countries
    cursor.execute("""
        SELECT Country_id, Country_Name
        FROM Country
        ORDER BY Country_Name
    """)

    countries = cursor.fetchall()


    # Load cities
    cursor.execute("""
        SELECT
            c.City_id,
            c.City_Name,
            c.City_Name_ar,
            c.Country_id,
            co.Country_Name
        FROM City c
        JOIN Country co
            ON c.Country_id = co.Country_id
        ORDER BY c.City_Name
    """)

    city_list = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "admin/cities/cities.html",
        Title="Cities",
        countries=countries,
        cities=city_list
    )