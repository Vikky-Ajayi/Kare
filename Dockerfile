FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq5 gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y gcc libpq-dev && apt-get autoremove -y

COPY . .

# Run as non-root
RUN useradd --create-home --uid 1000 kare && chown -R kare:kare /app
USER kare

EXPOSE 8000

# Railway sets $PORT. start.sh runs migrations then execs gunicorn.
CMD ["sh", "start.sh"]
