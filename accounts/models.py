from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """The site's user account, with the same fields as the built-in user.

    Changing AUTH_USER_MODEL after the first migration takes a hand-written
    schema and data migration, so the project sets its own model before any
    table exists.
    """
