from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection
from app.utils import parse_date
from app.routes.admin.staff_assignment_utils import  valid_role_ids
from app.routes.admin.person_utils import create_person


add_staff_member = Blueprint("add_staff_member", __name__)


@add_staff_member.route("/add-staff-member", methods=["GET", "POST"])
def add_staff_member_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        if request.method == "POST":

            person_source = request.form.get("person_source", "new")
            existing_person_id = request.form.get("existing_person_id")

            role_id = request.form.get("role_id")
            specialty = request.form.get("specialty") or None

            if not valid_role_ids(cursor, [role_id]):
                return "Please select a valid role", 400

            # --------------------------------
            # Existing Person
            # --------------------------------

            if person_source == "existing":

                if not existing_person_id:
                    return "Please select an existing person", 400

                cursor.execute("""
                    SELECT p.Person_id
                    FROM Person p
                    LEFT JOIN Staff_Member sm
                        ON p.Person_id = sm.Person_id
                    WHERE p.Person_id = %s
                      AND sm.Staff_Member_id IS NULL
                """, (existing_person_id,))

                person = cursor.fetchone()

                if person is None:
                    return "Invalid person or person is already a staff member", 400

                person_id = person["Person_id"]

            # --------------------------------
            # New Person
            # --------------------------------

            else:
                try:
                    person_id = create_person(cursor, request.form)
                except ValueError as error:
                    return str(error), 400

                if not display_name:
                    return "Display name is required", 400

                cursor.execute("""
                    INSERT INTO Person (
                        Person_First_Name,
                        Person_Last_Name,
                        Person_Display_Name,
                        Person_First_Name_ar,
                        Person_Last_Name_ar,
                        Person_Display_Name_ar,
                        Person_birth_date,
                        Person_death_date,
                        Sex,
                        Country_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    first_name,
                    last_name,
                    display_name,
                    first_name_ar,
                    last_name_ar,
                    display_name_ar,
                    birth_date,
                    death_date,
                    sex,
                    country_id
                ))

                person_id = cursor.lastrowid

            # --------------------------------
            # Staff Member + main career role
            # --------------------------------

            cursor.execute("""
                INSERT INTO Staff_Member (Person_id, Specialty)
                VALUES (%s, %s)
            """, (person_id, specialty))

            staff_member_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Staff_Member_Role (Staff_Member_id, Role_id, Is_Main)
                VALUES (%s, %s, TRUE)
            """, (staff_member_id, role_id))

            connection.commit()

            return redirect(url_for("staff_members.staff_members_page"))

        # ========================================
        # GET
        # ========================================

        cursor.execute("""
            SELECT Country_id, Country_Name
            FROM Country
            ORDER BY Country_Name
        """)
        countries = cursor.fetchall()

        cursor.execute("""
            SELECT Role_id, Role_name
            FROM Staff_Role
            ORDER BY Role_id
        """)
        roles = cursor.fetchall()

        cursor.execute("""
            SELECT
                p.Person_id,
                p.Person_Display_Name,
                p.Person_Display_Name_ar,

                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM Player pl
                        WHERE pl.Person_id = p.Person_id
                    )
                    THEN 1
                    ELSE 0
                END AS is_player

            FROM Person p

            WHERE NOT EXISTS (
                SELECT 1
                FROM Staff_Member sm
                WHERE sm.Person_id = p.Person_id
            )

            ORDER BY p.Person_Display_Name
        """)
        existing_persons = cursor.fetchall()

        return render_template(
            "admin/staff_members/add_staff_member.html",
            Title="Add Staff Member",
            countries=countries,
            roles=roles,
            existing_persons=existing_persons
        )

    except Exception as error:

        connection.rollback()

        print("Error while adding staff member:", error)

        return "Error while adding staff member", 500

    finally:

        cursor.close()
        connection.close()