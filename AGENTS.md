# RescueScout

A Django site for an animal rescue. The rescue's employees and volunteers
manage animals and adoption applications in the admin, visitors browse
animals and apply to adopt one, and a JSON API under `/api/v1/` lists the
animals.

## Commands

- `uv sync` installs everything.
- `docker compose up -d --wait` starts Postgres and returns when it accepts connections. `docker compose down -v` deletes the database and everything in it.
- `uv run manage.py migrate` creates or updates the tables.
- `uv run manage.py seed` loads the sample animals and applications, the fixed rows of `ANIMALS` and `APPLICATIONS` in the command. If the database already has an animal, it loads no animals or applications. `--reset` first deletes every animal and application, and the seeded photos. `--accounts` also creates the Volunteers and Employees groups and three accounts for the admin: a superuser, `admin` / `rescue-admin`; `volunteer` / `rescue-volunteer`, in Volunteers; and `employee` / `rescue-employee`, in Employees. An account or group that already exists is left as it is, and the command names the accounts it left.
- `uv run manage.py runserver` serves the site at http://127.0.0.1:8000/.
- These checks must all pass before a change is done:

      uv run pytest
      uv run ruff check .
      uv run ruff format --check .
      uv run djlint . --check
      uv run djlint . --lint
      uv run manage.py check
      uv run manage.py makemigrations --check --dry-run

- `uv run pytest` uses `config/test_settings.py`, which swaps the database for in-memory SQLite, so the tests pass with the container stopped. That is on purpose. A test that saves a photo takes the `media_root` fixture from `tests/conftest.py`, which points `MEDIA_ROOT` at a temporary directory.
- Before a change to a model, a migration, or a query is done, also run the tests on Postgres, with the container up: `uv run pytest --ds=config.settings`. SQLite does not enforce a column's length, folds case for ASCII letters only, and happens to return unordered rows in id order, so a test can pass there and fail on Postgres.

## Rules

- Pages are class-based views rendering Django templates, built on Django's generic views: `ListView`, `DetailView`, `CreateView`, and `TemplateView`. The API is Django REST Framework.
- A change to a model's fields or `Meta` options needs a migration: `uv run manage.py makemigrations`. Never edit a migration that has been applied.
- This project uses Django 6.1. Do not use an API that was removed or deprecated before it.
- Imports between modules of the same app are relative: `from .models import Animal`. Imports in tests, in management commands, and across apps are absolute: `from animals.models import Animal`.
- A rule about one field goes on the model field as a validator, so the admin, the forms, and the serializers all run it. Serializers skip a model's `clean()` method, and `save()` runs no validation at all.
- A package the application imports goes in `dependencies` with `uv add`; a development tool, such as Ruff or Django Debug Toolbar, goes in the `dev` group with `uv add --dev`. `psycopg` is the Postgres driver.
- The API is read-only and open to anyone on purpose. The site has no login of its own: employees and volunteers log in through the admin.
- Connection values, `SECRET_KEY`, and `DEBUG` are written in `config/settings.py`, for a database on your own machine.
- The permission checks are `AnimalAdmin`'s own `get_readonly_fields()` and `has_change_permission()`, each calling `request.user.has_perm("animals.manage_animal")`, as Django's documentation writes the admin's hooks.
