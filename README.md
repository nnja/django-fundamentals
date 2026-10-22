# RescueScout

RescueScout is an animal rescue site built with Django. Visitors find
animals looking for a home and apply to adopt one. Employees and volunteers
manage animal records in Django's admin, where employees review adoption
applications. A read-only JSON API built with Django REST Framework provides
access to the animals.

This is the finished application from
[Django Fundamentals](https://fundamentals.learndjango.net/), a
master.dev course by Nina Zakharenko.

## Quickstart

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
   [Docker Desktop](https://www.docker.com/products/docker-desktop/), start
   Docker Desktop, then:

   ```bash
   uv sync
   ```

2. Start Postgres in a container. The first run downloads the image:

   ```bash
   docker compose up -d --wait
   ```

3. Create the tables:

   ```bash
   uv run manage.py migrate
   ```

4. Create a superuser for the admin:

   ```bash
   uv run manage.py createsuperuser
   ```

5. Load the sample data:

   ```bash
   uv run manage.py seed
   ```

6. Start the development server:

   ```bash
   uv run manage.py runserver
   ```

   Then open:

   - http://127.0.0.1:8000/ the site
   - http://127.0.0.1:8000/admin/ the admin
   - http://127.0.0.1:8000/api/v1/ the browsable API

## The database

Postgres 17 runs in Docker, from `compose.yaml`, and listens on
`localhost:5432`. The connection values in `config/settings.py` match the
`db` service in that file, so nothing has to be exported or copied.

Start it, and wait until it accepts connections:

```bash
docker compose up -d --wait
```

Stop it, keeping the data:

```bash
docker compose stop
```

Remove it and delete the database, the tables, and every row in them:

```bash
docker compose down -v
```

Open a Postgres shell inside the container:

```bash
docker compose exec db psql -U rescuescout -d rescuescout
```

## Sample data

Load sample animals, each with a photo from `seed_photos/`, and their
adoption applications. It loads nothing if the database already has an
animal:

```bash
uv run manage.py seed
```

Delete every animal, application, and seeded photo first, then load them
again:

```bash
uv run manage.py seed --reset
```

Also create a Volunteers group and an Employees group with an account in
each, to see the admin as someone who isn't a superuser, and a superuser
named `admin` if there isn't one:

```bash
uv run manage.py seed --accounts
```

| Username    | Password           | Group      |
| ----------- | ------------------ | ---------- |
| `volunteer` | `rescue-volunteer` | Volunteers |
| `employee`  | `rescue-employee`  | Employees  |
| `admin`     | `rescue-admin`     | superuser  |

## Tests

`uv run pytest` runs the suite against an in-memory SQLite database, named
in `config/test_settings.py`, so the tests pass with the container stopped.
Run them on Postgres too, with the container up:

```bash
uv run pytest
uv run pytest --ds=config.settings
```
