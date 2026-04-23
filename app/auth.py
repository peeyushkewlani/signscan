"""Auth helpers — in-memory user store + Google OAuth."""
from __future__ import annotations
import hashlib, os, re, secrets
from datetime import datetime

_users:    dict[str, dict] = {}
_sessions: dict[str, str]  = {}

GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

_DIGIT   = re.compile(r'\d')
_SPECIAL = re.compile(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/\\`~]')


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _validate_password(pw: str) -> str | None:
    if len(pw) < 8:
        return "Password must be at least 8 characters long."
    if not _DIGIT.search(pw):
        return "Password must contain at least one number (0-9)."
    if not _SPECIAL.search(pw):
        return "Password must contain at least one special character (!@#$%…)."
    return None


# ── Local auth ────────────────────────────────────────────────────────────
def register_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        return {"error": "Username must be at least 3 characters."}
    err = _validate_password(password)
    if err:
        return {"error": err}
    if username in _users:
        return {"error": "That username is already taken."}
    _users[username] = {
        "display": username, "provider": "local",
        "pw_hash": _hash(password),
        "join_date": datetime.now().strftime("%B %Y"),
    }
    return {"ok": True}


def login_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    u = _users.get(username)
    if not u or u.get("provider") != "local" or u.get("pw_hash") != _hash(password):
        return {"error": "Incorrect username or password."}
    tok = secrets.token_urlsafe(32)
    _sessions[tok] = username
    return {"token": tok, "username": u["display"],
            "account_type": "local", "join_date": u.get("join_date", "")}





# ── Google OAuth ──────────────────────────────────────────────────────────
def google_login(credential: str) -> dict:
    if not GOOGLE_CLIENT_ID:
        return {"error": "Google Sign-In is not configured on this server."}
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as g_req
        info    = id_token.verify_oauth2_token(credential, g_req.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=10)
        email   = info.get("email", "")
        display = info.get("name") or info.get("given_name") or email.split("@")[0]
        ukey    = f"g_{email}"
        if ukey not in _users:
            _users[ukey] = {"display": display, "provider": "google",
                            "join_date": datetime.now().strftime("%B %Y")}
        tok = secrets.token_urlsafe(32)
        _sessions[tok] = ukey
        return {"token": tok, "username": display,
                "account_type": "google", "join_date": _users[ukey].get("join_date", "")}
    except Exception as exc:
        return {"error": f"Google sign-in failed. ({exc})"}


# ── Session helpers ───────────────────────────────────────────────────────
def logout_user(authorization: str) -> None:
    if authorization.startswith("Bearer "):
        _sessions.pop(authorization[7:], None)


def get_user_from_token(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    ukey = _sessions.get(authorization[7:])
    if ukey and ukey in _users:
        return _users[ukey]["display"]
    return None
