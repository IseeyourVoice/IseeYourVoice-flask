from flask import Flask, render_template
from dotenv import load_dotenv
import os

from flask_login import LoginManager

from auth import login_manager
from auth.oauth import oauth, create_google_oauth
from auth.routes import auth_bp, init_google
from community.routes import community_bp
from models import db
from config import Config
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from models.user import User

# Load environment variables
load_dotenv()

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config.from_object(Config)
# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

login_manager.init_app(app)
login_manager.login_view = 'auth_bp.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Initialize OAuth
oauth.init_app(app)
google = create_google_oauth(app)
init_google(google)  # Pass the OAuth object to routes

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(community_bp, url_prefix='/post')


@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    migrate = Migrate(app, db)
    app.run(debug=True)
