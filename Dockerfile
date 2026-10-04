FROM python:3.11-slim

ARG APP_REVISION=development
ENV APP_REVISION=$APP_REVISION PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
LABEL org.opencontainers.image.source="https://github.com/EvgenyZhirnov/nasa-mars-rover-photos"
LABEL org.opencontainers.image.revision=$APP_REVISION

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/nasa_images data/nasa_apod data/nasa_epic \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "main:app"]
