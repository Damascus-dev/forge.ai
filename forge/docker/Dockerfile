FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings docker redis httpx litellm prometheus-client python-json-logger rich

RUN mkdir -p /forge
COPY . /forge/

ENV PYTHONPATH=/

CMD ["uvicorn", "forge.api.main:app", "--host", "0.0.0.0", "--port", "8000"]