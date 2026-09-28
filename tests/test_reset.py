import re
from conftest import EMAIL, PASSWORD

NEW_PW = "N3w!Password"


def _token_from(email_body):
    return re.search(r"/reset_password/([^\s]+)", email_body).group(1)


def test_reset_request_sends_email(client, make_user, sent_emails):
    make_user()
    resp = client.post("/reset-password/request/", data={"email": EMAIL})
    assert resp.status_code == 200
    assert sent_emails and "/reset_password/" in sent_emails[0]["body"]


def test_full_reset_flow(client, make_user, login, sent_emails):
    make_user()
    client.post("/reset-password/request/", data={"email": EMAIL})
    token = _token_from(sent_emails[0]["body"])
    assert client.get(f"/reset_password/{token}").status_code == 200
    resp = client.post(f"/reset_password/{token}",
                       data={"password": NEW_PW, "confirmPassword": NEW_PW})
    assert resp.status_code == 302 and "/login/" in resp.headers["Location"]
    assert login(password=NEW_PW).status_code == 302


def test_reset_get_with_bad_token_redirects(client):
    resp = client.get("/reset_password/not-a-token")
    assert resp.status_code == 302


def test_reset_post_with_bad_token_changes_nothing(client, make_user, login):
    make_user()
    client.post("/reset_password/not-a-token",
                data={"password": NEW_PW, "confirmPassword": NEW_PW})
    assert login(password=PASSWORD).status_code == 302
