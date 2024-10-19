import os
import threading

from flask import Flask, render_template, redirect, render_template, url_for, request, session
from dotenv import load_dotenv
from flask_login import LoginManager
from pathlib import Path
from auth import login_manager
from auth.oauth import oauth, create_google_oauth
from auth.routes import auth_bp, init_google
from community.routes import community_bp
from models import db
from config import Config
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from models.user import User
from concurrent.futures import ThreadPoolExecutor

from DDSP_SVC_KOR_master import train_process, make_process
os.chdir(os.path.dirname(__file__))

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

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)

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

def escape_filename(filename: str):
    escape_chars = ' ', '[', ']', '*', '?', '/', '\\'
    for char in escape_chars:
        filename = filename.replace(char, '_')
    return filename

def save_uploaded_train_file(file):
    escaped_file_name = escape_filename(file.filename)
    file_path = UPLOAD_DIR / 'train' / escaped_file_name
    file.save(file_path)
    file.close()
    return escaped_file_name, str(file_path)

def save_uploaded_make_file(file):
    escaped_file_name = escape_filename(file.filename)
    file_path = UPLOAD_DIR / 'make' / escaped_file_name
    file.save(file_path)
    file.close()
    return escaped_file_name, str(file_path)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/train')
def train():
    # 유저의 학습 파일 업로드 form 존재 (train.html)
    return render_template('train.html')


@app.route('/train_start', methods=['GET', 'POST'])
def train_start():
    if request.method == 'GET':
        return redirect('/')

    file = request.files['file']
    file_name, file_path = save_uploaded_train_file(file)

    # 여기서 비동기로 학습 시작
    executor.submit(train_process.train_process, file_path)
    os.chdir(os.path.dirname(__file__))

    return render_template('train_start.html')


@app.route('/make')
def make():
    # 유저의 추론 파일 업로드 form 존재 (make.html)
    return render_template('make.html')


@app.route('/make_start', methods=['GET', 'POST'])
def make_start():
    if request.method == 'GET':
        return redirect('/')

    file = request.files['file']
    file_name, file_path = save_uploaded_train_file(file)

    # 여기서 비동기로 추론 시작
    #executor.submit(make_process.make_process, file_path)
    make_process.make_process(file_path)
    os.chdir(os.path.dirname(__file__))

    return render_template('make_start.html')


if __name__ == '__main__':
    migrate = Migrate(app, db)
    app.run(debug=True)
