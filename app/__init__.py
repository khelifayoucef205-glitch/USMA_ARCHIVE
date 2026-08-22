from flask import Flask


def create_app():

    app = Flask(__name__)

    # =========================
    # User Interface
    # =========================

    from app.routes.main import main
    from app.routes.player import player
    from app.routes.squad import squad

    app.register_blueprint(main)
    app.register_blueprint(player)
    app.register_blueprint(squad)


    # =========================
    # Admin Panel
    # =========================
    # from app.routes.admin import admin
    from app.routes.admin.add_player import add_player
    from app.routes.admin.players import players
    from app.routes.admin.edit_player import edit_player
    from app.routes.admin.player_club import player_club
    from app.routes.admin.cities import cities
    from app.routes.admin.clubs import clubs
    from app.routes.admin.player_season import player_season
    from app.routes.admin.edit_club import edit_clubs
    from app.routes.admin.edit_player_club import edit_player_club
    from app.routes.admin.dashboard import dashboard

    # app.register_blueprint(admin)
    app.register_blueprint(add_player)
    app.register_blueprint(players)
    app.register_blueprint(edit_player)
    app.register_blueprint(player_club)
    app.register_blueprint(cities)
    app.register_blueprint(clubs)
    app.register_blueprint(player_season)
    app.register_blueprint(edit_clubs)
    app.register_blueprint(edit_player_club)
    app.register_blueprint(dashboard)


    return app