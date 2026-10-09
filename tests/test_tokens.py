import task_login
from conftest import USERNAME, EMAIL


def test_reset_token_roundtrip():
    tok = task_login.get_reset_token(USERNAME)
    assert task_login.verify_reset_token(tok) == USERNAME


def test_reset_token_tampered():
    tok = task_login.get_reset_token(USERNAME)
    assert task_login.verify_reset_token(tok + "x") is None


def test_reset_token_not_valid_for_email_verify():
    tok = task_login.get_reset_token(USERNAME)
    assert task_login.verify_email_verify_token(tok) is None


def test_email_token_roundtrip():
    tok = task_login.get_email_verify_token(USERNAME, EMAIL)
    assert task_login.verify_email_verify_token(tok) == (USERNAME, EMAIL)


def test_reset_token_expires(monkeypatch):
    tok = task_login.get_reset_token(USERNAME)
    monkeypatch.setattr(task_login, "TOKEN_MAX_AGE", -1)
    assert task_login.verify_reset_token(tok) is None
