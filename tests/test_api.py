from conftest import USERNAME, PASSWORD


def _token(client):
    resp = client.post("/api/v2/login", json={"username": USERNAME, "password": PASSWORD})
    assert resp.status_code == 200
    return resp.get_json()["token"]


def test_api_login_and_profile(client, make_user):
    make_user()
    token = _token(client)
    resp = client.get("/api/v2/user/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_api_login_bad_password(client, make_user):
    make_user()
    resp = client.post("/api/v2/login", json={"username": USERNAME, "password": "x"})
    assert resp.status_code == 401


def test_api_rejects_missing_and_bad_token(client):
    assert client.get("/api/v2/user/profile").status_code == 401
    assert client.get("/api/v2/user/profile",
                      headers={"Authorization": "Bearer garbage"}).status_code == 401
