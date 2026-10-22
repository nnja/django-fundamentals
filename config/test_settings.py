"""Settings for the tests. pyproject.toml names this module for pytest.

Everything is config/settings.py except two settings. The database is an
in-memory SQLite database that Django creates for each run, so the tests pass
whether or not the Postgres container is up. The password hasher is a fast
one, so tests that log in run quickly.
"""

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fast and unsafe for real passwords; Django's default is slow on purpose
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
