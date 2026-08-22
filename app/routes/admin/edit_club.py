from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection

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

        # =================================================
        # POST - Update Club
        # =================================================

        if request.method == "POST":

            club_current_name = request.form.get("club_current_name")
            club_short_name = request.form.get("club_short_name")
            city_id = request.form.get("city_id")

            founding_date = (
                request.form.get("club_founding_date")
                or None
            )

            dissolution_date = (
                request.form.get("dissolution_date")
                or None
            )

            club_status = request.form.get("club_status")

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

            return redirect(
                url_for(
                    "edit_clubs.edit_club_page",
                    club_id=club_id
                )
            )

        # =================================================
        # GET - Load Club
        # =================================================

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
        # Load Cities
        # =================================================

        cursor.execute("""
            SELECT
                City_id,
                City_Name
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

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# DELETE CLUB
# =====================================================

@edit_clubs.route("/<int:club_id>/delete", methods=["POST"])
def delete_club(club_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # Check Player_Club
        # =================================================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Club
            WHERE Club_id = %s
        """, (club_id,))

        player_club_count = cursor.fetchone()["count"]

        # =================================================
        # Check Player_Season
        # =================================================

        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM Player_Season
            WHERE Club_id = %s
        """, (club_id,))

        player_season_count = cursor.fetchone()["count"]

        # =================================================
        # Prevent deletion if referenced
        # =================================================

        if player_club_count > 0 or player_season_count > 0:
            return (
                "Cannot delete this club because it "
                "has associated player records.",
                400
            )

        # =================================================
        # Delete Club
        # =================================================

        cursor.execute("""
            DELETE FROM Club
            WHERE Club_id = %s
        """, (club_id,))

        connection.commit()

        # =================================================
        # Redirect
        # =================================================

        return redirect(url_for("clubs.clubs_page"))

    except Exception as error:
        connection.rollback()
        return f"Error deleting club: {error}", 500

    finally:
        cursor.close()
        connection.close()