"""
Authentication module for the sample application.

Handles login, session token issuance, and OAuth callback processing.
"""

import time
from typing import Optional


class TokenExpiredError(Exception):
    """Raised when a session or OAuth token has expired."""


class AuthService:
    """Handles user authentication and session management."""

    def __init__(self, token_ttl_seconds: int = 3600):
        self.token_ttl_seconds = token_ttl_seconds
        self._sessions = {}

    def login(self, username: str, password: str) -> str:
        """
        Authenticate a user with username/password and issue a session token.

        :return: an opaque session token string
        """
        if not self._verify_credentials(username, password):
            raise ValueError("Invalid username or password")
        token = f"session-{username}-{int(time.time())}"
        self._sessions[token] = {"user": username, "issued_at": time.time()}
        return token

    def _verify_credentials(self, username: str, password: str) -> bool:
        # Placeholder for real credential verification (DB lookup, hashing, etc.)
        return bool(username) and bool(password)

    def validate_session(self, token: str) -> bool:
        """Check whether a session token is still valid (not expired)."""
        session = self._sessions.get(token)
        if session is None:
            return False
        age = time.time() - session["issued_at"]
        return age < self.token_ttl_seconds


def handle_oauth_callback(provider: str, code: str, state: Optional[str] = None) -> str:
    """
    Handle an OAuth provider's redirect callback.

    NOTE (see issue #15): this function does not currently verify that the
    `state` parameter returned by the provider matches the one we originally
    issued. Without that check, the callback is vulnerable to CSRF and can
    also silently accept a stale/replayed callback, which is the root cause
    of the intermittent "OAuth login fails after redirect" reports.

    :param provider: OAuth provider name, e.g. "google", "github"
    :param code: the authorization code returned by the provider
    :param state: the state parameter returned by the provider (currently unused!)
    :return: a session token
    """
    access_token = _exchange_code_for_token(provider, code)
    # BUG: `state` is accepted as a parameter but never validated against the
    # state we originally issued before redirecting the user to the provider.
    return _issue_session_from_access_token(access_token)


def _exchange_code_for_token(provider: str, code: str) -> str:
    # Placeholder for a real token exchange call to the OAuth provider.
    return f"access-token-for-{provider}-{code}"


def _issue_session_from_access_token(access_token: str) -> str:
    return f"session-{access_token}-{int(time.time())}"
