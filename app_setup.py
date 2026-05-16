from flask import Flask
import config
from flask_recaptcha import ReCaptcha # type: ignore

app = Flask(__name__)

isProd = config.IS_PROD

# Set secret key for Flask App.
app.config['SECRET_KEY'] = config.SECRET_KEY

if isProd:
    # Keys for Google reCAPTCHA.
    app.config['RECAPTCHA_SITE_KEY'] = config.RECAPTCHA_SITE_KEY
    app.config['RECAPTCHA_SECRET_KEY'] = config.RECAPTCHA_SECRET_KEY
    # initialize reCAPTCHA
    recaptcha = ReCaptcha(app)
else:
    recaptcha = "Disabled for DEV"


# email service account.
taskapp_email = config.SECRET_KEY

# specifies database to use.
db = config.MONGO_CLIENT["TaskAppLoginDB"]