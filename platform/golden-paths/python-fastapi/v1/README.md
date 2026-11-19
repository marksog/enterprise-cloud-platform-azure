# SOG Platform — FastAPI Golden Path

This application was generated using the SOG Internal Developer Platform.

## Local Development

Install dependencies:

    pip install -r requirements-dev.txt

Run the application:

    uvicorn app.main:app --reload --port 8080

Run tests:

    python -m pytest tests/ -v

## Health Endpoints

- /health — Liveness
- /ready — Readiness

## Deployment

The application is designed for deployment to Azure Kubernetes Service
using GitHub Actions and Argo CD.
