from flask import Flask
import config
from recaptcha_helper import Recaptcha
from datetime import timedelta

app = Flask(__name__)

recaptcha = Recaptcha()
isProd = config.IS_PROD

# Set secret key for Flask App.
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = isProd
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if isProd:
    # Keys for Google reCAPTCHA.
    app.config['RECAPTCHA_SITE_KEY'] = config.RECAPTCHA_SITE_KEY
    app.config['RECAPTCHA_SECRET_KEY'] = config.RECAPTCHA_SECRET_KEY
    # initialize reCAPTCHA
    recaptcha.init_app(app)

# specifies database to use.
db = config.MONGO_CLIENT["TaskAppLoginDB"]