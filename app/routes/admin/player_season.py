from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_db_connection

player_season = Blueprint(
    "player_season",
    __name__,
    url_prefix="/admin/player-season"
)

# =====================================================
# PLAYER SEASON - CREATE & READ
# =====================================================

@player_season.route("/", methods=["GET", "POST"])
def player_season_page():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Add Player Season
        # =================================================

        if request.method == "POST":

            player_id = request.form.get("player_id")
            club_id = request.form.get("club_id")
            season_number = request.form.get("season_number")
            position_id = request.form.get("position_id")
            jersey_number = request.form.get("jersey_number") or None

            # Check duplicate
            cursor.execute("""
                SELECT 1
                FROM Player_Season
                WHERE Player_id = %s
                  AND Club_id = %s
                  AND Season_Number = %s
            """, (
                player_id,
                club_id,
                season_number
            ))

            existing_record = cursor.fetchone()

            if existing_record:
                return (
                    "This player is already registered "
                    "for this club in this season.",
                    400
                )

            # Insert
            cursor.execute("""
                INSERT INTO Player_Season (
                    Player_id,
                    Club_id,
                    Season_Number,
                    Position_id,
                    Jersey_Number
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                player_id,
                club_id,
                season_number,
                position_id,
                jersey_number
            ))

            connection.commit()

            return redirect(url_for("player_season.player_season_page"))

        # =================================================
        # Load Players
        # =================================================

        cursor.execute("""
            SELECT
                p.Player_id,
                pe.Person_Display_Name
            FROM Player p
            JOIN Person pe
                ON p.Person_id = pe.Person_id
            ORDER BY pe.Person_Display_Name
        """)

        players = cursor.fetchall()

        # =================================================
        # Load Clubs
        # =================================================

        cursor.execute("""
            SELECT
                Club_id,
                Club_Current_Name
            FROM Club
            ORDER BY Club_Current_Name
        """)

        clubs = cursor.fetchall()

        # =================================================
        # Load Seasons
        # =================================================

        cursor.execute("""
            SELECT
                Season_Number,
                Season_Name,
                Start_Year,
                End_Year
            FROM Season
            ORDER BY Start_Year DESC
        """)

        seasons = cursor.fetchall()

        # =================================================
        # Load Positions
        # =================================================

        cursor.execute("""
            SELECT
                Position_id,
                Position_Code,
                Position_Name
            FROM Position
            ORDER BY Position_Category_id, Position_id
        """)

        positions = cursor.fetchall()

        # =================================================
        # Load Player Seasons
        # =================================================

        cursor.execute("""
            SELECT
                ps.Player_id,
                ps.Club_id,
                ps.Season_Number,
                ps.Position_id,
                ps.Jersey_Number,
                pe.Person_Display_Name,
                c.Club_Current_Name,
                s.Season_Name,
                po.Position_Code,
                po.Position_Name

            FROM Player_Season ps

            JOIN Player p
                ON ps.Player_id = p.Player_id

            JOIN Person pe
                ON p.Person_id = pe.Person_id

            JOIN Club c
                ON ps.Club_id = c.Club_id

            JOIN Season s
                ON ps.Season_Number = s.Season_Number

            JOIN Position po
                ON ps.Position_id = po.Position_id

            ORDER BY
                s.Start_Year DESC,
                pe.Person_Display_Name
        """)

        player_seasons = cursor.fetchall()

        return render_template(
            "admin/player_season/player_season.html",
            Title="Player Seasons",
            players=players,
            clubs=clubs,
            seasons=seasons,
            positions=positions,
            player_seasons=player_seasons
        )

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# EDIT PLAYER SEASON
# =====================================================

@player_season.route("/<int:player_id>/<int:club_id>/<int:season_number>/edit", methods=["GET", "POST"])
def edit_player_season(player_id, club_id, season_number):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # =================================================
        # POST - Update
        # =================================================

        if request.method == "POST":

            position_id = request.form.get("position_id")
            jersey_number = request.form.get("jersey_number") or None

            cursor.execute("""
                UPDATE Player_Season
                SET
                    Position_id = %s,
                    Jersey_Number = %s
                WHERE Player_id = %s
                  AND Club_id = %s
                  AND Season_Number = %s
            """, (
                position_id,
                jersey_number,
                player_id,
                club_id,
                season_number
            ))

            connection.commit()

            return redirect(url_for("player_season.player_season_page"))

        # =================================================
        # Load Current Record
        # =================================================

        cursor.execute("""
            SELECT
                ps.Player_id,
                ps.Club_id,
                ps.Season_Number,
                ps.Position_id,
                ps.Jersey_Number,
                pe.Person_Display_Name,
                c.Club_Current_Name,
                s.Season_Name

            FROM Player_Season ps

            JOIN Player p
                ON ps.Player_id = p.Player_id

            JOIN Person pe
                ON p.Person_id = pe.Person_id

            JOIN Club c
                ON ps.Club_id = c.Club_id

            JOIN Season s
                ON ps.Season_Number = s.Season_Number

            WHERE ps.Player_id = %s
              AND ps.Club_id = %s
              AND ps.Season_Number = %s
        """, (
            player_id,
            club_id,
            season_number
        ))

        player_season_data = cursor.fetchone()

        if player_season_data is None:
            return "Player Season record not found", 404

        # =================================================
        # Load Positions
        # =================================================

        cursor.execute("""
            SELECT
                Position_id,
                Position_Code,
                Position_Name

            FROM Position

            ORDER BY
                Position_Category_id,
                Position_id
        """)

        positions = cursor.fetchall()

        return render_template(
            "admin/player_season/edit_player_season.html",
            Title="Edit Player Season",
            player_season=player_season_data,
            positions=positions
        )

    except Exception as error:
        connection.rollback()
        return f"Error: {error}", 500

    finally:
        cursor.close()
        connection.close()


# =====================================================
# DELETE PLAYER SEASON
# =====================================================

@player_season.route("/<int:player_id>/<int:club_id>/<int:season_number>/delete", methods=["POST"])
def delete_player_season(player_id, club_id, season_number):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            DELETE FROM Player_Season

            WHERE Player_id = %s
              AND Club_id = %s
              AND Season_Number = %s
        """, (
            player_id,
            club_id,
            season_number
        ))

        connection.commit()

        return redirect(url_for("player_season.player_season_page"))

    except Exception as error:
        connection.rollback()
        return f"Error deleting Player Season: {error}", 500

    finally:
        cursor.close()
        connection.close()