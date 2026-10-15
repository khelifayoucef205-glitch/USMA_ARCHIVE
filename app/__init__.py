from flask import Flask


def create_app():

    app = Flask(__name__)

    # =========================
    # User Interface
    # =========================

    from app.routes.main import main
    from app.routes.player import player
    from app.routes.squad import squad
    from app.routes.staff_member import staff_member
    from app.routes.staff_history import staff_history
    from app.routes.titles_history import titles_history

    app.register_blueprint(main)
    app.register_blueprint(player)
    app.register_blueprint(squad)
    app.register_blueprint(staff_member)
    app.register_blueprint(staff_history)
    app.register_blueprint(titles_history)


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
    from app.routes.admin.staff_assignment_season import staff_assignment_season
    from app.routes.admin.edit_staff_assignment import edit_staff_assignment
    from app.routes.admin.add_staff_member import add_staff_member
    from app.routes.admin.staff_members import staff_members
    from app.routes.admin.edit_staff_member import edit_staff_member
    from app.routes.admin.staff_assignment import staff_assignment
    
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
    app.register_blueprint(add_staff_member)
    app.register_blueprint(staff_members)
    app.register_blueprint(edit_staff_member)
    app.register_blueprint(staff_assignment)
    app.register_blueprint(staff_assignment_season)
    app.register_blueprint(edit_staff_assignment)


    return app