import discord_api
import discord_service
from conftest import USERNAME


def test_connect_redirects_to_discord(logged_in):
    resp = logged_in.get("/api/v2/auth/discord/connect")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("https://discord.com/oauth2/authorize")


def test_redirect_links_account(logged_in, monkeypatch):
    monkeypatch.setattr(discord_api, "exchange_code", lambda code: {"access_token": "tok"})
    monkeypatch.setattr(discord_api, "retrieve_discord_id", lambda token: {"id": 4242})
    resp = logged_in.get("/api/v2/auth/discord/redirect?code=abc")
    assert resp.status_code == 302
    assert discord_service.get_discord_auth_info(USERNAME).discord_user_id == 4242


def test_disconnect(logged_in):
    discord_service.link_discord_id(USERNAME, 4242)
    resp = logged_in.get("/api/v2/auth/discord/disconnect")
    assert resp.status_code == 302
    assert discord_service.get_discord_auth_info(USERNAME).discord_user_id is None
