from flask import Blueprint, render_template
from app.database import get_db_connection
from datetime import datetime

staff_member = Blueprint("staff_member", __name__)


def get_staff_member_status(staff_member_data):

    if staff_member_data.get('Person_death_date'):
        return 'deceased'

    if staff_member_data.get('usma_current'):
        return 'active_with_usma'

    if staff_member_data.get('usma_history'):
        return 'former_usma'

    return 'no_club'


def calculate_age(birth_date, death_date=None):
    if not birth_date:
        return None

    reference_date = death_date if death_date else datetime.now().date()

    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    if isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()

    return reference_date.year - birth_date.year - (
        (reference_date.month, reference_date.day)
        < (birth_date.month, birth_date.day)
    )


@staff_member.route("/staff-member/<int:staff_member_id>")
def staff_member_page(staff_member_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # 1. Basic data
        cursor.execute("""
            SELECT
                p.Person_id,
                p.Person_First_Name,
                p.Person_Last_Name,
                p.Person_Display_Name,
                p.Person_First_Name_ar,
                p.Person_Last_Name_ar,
                p.Person_Display_Name_ar,
                p.Person_birth_date,
                p.Person_death_date,
                p.Sex,
                c.Country_Name,
                c.Country_Name_ar,

                sm.Staff_Member_id,
                sm.Specialty

            FROM Staff_Member sm
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Country c ON p.Country_id = c.Country_id
            WHERE sm.Staff_Member_id = %s
        """, (staff_member_id,))

        staff_data = cursor.fetchone()

        if staff_data is None:
            return "Staff Member not found", 404

        # 2. Career roles (main first)
        cursor.execute("""
            SELECT sr.Role_name, smr.Is_Main
            FROM Staff_Member_Role smr
            JOIN Staff_Role sr ON smr.Role_id = sr.Role_id
            WHERE smr.Staff_Member_id = %s
            ORDER BY smr.Is_Main DESC, sr.Role_id
        """, (staff_member_id,))

        career_roles = cursor.fetchall()

        main_role = None
        other_roles = []

        for role in career_roles:
            if role["Is_Main"] and main_role is None:
                main_role = role["Role_name"]
            else:
                other_roles.append(role["Role_name"])

        staff_data["Role"] = main_role

        # 3. USMA assignments (every period, with its seasons)
        cursor.execute("""
            SELECT
                sa.Assignment_id,
                sa.Start_Date,
                sa.End_Date,
                sr.Role_name,
                GROUP_CONCAT(s.Season_Name ORDER BY s.Start_Year SEPARATOR ', ') AS Seasons

            FROM Staff_Assignment sa
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
            LEFT JOIN Staff_Assignment_Season sas ON sas.Assignment_id = sa.Assignment_id
            LEFT JOIN Season s ON s.Season_Number = sas.Season_Number

            WHERE sa.Staff_Member_id = %s
              AND sa.Club_id = 1

            GROUP BY
                sa.Assignment_id,
                sa.Start_Date,
                sa.End_Date,
                sr.Role_name

            ORDER BY sa.Start_Date DESC
        """, (staff_member_id,))

        usma_assignments = cursor.fetchall()

        usma_current = [a for a in usma_assignments if a["End_Date"] is None]
        usma_history = [a for a in usma_assignments if a["End_Date"] is not None]

        # 4. USMA seasons (roles per season)
        cursor.execute("""
            SELECT
                s.Season_Number,
                s.Season_Name,
                s.Start_Year,
                GROUP_CONCAT(DISTINCT sr.Role_name ORDER BY sr.Role_id SEPARATOR ', ') AS Roles

            FROM Staff_Assignment sa
            JOIN Staff_Assignment_Season sas ON sas.Assignment_id = sa.Assignment_id
            JOIN Season s ON s.Season_Number = sas.Season_Number
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id

            WHERE sa.Staff_Member_id = %s
              AND sa.Club_id = 1

            GROUP BY s.Season_Number, s.Season_Name, s.Start_Year
            ORDER BY s.Start_Year DESC
        """, (staff_member_id,))

        usma_seasons = cursor.fetchall()

        # 5. Other clubs
        cursor.execute("""
            SELECT
                sa.Assignment_id,
                c.Club_Current_Name,
                ci.City_Name,
                sr.Role_name,
                sa.Start_Date,
                sa.End_Date

            FROM Staff_Assignment sa
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
            LEFT JOIN City ci ON c.City_id = ci.City_id

            WHERE sa.Staff_Member_id = %s
              AND sa.Club_id != 1

            ORDER BY sa.Start_Date DESC
        """, (staff_member_id,))

        other_clubs = cursor.fetchall()

        # 6. Is this person also a player?
        cursor.execute("""
            SELECT Player_id
            FROM Player
            WHERE Person_id = %s
        """, (staff_data["Person_id"],))

        player_record = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    staff_data["usma_current"] = bool(usma_current)
    staff_data["usma_history"] = bool(usma_history)
    staff_status = get_staff_member_status(staff_data)

    staff_data["age"] = calculate_age(
        staff_data["Person_birth_date"],
        staff_data["Person_death_date"]
    )

    return render_template(
        "staff_member.html",
        Title=staff_data["Person_Display_Name"],
        staff_member=staff_data,
        other_roles=other_roles,
        usma_current=usma_current,
        usma_history=usma_history,
        usma_seasons=usma_seasons,
        other_clubs=other_clubs,
        staff_status=staff_status,
        player_record=player_record
    )