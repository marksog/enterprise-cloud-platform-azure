import logging
import os
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from prometheus_client import Counter, Histogram, make_asgi_app


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("payments-api")


# ---------------------------------------------------------
# Database connection pool
# ---------------------------------------------------------

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=3,
    open=False,
    kwargs={"row_factory": dict_row},
)


# ---------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------

PAYMENTS_CREATED = Counter(
    "payments_created_total",
    "Total number of simulated payments created",
)

PAYMENTS_FAILED = Counter(
    "payments_failed_total",
    "Total number of failed payment operations",
)

PAYMENT_PROCESSING_DURATION = Histogram(
    "payment_processing_duration_seconds",
    "Duration of payment creation operations",
)


# ---------------------------------------------------------
# API models
# ---------------------------------------------------------

class PaymentRequest(BaseModel):
    order_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    amount: Decimal
    currency: str
    status: str


# ---------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Payments API")

    pool.open()
    pool.wait(timeout=15)

    with pool.connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                payment_id UUID PRIMARY KEY,
                order_id TEXT NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

    logger.info("Database initialized")

    yield

    pool.close()

    logger.info("Payments API stopped")


app = FastAPI(
    title="SOG Payments API",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# Prometheus endpoint
# ---------------------------------------------------------

app.mount("/metrics", make_asgi_app())


# ---------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "service": "payments-api",
        "status": "running",
    }


@app.get("/ready")
def ready():
    try:
        with pool.connection(timeout=3) as conn:
            conn.execute("SELECT 1")

        return {"status": "ready"}

    except Exception:
        logger.exception("Database readiness check failed")

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


# ---------------------------------------------------------
# Create simulated payment
# ---------------------------------------------------------

@app.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payment: PaymentRequest):
    payment_id = str(uuid.uuid4())

    try:
        with PAYMENT_PROCESSING_DURATION.time():
            with pool.connection() as conn:
                conn.execute(
                    """
                    INSERT INTO payments (
                        payment_id,
                        order_id,
                        amount,
                        currency,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        payment_id,
                        payment.order_id,
                        payment.amount,
                        payment.currency,
                        "simulated",
                    ),
                )

        PAYMENTS_CREATED.inc()

        logger.info(
            "Payment created payment_id=%s order_id=%s",
            payment_id,
            payment.order_id,
        )

        return PaymentResponse(
            payment_id=payment_id,
            order_id=payment.order_id,
            amount=payment.amount,
            currency=payment.currency,
            status="simulated",
        )

    except Exception:
        PAYMENTS_FAILED.inc()
        logger.exception("Payment creation failed")

        raise HTTPException(
            status_code=500,
            detail="Payment creation failed",
        )


# ---------------------------------------------------------
# Retrieve payment
# ---------------------------------------------------------

@app.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: uuid.UUID):
    try:
        with pool.connection() as conn:
            result = conn.execute(
                """
                SELECT
                    payment_id,
                    order_id,
                    amount,
                    currency,
                    status
                FROM payments
                WHERE payment_id = %s
                """,
                (payment_id,),
            ).fetchone()

    except Exception:
        logger.exception("Payment lookup failed")

        raise HTTPException(
            status_code=500,
            detail="Payment lookup failed",
        )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return PaymentResponse(
        payment_id=str(result["payment_id"]),
        order_id=result["order_id"],
        amount=result["amount"],
        currency=result["currency"],
        status=result["status"],
    )