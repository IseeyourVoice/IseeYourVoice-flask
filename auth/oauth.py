from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def create_google_oauth(app):
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',  # Correct URL
        client_kwargs={'scope': 'openid profile email'},
        jwks_uri='https://www.googleapis.com/oauth2/v3/certs',  # Ensure JWKS URI is set
    )
    return google
