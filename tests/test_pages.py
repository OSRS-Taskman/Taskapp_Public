import pytest

PUBLIC = ["/", "/login/", "/register/", "/reset-password/"]
AUTHED = ["/dashboard/", "/profile/", "/faq/", "/wall-of-pain/", "/hiscores/",
          "/rank-check/", "/sync-collection-logs/",
          "/task-list-easy/", "/task-list-medium/", "/task-list-hard/",
          "/task-list-elite/", "/task-list-master/", "/task-list-pets/",
          "/task-list-extra/", "/task-list-passive/"]


@pytest.mark.parametrize("path", PUBLIC)
def test_public_pages_render(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", AUTHED)
def test_authenticated_pages_render(logged_in, path):
    resp = logged_in.get(path)
    assert resp.status_code == 200, resp.data[:300]


@pytest.mark.parametrize("path", AUTHED)
def test_pages_never_contain_secret_key(logged_in, app, path):
    body = logged_in.get(path).data.decode("utf-8", "replace")
    assert app.config["SECRET_KEY"] not in body
