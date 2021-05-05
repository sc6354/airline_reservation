#Import Flask Library
from flask import Flask, request
import pymysql.cursors
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy 

#init MySQL so we can use it later 
#db = pymysql.connect(host='localhost',user='root', password='', database='airline_system')



db = SQLAlchemy() 

def create_app():
    app = Flask(__name__)
    #app.secret_key = 'some secret key'
    app.config['SECRET_KEY'] = 'some-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:pass@127.0.0.1/airline_system'
    #mysql+pymysql://<username>:<password>@<host>/<dbname>
    # Connecting to MySQL server at localhost using PyMySQL DBAPI 
    #engine = create_engine("mysql+pymysql://root:pass@localhost/mydb")

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import users

    @login_manager.user_loader
    def load_user(username):
        return users.query.get(username)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    app = create_app
    app.run()