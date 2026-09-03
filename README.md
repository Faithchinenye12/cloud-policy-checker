# CloudConform

**[Explore the live read-only recruiter demo](https://cloudconform-demo.onrender.com)**

A multi-cloud security and compliance platform for inventorying resources,
evaluating policies, and running auditable background scans.

The product is guided by a commitment to pair trustworthy security engineering
with an interface that is calm, clear, and memorable. Read the
[product and design vision](docs/DESIGN_VISION.md) for the story and standards
behind that work.

## Current capabilities

- JWT-based registration and authentication
- Manual AWS, Azure, and GCP resource inventory
- Opt-in AWS, Azure, and Google Cloud storage discovery through official SDKs
- Policy creation, management, and live evaluation
- PostgreSQL-backed scans and compliance findings
- Redis/Celery background scan processing
- React dashboard with responsive resource, policy, scan, and finding views
- Traceable policy intelligence graph with deterministic risk prioritization
- Risk Intelligence workspace with evidence paths and remediation guidance
- Finding ownership, deadlines, lifecycle status, notes, and audit history
- Evidence-backed readiness views for CIS Controls v8.1, NIST CSF 2.0,
  ISO/IEC 27001:2022, and the SOC 2 Trust Services Criteria

Framework mappings are product-authored crosswalks from deterministic policy
evidence. Readiness scores are decision support, not an audit, certification,
or endorsement by a framework publisher. A failed control remains a gap after
workflow resolution until a later verification scan records compliant evidence.

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

## Public recruiter demo

The root `render.yaml` describes the API, worker, PostgreSQL database, Key Value
cache, and static frontend. Render applies migrations and seeds a representative
workspace on the first deployment. Set `ALLOWED_ORIGINS` on the API to the
frontend URL and `VITE_API_URL` on the frontend to the public API URL, then
redeploy both services. Visitors can use **Explore live demo** without receiving
credentials; demo JWTs are read-only, so the shared evidence cannot be changed.

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

## AWS S3 discovery

AWS discovery is disabled by default, so local demonstrations continue to use
the manually entered inventory. To enable live S3 discovery, set
`AWS_DISCOVERY_ENABLED=true` privately in `.env`, then restart the API and
worker containers. Never commit `.env` or cloud credentials.

The AWS SDK uses its standard credential provider chain. Prefer temporary
credentials supplied by an IAM role. The scanning identity needs permission to
list buckets and read each bucket's region, public-access-block configuration,
and encryption configuration. During an AWS scan, discovered buckets are
upserted into inventory before deterministic policies are evaluated.

## Azure and Google Cloud discovery

Azure and Google Cloud discovery are also disabled by default. Azure uses
`DefaultAzureCredential` and lists storage accounts in the configured
subscription. Google Cloud uses Application Default Credentials and lists
buckets in the configured project. Enable either integration privately with
`AZURE_DISCOVERY_ENABLED=true` or `GCP_DISCOVERY_ENABLED=true`, configure its
subscription or project identifier, and restart the API and worker.

Prefer managed identity, workload identity, or another short-lived credential
source supported by the provider SDK. Never commit client secrets, service
account keys, access tokens, or credential files.
