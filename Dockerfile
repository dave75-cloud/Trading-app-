FROM python:3.11-slim

WORKDIR /app

# System deps for scientific python / parquet
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Default to API; docker-compose overrides for other services
CMD ["uvicorn", "services.inference_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
