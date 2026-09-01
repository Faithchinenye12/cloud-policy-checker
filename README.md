# Cloud Policy Checker

A multi-cloud security and compliance platform for inventorying resources,
evaluating policies, and running auditable background scans.

## Current capabilities

- JWT-based registration and authentication
- AWS, Azure, and GCP resource inventory
- Policy creation, management, and live evaluation
- PostgreSQL-backed scans and compliance findings
- Redis/Celery background scan processing
- React dashboard with responsive resource, policy, scan, and finding views

## Run with Docker Compose

1. Copy `.env.example` to `.env` and set a unique `JWT_SECRET_KEY` containing
   at least 32 characters.
2. Start the database and cache, then apply the database migrations:

   ```sh
   docker compose up -d postgres redis
   docker compose run --rm api alembic -c backend/alembic.ini upgrade head
   ```

3. Build and start the application services:

   ```sh
   docker compose up --build
   ```

4. Open the dashboard at <http://localhost:3000>. The API documentation is at
   <http://localhost:8000/docs>.

The stack includes PostgreSQL, Redis, the FastAPI service, a Celery worker, and
the frontend.

## Development checks

Run backend tests from the repository root:

```sh
pytest -c backend/pytest.ini
```

Build the frontend:

```sh
cd frontend
npm install
npm run build
```

## Scan workflow

Create a scan from the **Scans** view, then select **Run** to queue it. The
worker evaluates active policies matching each active resource's provider and
resource type, persists every result, and updates scan totals. Failed policy
results appear in the **Findings** view.
