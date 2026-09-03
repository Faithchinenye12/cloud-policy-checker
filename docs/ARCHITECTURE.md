# Architecture

The browser authenticates with FastAPI and sends its JWT in the authorization
header. FastAPI owns inventory, policies, scans, and persisted compliance
results in PostgreSQL. Scan requests are queued through Redis and executed by a
Celery worker.

Before evaluation, an enabled provider adapter can refresh storage inventory
through the official AWS, Azure, or Google Cloud SDK. Discovery is read-only and
disabled by default. The deterministic rule engine then compares stored JSON
configuration with active policies. Failed results become traceable findings;
the Reports page summarises and exports that stored evidence.

The React application is compiled into static assets and served by Nginx, which
also proxies API requests. This separation allows the API, worker, and frontend
to scale independently while sharing one versioned contract.

## Policy intelligence projection

The Intelligence API projects existing compliance evidence into a connected
graph without creating a second source of truth. Resource, policy, scan, and
finding nodes retain their database identifiers. Typed edges explain which scan
evaluated a resource, which policy checked it, and which finding was produced.

Risk scoring is deterministic and capped at 100. Open findings contribute
points according to policy severity, and remediation guidance is derived from
the stored rule configuration. The Risk Intelligence workspace consumes this
projection to present exposure, traceability, and prioritized next actions.
