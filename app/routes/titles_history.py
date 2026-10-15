from flask import Blueprint, render_template, request
from app.database import get_db_connection


titles_history = Blueprint("titles_history", __name__)


@titles_history.route("/titles")
def titles_history_page():

    # Chronological order: oldest first by default
    order = request.args.get("order", "asc").lower()
    if order not in ("asc", "desc"):
        order = "asc"
    direction = "DESC" if order == "desc" else "ASC"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(f"""
        SELECT
            s.Season_Number,
            s.Season_Name,
            s.Start_Year,
            s.End_Year,
            c.Competition_id,
            c.Competition_Name,
            c.Competition_Name_ar,
            c.Competition_Type
        FROM Competition_Season cs

        JOIN Season s
            ON cs.Season_Number = s.Season_Number

        JOIN Competition c
            ON cs.Competition_id = c.Competition_id

        WHERE cs.Competition_Winner_Club_id = 1

        ORDER BY s.Start_Year {direction}, c.Competition_id
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    # Group titles by season (order is preserved)
    seasons_with_titles = []
    index = {}
    summary = {}

    for row in rows:
        season_number = row["Season_Number"]

        if season_number not in index:
            index[season_number] = {
                "Season_Number": season_number,
                "Season_Name": row["Season_Name"],
                "titles": []
            }
            seasons_with_titles.append(index[season_number])

        index[season_number]["titles"].append(row)

        comp_id = row["Competition_id"]
        if comp_id not in summary:
            summary[comp_id] = {
                "name": row["Competition_Name"],
                "type": row["Competition_Type"],
                "count": 0
            }
        summary[comp_id]["count"] += 1

    summary = dict(sorted(summary.items()))

    return render_template(
        "titles_history.html",
        Title="Titles",
        seasons_with_titles=seasons_with_titles,
        summary=summary,
        total_titles=len(rows),
        order=order
    )