# Architecture Overview

The sample application is a small monolith with three main modules:

- `auth.py` -- login, session management, and OAuth callback handling.
- `oauth.py` -- OAuth authorization-URL construction and CSRF `state` tracking.
- `database.py` -- an in-memory key-value store standing in for a real
  database connection.
- `utils.py` -- shared helper functions (slugify, truncate) used across
  the rest of the codebase.

Sessions are stored in-process (see `AuthService._sessions`) and are not
currently persisted to `database.py`; that is a known limitation, not a bug,
and is out of scope for issue #15.
