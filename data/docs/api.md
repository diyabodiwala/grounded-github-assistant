# API Reference

## POST /login

Body: `{ "username": str, "password": str }`
Returns: `{ "token": str }`

Calls `AuthService.login`. See `authentication_flow.md` for details.

## GET /oauth/authorize

Query params: `provider`
Redirects the user to the URL returned by `oauth.build_authorization_url`.

## GET /oauth/callback

Query params: `provider`, `code`, `state`
Calls `auth.handle_oauth_callback(provider, code, state)`.

## GET /health

Returns `{ "status": "ok" }`. No authentication required.
