# 🚀 NASA Space Imagery Aggregator

Публичный сайт: https://nasarover.37-27-244-205.sslip.io — тестовый стенд:
https://preview.nasarover.37-27-244-205.sslip.io (под паролем).
Порядок обновления через GitHub Actions и откат описаны в [deploy/README.md](deploy/README.md).

**RU** | [EN](#english)

Автоматический сборщик и отображение снимков из NASA. Собирает фотографии с марсоходов, астрономическое фото дня и снимки Земли из космоса.

## Возможности

- **Марсоходы** — фотографии с Curiosity с резервным запросом Perseverance (каждые 5 минут, с паузой при ошибках)
- **APOD** — Astronomy Picture of the Day, ежедневное обновление
- **EPIC** — снимки Земли с аппарата DSCOVR, ежедневное обновление
- **Анимации** — автоматическая генерация MP4 из фотографий марсоходов каждый день в 16:00
- **Telegram-бот** — отправка анимаций в Telegram
- **Веб-интерфейс** — тёмная тема на русском и английском языках

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
gunicorn --bind 127.0.0.1:5000 --workers 1 --timeout 120 main:app
```

## Полезные команды Docker

```bash
docker compose logs -f       # смотреть логи
docker compose restart       # перезапустить
docker compose down          # остановить
```

---

## English

**[RU](#-nasa-space-imagery-aggregator)** | EN

Automatic aggregator and viewer for NASA imagery. Collects photos from Mars rovers, the Astronomy Picture of the Day, and Earth imagery from space.

## Features

- **Mars Rovers** — photos from Curiosity with Perseverance fallback (every 5 minutes, with backoff on errors)
- **APOD** — Astronomy Picture of the Day, updated daily
- **EPIC** — Earth imagery from the DSCOVR spacecraft, updated daily
- **Animations** — automatic daily MP4 generation from rover photos at 16:00
- **Telegram Bot** — sends daily animations to a Telegram chat
- **Web Interface** — dark theme with Russian and English support

## Quick Start with Docker

```bash
git clone https://github.com/EvgenyZhirnov/nasa-mars-rover-photos.git
cd nasa-mars-rover-photos

cp .env.example .env
nano .env  # set NASA_API_KEY and SESSION_SECRET

docker compose up -d
```

App will be available at `http://localhost:5000`

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NASA_API_KEY` | Yes | NASA API key (get one at [api.nasa.gov](https://api.nasa.gov)) |
| `SESSION_SECRET` | Yes | Any random string for Flask sessions |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | No | Chat ID to send animations to |

## Run without Docker

```bash
pip install flask requests schedule imageio imageio-ffmpeg gunicorn python-telegram-bot

export NASA_API_KEY=your_key
export SESSION_SECRET=random_string

mkdir -p data/nasa_images data/nasa_apod data/nasa_epic
gunicorn --bind 127.0.0.1:5000 --workers 1 --timeout 120 main:app
```

## Useful Docker Commands

```bash
docker compose logs -f       # view logs
docker compose restart       # restart
docker compose down          # stop
```

## VPS: запуск и проверка

Контейнер слушает только `127.0.0.1:5000`. Для доступа с компьютера используйте
SSH-туннель: `ssh -L 5000:127.0.0.1:5000 USER@SERVER`, затем откройте
`http://localhost:5000`. Не публикуйте порт на всех интерфейсах для закрытого стенда.

Хранилище и SQLite готовятся до запуска HTTP; синхронизация NASA и запуск
планировщика выполняются в фоне. Используйте ровно один worker, без `--preload`:
планировщик находится внутри процесса приложения. `/healthz` проверяет HTTP,
а `/status` показывает содержимое локального хранилища и ошибки Mars API.
Готовность HTTP не гарантирует доступность NASA или наличие новых фотографий.

APOD и его описание сохраняются вместе. Главная страница и `/apod/data` читают
локальный кэш; при первой загрузке он может быть пустым, после сбоя остаётся
последняя успешная запись. Изображения из прежней версии сохраняются в галерее;
карточка APOD появится после первой успешной синхронизации метаданных.

Проверки без запросов к NASA: `python -m unittest discover -s tests -v`.

## Space Explorer / тестовая обсерватория

Новая главная страница `/` содержит обзор APOD, снимки Curiosity/Perseverance,
проигрыватель кадров Земли (EPIC), поиск по NASA Image Library, таблицу
сближений JPL, карту EONET + GIBS и солнечные вспышки DONKI.
Прежний интерфейс доступен по `/classic`, сохранённые изображения — `/photos`.
Названия и описания наблюдений отображаются на языке источника.

Актуальные источники:

- APOD: `science.nasa.gov/wp-json/wp/v2/apod-basic`, изображение из `hdurl`.
- Марсоходы: `rovers.nebulum.one/api/v1`, независимый общественный сервис;
  `ROVER_API_BASE` позволяет сменить адрес. Ключ NASA этому сервису не передаётся.
- EPIC: прямой API и JPEG-архив `epic.gsfc.nasa.gov`.
- Медиатека: `images-api.nasa.gov/search`.
- Сближения: `ssd-api.jpl.nasa.gov/cad.api`, 30 дней и не дальше 10 расстояний до Луны.
- События: `eonet.gsfc.nasa.gov/api/v3/events`, до 60 открытых событий за 30 дней.
- Карта: NASA GIBS Terra/MODIS, дата съёмки выбирается отдельно от даты событий.
- DONKI: `ccmc.gsfc.nasa.gov/DONKI-API/get/FLR` — адрес после миграции сентября 2026.

`/api/explore/<source>` возвращает `status`, `source`, `updated_at`, `data`,
`refreshing`, `error`. Статусы: `loading`, `ready`, `stale`, `error`.
Источники обновляются независимо в фоне; последняя успешная запись переживает
ошибку запроса и перезапуск приложения. Кэш ограничен 128 записями на диске;
очередь — 12 запросами. Изображения нового интерфейса загружаются браузером
непосредственно из указанных источников. Подстановка вымышленных данных отсутствует.

### Отдельный тестовый контейнер

Создайте `.env` с `SESSION_SECRET` (случайная строка), затем:

```sh
docker compose -f docker-compose.preview.yml up -d --build
docker compose -f docker-compose.preview.yml ps
```

Порт: только `127.0.0.1:5080` сервера. Доступ с компьютера:

```sh
ssh -L 5081:127.0.0.1:5080 USER@SERVER
```

Откройте `http://127.0.0.1:5081`. Отдельный том `preview_data` сохраняет
изображения, комментарии и кэш. Остановка без удаления данных:

```sh
docker compose -f docker-compose.preview.yml down
```

### Проверки

```sh
python -m unittest discover -s tests -v
node --check static/explorer.js
```

Библиотека Leaflet 1.9.4 включена в `static/vendor`; лицензия рядом.

### Тематическая фотогалерея

В медиатеке доступны 24 подборки в четырёх группах: Солнечная система,
космические телескопы, наземные обсерватории и дальний космос. Все восемь
планет представлены отдельно; Луна, Солнце и Плутон — дополнительные подборки.
Состав: `/api/media/collections`; выбор и страницы:
`/api/explore/media?collection=neptune&page=2`.

Источником остаётся NASA Image Library. Подборки обсерваторий включают
совместные наблюдения и публикации о результатах, а не полные архивы учреждений.
Подписи сохраняют авторство и дату каталога. Фильтр по описанию скрывает
распознанные иллюстрации, схемы и оборудование, но не гарантирует идеальную
классификацию. Наблюдательные композиции и условные цвета остаются доступными.
Полноразмерные файлы запрашиваются при открытии карточки через NASA Asset API;
переход к большому файлу выполняется по отдельной ссылке.
