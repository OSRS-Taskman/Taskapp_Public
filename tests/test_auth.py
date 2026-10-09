import task_login
from conftest import USERNAME, EMAIL, PASSWORD


def test_register_creates_user_and_sends_verification(client, sent_emails):
    resp = client.post("/register/", data={
        "username": USERNAME, "password": PASSWORD, "confirmPassword": PASSWORD,
        "email": EMAIL,
    })
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/login/")
    assert task_login.coll.find_one({"username": USERNAME}) is not None
    assert sent_emails and sent_emails[0]["to"] == EMAIL
    assert "/email_verify_inital/" in sent_emails[0]["body"]


def test_register_rejects_mismatched_passwords(client):
    resp = client.post("/register/", data={
        "username": USERNAME, "password": PASSWORD, "confirmPassword": "nope",
        "email": EMAIL,
    })
    assert b"did not match" in resp.data
    assert task_login.coll.find_one({"username": USERNAME}) is None


def test_register_rejects_weak_password(client):
    resp = client.post("/register/", data={
        "username": USERNAME, "password": "weak", "confirmPassword": "weak",
        "email": EMAIL,
    })
    assert b"does not meet requirements" in resp.data
    assert task_login.coll.find_one({"username": USERNAME}) is None


def test_login_success_sets_session(client, make_user, login):
    make_user()
    resp = login()
    assert resp.status_code == 302 and "/dashboard/" in resp.headers["Location"]
    with client.session_transaction() as s:
        assert s["logged_in"] and s["username"] == USERNAME


def test_login_wrong_password(client, make_user, login):
    make_user()
    resp = login(password="Wr0ng!Pass")
    assert resp.status_code == 200 and b"Invalid Username or Password" in resp.data
    with client.session_transaction() as s:
        assert "logged_in" not in s


def test_login_unknown_user(login):
    resp = login(username="unknown user")
    assert b"Invalid Username or Password" in resp.data


def test_long_password_over_72_bytes(make_user, login):
    long_pw = "TooL0ng!" + "g" * 100   # meets policy, 108 bytes
    make_user(password=long_pw)
    assert login(password=long_pw).status_code == 302


def test_logout_clears_session(logged_in):
    resp = logged_in.get("/logout/")
    assert resp.status_code == 302
    with logged_in.session_transaction() as s:
        assert "logged_in" not in s


def test_protected_page_redirects_when_logged_out(client):
    resp = client.get("/dashboard/")
    assert resp.status_code == 302 and "/login/" in resp.headers["Location"]
