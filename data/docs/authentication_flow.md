# Authentication Flow

This document describes how login and OAuth work in the sample application.

## Username/password login

1. The client calls `AuthService.login(username, password)`.
2. `AuthService._verify_credentials` checks the credentials.
3. A session token is issued and stored in `AuthService._sessions`.
4. Subsequent requests validate the token via `AuthService.validate_session`.

## OAuth login

1. The client requests an authorization URL via
   `oauth.build_authorization_url(provider, redirect_uri)`.
2. This function generates a random `state` value, stores it as "pending",
   and embeds it in the URL sent to the provider.
3. The provider redirects the browser back to our callback endpoint with an
   authorization `code` and the same `state` value.
4. Our callback endpoint calls `auth.handle_oauth_callback(provider, code, state)`.
5. `handle_oauth_callback` exchanges the `code` for an access token and issues
   a session.

### Security requirement: state validation

Per OAuth 2.0 best practice (RFC 6749 Section 10.12), the `state` value
returned by the provider **must** be validated against the value we
originally issued, using `oauth.is_state_valid(state)`, before the callback
is treated as legitimate. This prevents CSRF attacks and replay of stale
callbacks.

As of the current codebase, `handle_oauth_callback` accepts a `state`
argument but does not call `is_state_valid` on it. This is a known gap
tracked in issue #15.
