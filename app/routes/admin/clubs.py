from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection


clubs = Blueprint("clubs", __name__)


@clubs.route("/clubs", methods=["GET", "POST"])
def clubs_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        club_current_name = request.form.get("club_current_name")
        club_short_name = request.form.get("club_short_name")
        city_id = request.form.get("city_id")

        founding_date = request.form.get("founding_date") or None
        dissolution_date = request.form.get("dissolution_date") or None
        club_status = request.form.get("club_status")

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

        cursor.close()
        connection.close()

        return redirect(url_for("clubs.clubs_page"))

    # Get filter parameters
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status_filter", "")

    # Load cities
    cursor.execute("""
        SELECT
            City_id,
            City_Name,
            Country_id
        FROM City
        ORDER BY City_Name
    """)

    cities = cursor.fetchall()

    # Build WHERE clause for clubs
    where_clauses = []
    params = []

    if search:
        where_clauses.append("c.Club_Current_Name LIKE %s")
        params.append(f"%{search}%")

    if status_filter:
        where_clauses.append("c.Club_Status = %s")
        params.append(status_filter)

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Load clubs with filters
    query = f"""
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
        JOIN City ci
            ON c.City_id = ci.City_id
        WHERE {where_clause}
        ORDER BY c.Club_Current_Name
    """

    cursor.execute(query, params)
    club_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin/clubs/clubs.html",
        Title="Clubs",
        cities=cities,
        clubs=club_list,
        search=search,
        status_filter=status_filter
    )