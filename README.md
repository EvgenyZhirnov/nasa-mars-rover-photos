# 🚀 NASA Space Imagery Aggregator

Автоматический сборщик и отображение снимков из NASA. Собирает фотографии с марсоходов, астрономическое фото дня и снимки Земли из космоса.

## Возможности

- **Марсоходы** — фотографии с Curiosity, Opportunity и Spirit (каждые 2.4 минуты)
- **APOD** — Astronomy Picture of the Day, ежедневное обновление
- **EPIC** — снимки Земли с аппарата DSCOVR, ежедневное обновление
- **Анимации** — автоматическая генерация MP4 из фотографий марсоходов каждый день в 16:00
- **Telegram-бот** — отправка анимаций в Telegram
- **Веб-интерфейс** — тёмная тема на русском языке

## Структура проекта

```
nasa-mars-rover-photos/
├── main.py                 # Точка входа
├── web_server.py           # Flask веб-сервер и маршруты
├── nasa_api.py             # NASA Mars Rover Photos API
├── nasa_apod.py            # NASA Astronomy Picture of the Day API
├── nasa_epic.py            # NASA EPIC (Земля из космоса) API
├── animation_creator.py    # Генерация MP4 анимаций из фото
├── scheduler.py            # Планировщик фоновых задач
├── telegram_bot.py         # Telegram бот для отправки анимаций
├── utils.py                # Вспомогательные функции
├── templates/
│   ├── index.html          # Главная страница
│   ├── photos.html         # Страница фотографий
│   └── animation.html      # Страница анимаций
├── static/
│   ├── style.css           # Стили (тёмная тема)
│   └── *.svg               # Иконки и заглушки
├── data/                   # Загруженные фото и анимации (не в git)
│   ├── nasa_images/        # Фото марсоходов
│   ├── nasa_apod/          # Фото APOD
│   └── nasa_epic/          # Фото EPIC
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Быстрый запуск через Docker

```bash
git clone https://github.com/EvgenyZhirnov/nasa-mars-rover-photos.git
cd nasa-mars-rover-photos

cp .env.example .env
nano .env  # вставь NASA_API_KEY и SESSION_SECRET

docker compose up -d
```

Приложение запустится на `http://localhost:5000`

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `NASA_API_KEY` | Да | Ключ NASA API (получить на [api.nasa.gov](https://api.nasa.gov)) |
| `SESSION_SECRET` | Да | Любая случайная строка для Flask сессий |
| `TELEGRAM_BOT_TOKEN` | Нет | Токен Telegram бота от @BotFather |
| `TELEGRAM_CHAT_ID` | Нет | ID чата для отправки анимаций |

## Запуск без Docker

```bash
pip install flask requests schedule imageio imageio-ffmpeg gunicorn python-telegram-bot

export NASA_API_KEY=your_key
export SESSION_SECRET=random_string

mkdir -p data/nasa_images data/nasa_apod data/nasa_epic
gunicorn --bind 0.0.0.0:5000 main:app
```

## Полезные команды Docker

```bash
docker compose logs -f       # смотреть логи
docker compose restart       # перезапустить
docker compose down          # остановить
```
