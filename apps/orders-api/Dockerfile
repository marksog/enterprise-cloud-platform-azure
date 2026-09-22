FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    -r requirements.txt

COPY app ./app

RUN groupadd \
      --gid 10001 \
      appuser \
    && useradd \
      --create-home \
      --uid 10001 \
      --gid 10001 \
      appuser

USER 10001:10001

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]