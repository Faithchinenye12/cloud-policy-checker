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
