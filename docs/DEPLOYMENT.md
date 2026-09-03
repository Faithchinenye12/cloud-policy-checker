# Deployment guide

CloudConform runs as five services: the React/Nginx frontend, FastAPI
API, Celery worker, PostgreSQL, and Redis. Docker Compose is the supported local
and portfolio demonstration environment.

## Production principles

Use managed PostgreSQL and Redis services, terminate TLS at a load balancer or
ingress, and run the API and worker from the same tested image revision. Store
the JWT secret and provider identity configuration in a secret manager. Do not
commit `.env`, cloud keys, tokens, or credential files.

Use workload identity, managed identity, or IAM roles for cloud discovery. Keep
all discovery flags disabled until the corresponding identity and least-
privilege read permissions have been configured.

## Release checks

1. Run the backend tests and frontend production build.
2. Run `git diff --check` and confirm the worktree contains only intended files.
3. Apply Alembic migrations before serving the new API revision.
4. Start or roll out the API, worker, and frontend from the same commit.
5. Verify `/health`, worker connectivity to Redis, authentication, one policy
   evaluation, one background scan, findings, and report export.
6. Enable one cloud provider at a time and monitor failed scans without logging
   credential values.

## Backup and rollback

Back up PostgreSQL before migrations. Retain the previous container images and
deployment definition. If validation fails, disable provider discovery, roll
back the application images, and only downgrade the database when the matching
Alembic revision explicitly supports it.
