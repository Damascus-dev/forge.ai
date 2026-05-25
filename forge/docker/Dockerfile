FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e . 2>&1 | grep -v "WARNING"

RUN mkdir -p /forge
COPY . /forge/

ENV PYTHONPATH=/

CMD ["uvicorn", "forge.api.main:app", "--host", "0.0.0.0", "--port", "8000"]