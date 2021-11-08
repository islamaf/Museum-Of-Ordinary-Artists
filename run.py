import os
from config import secret_key
from flask import Flask, abort, session
from flask_admin import Admin
from flask_login import LoginManager, current_user
from flask_admin.contrib.sqla import ModelView
# from flask_s3 import FlaskS3
from werkzeug.security import generate_password_hash, check_password_hash

from commands import create_tables

from flaskr.database import *

# s3 = FlaskS3()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.cfg')

    from flaskr.home import home, cache
    from flaskr.auth import auth, mail_on_signup
    from flaskr.approve import approve
    from flaskr.user_control import user_control, mail

    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'

    app.config['SECRET_KEY'] = secret_key
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Neptune99@localhost:5432/mofoa'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://mofoa-db.cqvntsr097li.eu-central-1.rds.amazonaws.com:5432'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://xqprxuypzliusf:271fcbb45b74954c5f35a0dc8e0c98939480cd8aaa1ccc7fd2c862e544e4665a@ec2-54-72-155-238.eu-west-1.compute.amazonaws.com:5432/ddrnpn0tqfps8o'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://zyqkkqucdeocga:c4858941e40bbf702bf94fa9698e67cf8cbffae055e988acb6c240e4876d61a5@ec2-52-214-178-113.eu-west-1.compute.amazonaws.com:5432/deqsf43qvnoue3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    db.init_app(app)
    # s3.init_app(app)
    mail_on_signup.init_app(app)
    mail.init_app(app)
    cache.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    class Controller(ModelView):
        def is_accessible(self):
            if current_user.is_admin:
                return current_user.is_authenticated
            else:
                abort(404)

        def not_auth(self):
            return "You are not authorized to this admin page"

    admin = Admin(app, name='microblog', template_mode='bootstrap3')
    admin.add_view(Controller(User, db.session))
    admin.add_view(Controller(Post, db.session))

    # admin = User(name='islam', email='islam_9t9@yahoo.com', password=generate_password_hash('islam', method='sha256')
    #              , is_confirmed=True, is_admin=True)

    with app.app_context():
        db.create_all()
        # db.session.add(admin)
        # db.session.commit()
        cache.clear()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints registration
    app.register_blueprint(home)
    app.register_blueprint(auth)
    app.register_blueprint(approve)
    app.register_blueprint(user_control)

    app.cli.add_command(create_tables)

    return app


if __name__ == '__main__':
    app = create_app().run()