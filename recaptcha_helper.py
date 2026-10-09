import requests
from flask import request
from markupsafe import Markup

class Recaptcha:
    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

    def __init__(self):
        self.enabled = False
        self.site_key = self.secret_key = None

    def init_app(self, app):
        self.site_key = app.config.get("RECAPTCHA_SITE_KEY")
        self.secret_key = app.config.get("RECAPTCHA_SECRET_KEY")
        self.enabled = bool(self.site_key and self.secret_key)
        app.jinja_env.globals["recaptcha"] = self.get_code()

    def get_code(self):
        if not self.enabled:
            return ""
        return Markup(
            '<script src="https://www.google.com/recaptcha/api.js" async defer></script>'
            f'<div class="g-recaptcha" data-sitekey="{self.site_key}"></div>'
        )

    def verify(self):
        if not self.enabled:
            return True  # dev mode
        token = request.form.get("g-recaptcha-response", "")
        if not token:
            return False
        try:
            r = requests.post(self.VERIFY_URL,
                              data={"secret": self.secret_key, "response": token},
                              timeout=10)
            return bool(r.json().get("success"))
        except (requests.RequestException, ValueError):
            return False