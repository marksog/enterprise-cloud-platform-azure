# Stage 1: Install application dependencies
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY platform/api/requirements.txt /build/requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    --prefix=/install \
    -r /build/requirements.txt


# Stage 2: Production runtime
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/platform/api:/app

WORKDIR /app

COPY --from=builder /install /usr/local

COPY platform/api/app /app/platform/api/app
COPY platform/generator /app/platform/generator

# Required by the workload generator
COPY terraform/workloads/nonprod/workloads.auto.tfvars \
     /app/terraform/workloads/nonprod/workloads.auto.tfvars

# Required for existing workload detection and GitOps generation
COPY gitops/workloads /app/gitops/workloads

# Create an unprivileged application user.
# Remove pip from the runtime image.
RUN useradd --create-home --uid 10001 appuser \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip \
              /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
              /usr/local/bin/pip \
              /usr/local/bin/pip3 \
              /usr/local/bin/pip3.13

USER 10001

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]