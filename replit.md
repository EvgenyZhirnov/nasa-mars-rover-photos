# NASA Mars Rover Photos Application

## Overview

This is a NASA space imagery aggregation application that automatically fetches, stores, and displays photos from multiple NASA APIs. The application collects images from Mars Rovers (Curiosity, Opportunity, Spirit), the Astronomy Picture of the Day (APOD), and Earth Polychromatic Imaging Camera (EPIC). It creates daily animations from collected Mars Rover photos and can distribute them via Telegram bot integration.

The web interface is presented in Russian and provides a dark-themed space exploration experience for viewing collected imagery and generated animations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask** serves as the web application framework
- Single-file web server (`web_server.py`) handles all HTTP routing and template rendering
- Application starts schedulers and fetches initial data on startup

### Modular API Integration Design
Each NASA API has its own dedicated module for separation of concerns:
- `nasa_api.py` - Mars Rover Photos API integration
- `nasa_apod.py` - Astronomy Picture of the Day API
- `nasa_epic.py` - Earth Polychromatic Imaging Camera API

This approach allows independent development and testing of each API integration.

### Scheduled Task System
- Uses the `schedule` library for periodic task execution
- Runs in a background thread via `scheduler.py`
- Tasks include: fetching new images (25 times/hour), updating APOD, updating EPIC photos, creating daily animations

### Animation Generation
- `animation_creator.py` uses `imageio` to compile downloaded images into MP4 animations
- Animations are generated daily at 16:00
- Images are organized by date prefix (YYYYMMDD format) for easy filtering

### Frontend Architecture
- Server-side rendered templates using Jinja2
- Bootstrap dark theme for styling (`bootstrap-agent-dark-theme.min.css`)
- Font Awesome icons for UI elements
- Custom CSS in `static/style.css` for Mars-themed accents

### File Storage Structure
All data is stored in the filesystem rather than a database:
- `data/nasa_images/` - Mars Rover photos (named with date prefix)
- `data/nasa_apod/` - Astronomy Picture of the Day
- `data/nasa_epic/` - EPIC Earth photos
- `data/nasa_animation.mp4` - Generated daily animation

## External Dependencies

### NASA APIs
- **Mars Rover Photos API** (`https://api.nasa.gov/mars-photos/api/v1/rovers`) - Fetches images from Curiosity, Opportunity, and Spirit rovers
- **APOD API** (`https://api.nasa.gov/planetary/apod`) - Daily astronomy images
- **EPIC API** (`https://api.nasa.gov/EPIC/api`) - Earth observation imagery
- All APIs require `NASA_API_KEY` environment variable (falls back to DEMO_KEY)

### Telegram Integration
- Uses `python-telegram-bot` library for sending animations
- Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables
- Async implementation for non-blocking message delivery

### Python Libraries
- `Flask` - Web framework
- `requests` - HTTP client for API calls
- `schedule` - Task scheduling
- `imageio` - Animation creation from image sequences
- `telegram` - Telegram bot functionality

### Environment Variables Required
- `NASA_API_KEY` - NASA API authentication (optional, uses DEMO_KEY if not set)
- `TELEGRAM_BOT_TOKEN` - Telegram bot authentication (optional)
- `TELEGRAM_CHAT_ID` - Default Telegram chat for sending animations (optional)
- `SESSION_SECRET` - Flask session secret key (has default fallback)