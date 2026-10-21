FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy dependency definition and install dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

# Copy application source code and tests
COPY app /app/app
COPY tests /app/tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
