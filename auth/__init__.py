from flask_login import LoginManager

login_manager = LoginManager()
from . import routes  # routes.py에서 라우트 로드