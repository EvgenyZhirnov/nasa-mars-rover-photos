FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "flask>=3.1.0" \
    "gunicorn>=23.0.0" \
    "requests>=2.32.3" \
    "schedule>=1.2.2" \
    "imageio[ffmpeg]>=2.37.0" \
    "python-telegram-bot>=22.0"

COPY . .

RUN mkdir -p data/nasa_images data/nasa_apod data/nasa_epic \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "main:app"]
