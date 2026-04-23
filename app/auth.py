"""Auth helpers — in-memory user store + Google OAuth."""
from __future__ import annotations
import hashlib
import os
import re
import secrets

_users: dict[str, dict] = {}    # internal_key -> {display, provider, pw_hash?}
_sessions: dict[str, str] = {}  # token -> internal_key

GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

_DIGIT   = re.compile(r'\d')
_SPECIAL = re.compile(r'[!@#$%^&*()|\-_=+\[\]{};\'",./<>?\\`~]')


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _validate_password(pw: str) -> str | None:
    """Return an error string, or None if the password is valid."""
    if len(pw) < 8:
        return "Password must be at least 8 characters long."
    if not _DIGIT.search(pw):
        return "Password must contain at least one number (0-9)."
    if not _SPECIAL.search(pw):
        return "Password must contain at least one special character (!@#$%^&* …)."
    return None


# ── Local auth ────────────────────────────────────────────────────────────
def register_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        return {"error": "Username must be at least 3 characters."}
    pw_err = _validate_password(password)
    if pw_err:
        return {"error": pw_err}
    if username in _users:
        return {"error": "That username is already taken. Please choose another."}
    _users[username] = {"display": username, "provider": "local", "pw_hash": _hash(password)}
    return {"ok": True}


def login_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    rec = _users.get(username)
    if not rec or rec.get("provider") != "local":
        return {"error": "Incorrect username or password."}
    if rec.get("pw_hash") != _hash(password):
        return {"error": "Incorrect username or password."}
    tok = secrets.token_urlsafe(32)
    _sessions[tok] = username
    return {"token": tok, "username": rec["display"]}


# ── Google OAuth ──────────────────────────────────────────────────────────
def google_login(credential: str) -> dict:
    if not GOOGLE_CLIENT_ID:
        return {"error": "Google Sign-In is not configured on this server."}
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as g_req
        idinfo = id_token.verify_oauth2_token(
            credential, g_req.Request(), GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
        email   = idinfo.get("email", "")
        display = idinfo.get("name") or idinfo.get("given_name") or email.split("@")[0]
        ukey    = f"g_{email}"  # 'g_' prefix avoids collision with local users
        if ukey not in _users:
            _users[ukey] = {"display": display, "provider": "google"}
        tok = secrets.token_urlsafe(32)
        _sessions[tok] = ukey
        return {"token": tok, "username": display}
    except Exception as exc:
        return {"error": f"Google sign-in failed. Please try again. ({exc})"}


# ── Session helpers ───────────────────────────────────────────────────────
def logout_user(authorization: str) -> None:
    if authorization.startswith("Bearer "):
        _sessions.pop(authorization[7:], None)


def get_user_from_token(authorization: str) -> str | None:
    """Returns display name for valid token, else None."""
    if not authorization.startswith("Bearer "):
        return None
    ukey = _sessions.get(authorization[7:])
    if ukey and ukey in _users:
        return _users[ukey]["display"]
    return None
