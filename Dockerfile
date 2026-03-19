FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir \
    flask \
    requests \
    schedule \
    imageio \
    imageio-ffmpeg \
    "python-telegram-bot>=13.0,<14.0" \
    gunicorn

COPY . .

RUN mkdir -p data/nasa_images data/nasa_apod data/nasa_epic

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--workers", "1", "main:app"]
