import task_login
from conftest import USERNAME


NEW_PW = "N3w!Password"


def test_change_password(logged_in, login):
    resp = logged_in.post("/profile/change-password/", data={"new_password": NEW_PW})
    assert resp.get_json()["success"] is True
    logged_in.get("/logout/")
    assert login(password=NEW_PW).status_code == 302


def test_change_password_rejects_weak(logged_in):
    resp = logged_in.post("/profile/change-password/", data={"new_password": "weak"})
    assert resp.get_json()["success"] is False


def test_change_username(logged_in):
    resp = logged_in.post("/profile/change-username/", data={"username": "Gerni Changed"})
    assert resp.get_json()["success"] is True
    with logged_in.session_transaction() as s:
        assert s["username"] == "Gerni Changed"
    assert task_login.coll.find_one({"username": "Gerni Changed"}) is not None


def test_change_username_to_same_name(logged_in):
    resp = logged_in.post("/profile/change-username/", data={"username": USERNAME})
    assert resp.get_json()["success"] is False


def test_change_lms_status(logged_in):
    resp = logged_in.post("/profile/change-lms-status/", data={"lms_status": "true"})
    assert resp.get_json()["success"] is True
