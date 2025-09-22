# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# copy only requirements first for better caching
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# copy the code
COPY . /app

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# entrypoint will run migrations/collectstatic and wait for DB
ENTRYPOINT ["/app/entrypoint.sh"]

# Default CMD (overridden by compose during development)
CMD ["gunicorn", "automdjango.wsgi:application", "--bind", "0.0.0.0:8000"]
