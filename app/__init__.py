from flask import Flask

app = Flask(__name__)

# Setup the app with the config.py file
app.config.from_object('app.config_dev')

# Setup the logger
from app.logger_setup import logger

# Setup the database
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

# Setup the mail server
from flask_mail import Mail

mail = Mail(app)

# Setup the debug toolbar
from flask_debugtoolbar import DebugToolbarExtension

app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
app.config['DEBUG_TB_PROFILER_ENABLED'] = True
toolbar = DebugToolbarExtension(app)

# Setup the password crypting
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# Import the views
from app.views import main, error
from app.views.controllers.user import userbp
from app.views.controllers.monitor import monitor
from app.views.controllers.data_set import data_set
from app.views.controllers.communicate import communicate
from app.views.controllers.logic_build import logic_build
from app.views.controllers.logic_setting import logic_setting

app.register_blueprint(userbp)
app.register_blueprint(monitor)
app.register_blueprint(data_set)
app.register_blueprint(communicate)
app.register_blueprint(logic_build)
app.register_blueprint(logic_setting)

# Setup the user login process
from flask_login import LoginManager
from app.models import User

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(email):
    return User.query.filter(User.email == email).first()


from flask_wtf.csrf import CsrfProtect
CsrfProtect(app)

from app import admin
