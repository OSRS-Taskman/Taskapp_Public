import os
import sys
from pathlib import Path

import mongomock
import pymongo
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.update({
    "FLASK_ENV": "development",
    "SECRET_KEY": "finally-adding-tests-omg-now-32-bytes-plus",
    "SENDGRID_API_KEY": "test",
    "MONGO_URI": "mongodb://localhost:27017/",
    "DISCORD_CLIENT_ID": "123",
    "DISCORD_CLIENT_SECRET": "test",
    "DISCORD_REDIRECT_URI": "http://localhost/api/v2/auth/discord/redirect",
    "DISCORD_BOT_TOKEN": "test",
    "DISCORD_GUILD_ID": "1",
})


pymongo.MongoClient = mongomock.MongoClient

import config          # noqa: E402
import send_grid_email  # noqa: E402
import taskapp         # noqa: E402  (registers every route)
import task_login      # noqa: E402

USERNAME = "Gerni Test"
EMAIL = "GerniTest@example.com"
PASSWORD = "Str0ng!PassF0rT3st1ng"


@pytest.fixture
def app():
    taskapp.app.config.update(TESTING=True, SERVER_NAME="localhost")
    return taskapp.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db():
    yield
    for name in config.MONGO_CLIENT.list_database_names():
        config.MONGO_CLIENT.drop_database(name)


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    sent = []
    def fake_send(to, subject, body):
        sent.append({"to": to, "subject": subject, "body": body})
        return True
    monkeypatch.setattr(send_grid_email, "send_message", fake_send)
    return sent


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import requests
    def blocked(self, method, url, *args, **kwargs):
        # ConnectionError is a RequestException, so the app's own
        # "Discord/Google is down" handling gets exercised too.
        raise requests.ConnectionError(f"Network blocked in tests: {method} {url}")
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


@pytest.fixture
def make_user():
    def _make(username=USERNAME, password=PASSWORD, email=EMAIL,
              official=False, lms=False):
        ok, err = task_login.add_user(username, password, email, official, lms)
        assert ok, err
        return username
    return _make


@pytest.fixture
def login(client):
    def _login(username=USERNAME, password=PASSWORD):
        return client.post("/login/", data={"username": username, "password": password})
    return _login


@pytest.fixture
def logged_in(client, make_user, login):
    make_user()
    resp = login()
    assert resp.status_code == 302 and "/dashboard/" in resp.headers["Location"]
    return client
