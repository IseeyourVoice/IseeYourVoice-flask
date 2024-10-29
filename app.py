import os
import threading

from flask import Flask, render_template, redirect, render_template, url_for, request, session, send_file, \
    send_from_directory
from dotenv import load_dotenv
from flask_login import LoginManager, login_required
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
from mail.mail import mail, send_mail, send_training_complete_email, send_inference_complete_email
from edit.edit import edit_audio
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


os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
# Initialize OAuth
oauth.init_app(app)
google = create_google_oauth(app)
init_google(google)  # Pass the OAuth object to routes
mail.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(community_bp, url_prefix='/post')

OUTPUT_FILE_PATH = ""


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


def save_uploaded_model_file(file):
    escaped_file_name = escape_filename(file.filename)
    file_path = UPLOAD_DIR / 'model' / escaped_file_name
    file.save(file_path)
    file.close()
    return escaped_file_name, str(file_path)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/train')
@login_required
def train():
    # 유저의 학습 파일 업로드 form 존재 (train.html)
    return render_template('train.html')


@app.route('/train_start', methods=['GET', 'POST'])
@login_required
def train_start():
    if request.method == 'GET':
        return redirect('/')

    file = request.files['file']
    file_name, file_path = save_uploaded_train_file(file)

    # 여기서 비동기로 학습 시작
    executor.submit(train_process.train_process, file_path, file_name)
    os.chdir(os.path.dirname(__file__))

    return render_template('train_start.html')


@app.route('/make')
@login_required
def make():
    # 유저의 추론 파일 업로드 form 존재 (make.html)
    return render_template('make.html')


@app.route('/make_start', methods=['GET', 'POST'])
@login_required
def make_start():
    if request.method == 'GET':
        return redirect('/')

    file = request.files['audio_file']
    file_name, file_path = save_uploaded_make_file(file)

    model = request.files['model_file']
    model_name, model_path = save_uploaded_model_file(model)

    # 여기서 비동기로 추론 시작
    executor.submit(make_process.make_process(file_path, file_name, model_path, model_name))
    os.chdir(os.path.dirname(__file__))

    return render_template('make_start.html')


@app.route('/edit')
@login_required
def edit():
    # 유저가 편집할 파일과 파라미터를 제출할 수 있느 form 존재 (edit.html)
    return render_template('edit.html')


@app.route('/edit_finish', methods=['GET', 'POST'])
@login_required
def edit_finish():
    global OUTPUT_FILE_PATH

    if request.method == 'GET':
        return redirect('/')

    file = request.files['file']
    file_name, file_path = save_uploaded_make_file(file)

    start_time = int(request.form['start_time'])
    end_time = int(request.form['end_time'])
    volume_change = int(request.form['volume_change'])
    fade_in_time = int(request.form['fade_in_time'])
    fade_out_time = int(request.form['fade_out_time'])

    OUTPUT_FILE_PATH = edit_audio(file_name, file_path, start_time, end_time, volume_change, fade_in_time,
                                  fade_out_time)

    return render_template('edit_finish.html', file_path=OUTPUT_FILE_PATH)  # file_path 전달


@app.route('/download')
@login_required
def download_file():
    return send_file(OUTPUT_FILE_PATH, as_attachment=True)


@app.route('/mypage/<int:user_id>', methods=['GET', 'POST'])
@login_required
def mypage(user_id):
    user_id = session['user']['id']  # 세션에서 유저 ID 가져오기
    model_path = os.path.join('account', str(user_id), 'model')
    cover_path = os.path.join('account', str(user_id), 'cover')

    # 모델 파일 리스트
    model_files = os.listdir(model_path) if os.path.exists(model_path) else []

    # 음성 합성 작품 파일 리스트
    cover_files = os.listdir(cover_path) if os.path.exists(cover_path) else []

    return render_template('mypage.html', user_id=user_id, model_files=model_files, cover_files=cover_files)


@app.route('/download_model/<user_id>/<filename>')
@login_required
def download_model(user_id, filename):
    model_path = os.path.join('account', str(user_id), 'model')
    return send_from_directory(model_path, filename)


@app.route('/download_cover/<user_id>/<filename>')
@login_required
def download_cover(user_id, filename):
    cover_path = os.path.join('account', str(user_id), 'cover')
    return send_from_directory(cover_path, filename)


if __name__ == '__main__':
    migrate = Migrate(app, db)
    app.run(debug=True)
