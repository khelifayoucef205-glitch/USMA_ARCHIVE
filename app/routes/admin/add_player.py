from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection


add_player = Blueprint("add_player", __name__)


@add_player.route("/add-player", methods=["GET", "POST"])
def add_player_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        try:

            # Person information
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            display_name = request.form.get("display_name")

            first_name_ar = request.form.get("first_name_ar")
            last_name_ar = request.form.get("last_name_ar")
            display_name_ar = request.form.get("display_name_ar")

            birth_date = request.form.get("birth_date") or None
            sex = request.form.get("sex")
            country_id = request.form.get("country_id")

            # Player information
            position_id = request.form.get("position_id")
            nickname = request.form.get("nickname")
            nickname_ar = request.form.get("nickname_ar")
            jersey_number = request.form.get("jersey_number") or None

            is_active = 1 if request.form.get("is_active") else 0


            # Create Person
            cursor.execute("""
                INSERT INTO Person (
                    Person_First_Name,
                    Person_Last_Name,
                    Person_Display_Name,
                    Person_First_Name_ar,
                    Person_Last_Name_ar,
                    Person_Display_Name_ar,
                    Person_birth_date,
                    Sex,
                    Country_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                first_name,
                last_name,
                display_name,
                first_name_ar,
                last_name_ar,
                display_name_ar,
                birth_date,
                sex,
                country_id
            ))

            person_id = cursor.lastrowid


            # Create Player
            cursor.execute("""
                INSERT INTO Player (
                    Person_id,
                    Player_Nickname,
                    Player_Nickname_ar,
                    Main_Jersey_Number,
                    Is_Active
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                person_id,
                nickname,
                nickname_ar,
                jersey_number,
                is_active
            ))

            player_id = cursor.lastrowid


            # Create Player Position
            cursor.execute("""
                INSERT INTO Player_Position (
                    Player_id,
                    Position_id,
                    Is_Main
                )
                VALUES (%s, %s, %s)
            """, (
                player_id,
                position_id,
                1
            ))


            # Everything succeeded
            connection.commit()

            return redirect(url_for("main.home"))


        except Exception as error:

            # Something failed → undo everything
            connection.rollback()

            print("Error while adding player:", error)

            return "Error while adding player", 500


        finally:

            cursor.close()
            connection.close()


    # GET request → load countries
    cursor.execute("""
        SELECT Country_id, Country_Name
        FROM Country
        ORDER BY Country_Name
    """)

    countries = cursor.fetchall()


    cursor.execute("""
        SELECT Position_id, Position_Code, Position_Name
        FROM Position
        ORDER BY Position_Category_id, Position_id
    """)

    positions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin/players/add_player.html",
        Title="Add Player",
        countries=countries,
        positions=positions
    )