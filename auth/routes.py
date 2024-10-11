# auth/routes.py

from flask import Blueprint, redirect, url_for, session
from flask_login import login_user, login_required, logout_user

from models.user import User
from models import db

auth_bp = Blueprint('auth_bp', __name__)
google = None  # google 객체를 전역에서 초기화하지 않음


def init_google(google_obj):
    global google
    google = google_obj


@auth_bp.route('/login',methods=['GET','POST'],endpoint='login')
def login():
    redirect_uri = url_for('auth_bp.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/authorize')
def authorize():
    try:
        # Fetch access token
        token = google.authorize_access_token()
        print(f"Token: {token}")  # Debugging output

        # Fetch user info from Google using the correct URL
        resp = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        user_info = resp.json()
        print(f"User info: {user_info}")  # Debugging output

        # Check if user exists in the database, else create a new user
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            new_user = User(email=user_info['email'], name=user_info['name'])
            db.session.add(new_user)
            db.session.commit()

        login_user(user)
        # Store user info in session
        session['user'] = user_info

        # Redirect to home page after login
        return redirect(url_for('home'))

    except Exception as e:
        print(f"Error during authorization: {e}")
        return redirect(url_for('home'))



@auth_bp.route('/profile')
@login_required
def profile():
    user_info = session.get('user')
    return f'Hello, {user_info["name"]}!'


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user', None)
    return redirect(url_for('home'))
