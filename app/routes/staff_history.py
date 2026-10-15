from flask import Blueprint, render_template
from app.database import get_db_connection


staff_history = Blueprint("staff_history", __name__)


@staff_history.route("/staff-history")
def staff_history_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                sa.Assignment_id,
                sa.Staff_Member_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name,
                GROUP_CONCAT(
                    s.Season_Name
                    ORDER BY s.Start_Year DESC, s.Season_Number DESC
                    SEPARATOR ', '
                ) AS Seasons

            FROM Staff_Assignment sa

            JOIN Staff_Member sm ON sa.Staff_Member_id = sm.Staff_Member_id
            JOIN Person p ON sm.Person_id = p.Person_id
            JOIN Club c ON sa.Club_id = c.Club_id
            JOIN Staff_Role sr ON sa.Role_id = sr.Role_id
            LEFT JOIN Staff_Assignment_Season sas ON sas.Assignment_id = sa.Assignment_id
            LEFT JOIN Season s ON s.Season_Number = sas.Season_Number
            WHERE sa.Club_id = 1

            GROUP BY
                sa.Assignment_id,
                sa.Staff_Member_id,
                sa.Start_Date,
                sa.End_Date,
                p.Person_Display_Name,
                c.Club_Current_Name,
                sr.Role_name

            ORDER BY sa.Start_Date DESC, sa.Assignment_id DESC
        """)

        assignments = cursor.fetchall()

        return render_template(
            "staff_history.html",
            Title="Staff History",
            assignments=assignments
        )

    finally:
        cursor.close()
        connection.close()