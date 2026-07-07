"""
OAuth provider integration helpers.

This module is responsible for building the authorization redirect URL and
generating/storing the CSRF `state` value that `auth.py`'s
`handle_oauth_callback` is supposed to validate on the way back.
"""

import secrets

_PENDING_STATES = set()


def build_authorization_url(provider: str, redirect_uri: str) -> str:
    """
    Build the URL we send the user to at the OAuth provider, including a
    freshly generated `state` value that must be echoed back on callback.

    :return: the full authorization URL
    """
    state = secrets.token_urlsafe(16)
    _PENDING_STATES.add(state)
    return (
        f"https://oauth.{provider}.example.com/authorize"
        f"?redirect_uri={redirect_uri}&state={state}"
    )


def is_state_valid(state: str) -> bool:
    """
    Check whether a `state` value returned by the provider matches one we
    issued. Currently NOT called anywhere in auth.py's callback handler --
    this is the missing piece referenced in issue #15.
    """
    if state in _PENDING_STATES:
        _PENDING_STATES.discard(state)
        return True
    return False
