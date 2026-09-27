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

            # تحويل من DD/MM/YYYY إلى YYYY-MM-DD إذا لزم الأمر
            # (لا يوجد تاريخ في Player_Season لكن للمستقبل)

            # ---------------------------------------------
            # Check duplicate
            # ---------------------------------------------

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

            # ---------------------------------------------
            # Insert Player Season
            # ---------------------------------------------

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

            return redirect(
                url_for("player_season.player_season_page")
            )

                # =================================================
        # GET REQUEST
        # =================================================

        # Get filter parameters
        search_player = request.args.get("search_player", "").strip()
        search_club = request.args.get("search_club", "").strip()
        season_filter = request.args.get("season_filter", "")
        position_filter = request.args.get("position_filter", "")

        # ... (الكود السابق للـ last_player و usma_club يبقى كما هو)

        cursor.execute("""
            SELECT Player_id
            FROM Player
            ORDER BY Player_id DESC
            LIMIT 1
        """)

        last_player = cursor.fetchone()
        last_player_id = last_player["Player_id"] if last_player else None

        cursor.execute("""
            SELECT Club_id
            FROM Club
            WHERE Club_Current_Name = 'USM Alger'
            LIMIT 1
        """)

        usma_club = cursor.fetchone()
        usma_club_id = usma_club["Club_id"] if usma_club else 1

        # ... (باقي الـ selects للـ players, clubs, seasons, positions بقى كما هو)

        cursor.execute("""
            SELECT
                p.Player_id,
                pe.Person_Display_Name,
                p.Main_Jersey_Number,
                pp.Position_id AS Main_Position_id

            FROM Player p

            JOIN Person pe
                ON p.Person_id = pe.Person_id

            LEFT JOIN Player_Position pp
                ON p.Player_id = pp.Player_id
                AND pp.Is_Main = 1

            ORDER BY
                pe.Person_Display_Name
        """)

        players = cursor.fetchall()

        cursor.execute("""
            SELECT
                Club_id,
                Club_Current_Name

            FROM Club

            ORDER BY
                Club_Current_Name
        """)

        clubs = cursor.fetchall()

        cursor.execute("""
            SELECT
                Season_Number,
                Season_Name,
                Start_Year,
                End_Year

            FROM Season

            ORDER BY
                Start_Year DESC
        """)

        seasons = cursor.fetchall()

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

        # ========================================
        # Load Player Seasons WITH FILTERS
        # ========================================

        where_clauses = []
        params = []

        if search_player:
            where_clauses.append("pe.Person_Display_Name LIKE %s")
            params.append(f"%{search_player}%")

        if search_club:
            where_clauses.append("c.Club_Current_Name LIKE %s")
            params.append(f"%{search_club}%")

        if season_filter:
            where_clauses.append("ps.Season_Number = %s")
            params.append(season_filter)

        if position_filter:
            where_clauses.append("ps.Position_id = %s")
            params.append(position_filter)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
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

            WHERE {where_clause}

            ORDER BY
                s.Start_Year DESC,
                pe.Person_Display_Name
        """

        cursor.execute(query, params)
        player_seasons = cursor.fetchall()

        return render_template(
            "admin/player_season/player_season.html",
            Title="Player Seasons",

            players=players,
            clubs=clubs,
            seasons=seasons,
            positions=positions,
            player_seasons=player_seasons,
            last_player_id=last_player_id,
            usma_club_id=usma_club_id,
            search_player=search_player,
            search_club=search_club,
            season_filter=season_filter,
            position_filter=position_filter
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

@player_season.route(
    "/<int:player_id>/<int:club_id>/<int:season_number>/edit",
    methods=["GET", "POST"]
)
def edit_player_season(
    player_id,
    club_id,
    season_number
):

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

            return redirect(
                url_for("player_season.player_season_page")
            )

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

        return render_template(
            "admin/player_season/edit_player_season.html",

            Title="Edit Player Season",

            player_season=player_season_data,

            positions=positions,

            clubs = clubs
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

@player_season.route(
    "/<int:player_id>/<int:club_id>/<int:season_number>/delete",
    methods=["POST"]
)
def delete_player_season(
    player_id,
    club_id,
    season_number
):

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

        return redirect(
            url_for("player_season.player_season_page")
        )

    except Exception as error:

        connection.rollback()

        return f"Error deleting Player Season: {error}", 500

    finally:

        cursor.close()
        connection.close()