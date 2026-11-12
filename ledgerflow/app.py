#!/usr/bin/env python3
"""
app.py — LedgerFlow Enterprise Application Entrypoint
Run locally with zero dependencies:
    python3 app.py
Or run via Uvicorn ASGI server in production:
    uvicorn app:app --host 0.0.0.0 --port ${PORT:-8090}
"""

import os
from backend.payment_flows import init_database
from backend.server import asgi_app, run_http_server

# Ensure DB is initialized on module import for serverless/ASGI workers
init_database()

# ASGI callable for uvicorn / hypercorn / daphne
app = asgi_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    host = os.environ.get("HOST", "0.0.0.0")
    run_http_server(host=host, port=port)
