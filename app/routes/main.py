from flask import Blueprint, render_template

from app.database import get_db_connection

main = Blueprint("main", __name__)


@main.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM Country")
        country_count = cursor.fetchone()[0]
    finally:
        cursor.close()
        connection.close()

    return render_template(
        "home.html",
        Title="Home",
        country_count=country_count
    )