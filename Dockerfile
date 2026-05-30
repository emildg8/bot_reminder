FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/
COPY scripts/ scripts/
COPY assets/ assets/
COPY pytest.ini .

RUN mkdir -p data/logs data/backups

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=60s --timeout=10s --start-period=45s --retries=3 \
    CMD python scripts/healthcheck.py

CMD ["python", "-m", "bot.main"]
