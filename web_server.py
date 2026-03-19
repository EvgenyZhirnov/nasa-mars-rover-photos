"""
Flask web server — defines the app and routes only.
No side effects on import: no scheduler start, no API calls, no downloads.
"""
import os
import json
import math
import logging
from flask import Flask, render_template, send_file, jsonify, abort, request, redirect, url_for
from datetime import datetime

import config
import nasa_apod
import nasa_epic
import comments as comments_db

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SESSION_SECRET or "change-me-set-SESSION_SECRET-env-var"


@app.route('/')
def index():
    apod_info = None
    apod_dir = config.NASA_APOD_DIR

    if apod_dir.exists() and any(apod_dir.iterdir()):
        apod_files = [f for f in apod_dir.iterdir() if f.is_file()]
        if apod_files:
            latest = max(apod_files, key=lambda f: f.stat().st_mtime)
            try:
                apod_data = nasa_apod.get_apod()
                if apod_data:
                    apod_info = {
                        'title':       apod_data.get('title', 'NASA APOD'),
                        'date':        apod_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'explanation': apod_data.get('explanation', ''),
                        'file_path':   f"/apod/image/{latest.name}",
                        'media_type':  apod_data.get('media_type', 'image'),
                        'url':         apod_data.get('url', ''),
                        'copyright':   apod_data.get('copyright', 'NASA'),
                    }
            except Exception as e:
                logger.error(f"Error getting APOD data: {e}")

    reviews = comments_db.get_comments('review')
    return render_template('index.html', apod=apod_info, reviews=reviews)


@app.route('/animation')
def get_animation():
    if config.ANIMATION_MP4.exists():
        return send_file(
            config.ANIMATION_MP4, mimetype='video/mp4', as_attachment=True,
            download_name=f"mars_rover_{datetime.now().strftime('%Y%m%d')}.mp4"
        )
    if config.ANIMATION_GIF.exists():
        return send_file(
            config.ANIMATION_GIF, mimetype='image/gif', as_attachment=True,
            download_name=f"mars_rover_{datetime.now().strftime('%Y%m%d')}.gif"
        )
    return render_template('animation.html', error="Анимация пока недоступна / Animation not yet available.")


@app.route('/animation/view')
def view_animation():
    return render_template('animation.html', error=None)


@app.route('/status')
def status():
    has_mp4 = config.ANIMATION_MP4.exists()
    has_gif = config.ANIMATION_GIF.exists()
    has_animation = has_mp4 or has_gif

    animation_time = None
    anim_path = config.ANIMATION_MP4 if has_mp4 else (config.ANIMATION_GIF if has_gif else None)
    if anim_path:
        animation_time = datetime.fromtimestamp(anim_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    def count_images(directory):
        if not directory.exists():
            return 0
        try:
            return len([f for f in directory.iterdir() if f.suffix.lower() in ('.jpg', '.png')])
        except Exception:
            return 0

    rover_count = count_images(config.NASA_IMAGES_DIR)
    apod_count  = count_images(config.NASA_APOD_DIR)
    epic_count  = count_images(config.NASA_EPIC_DIR)

    return jsonify({
        "status":               "operational",
        "has_animation":        has_animation,
        "animation_last_updated": animation_time,
        "image_count":          rover_count + apod_count + epic_count,
        "rover_image_count":    rover_count,
        "apod_image_count":     apod_count,
        "epic_image_count":     epic_count,
        "current_time":         datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })


@app.route('/photos')
def view_photos():
    all_photos = []

    sources = [
        (config.NASA_IMAGES_DIR, '/photos/{}',      'Марсоход / Mars Rover', 'rover'),
        (config.NASA_APOD_DIR,   '/apod/image/{}',  'Фото дня / APOD',       'apod'),
        (config.NASA_EPIC_DIR,   '/epic/image/{}',  'EPIC (Земля / Earth)',   'epic'),
    ]

    for directory, url_pattern, label, photo_type in sources:
        if not directory.exists():
            continue
        try:
            for f in directory.iterdir():
                if f.suffix.lower() in ('.jpg', '.png'):
                    all_photos.append({
                        'path':   url_pattern.format(f.name),
                        'name':   f.name,
                        'date':   datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'source': label,
                        'type':   photo_type,
                    })
        except Exception as e:
            logger.error(f"Error reading {directory}: {e}")

    all_photos.sort(key=lambda x: x['date'], reverse=True)
    return render_template('photos.html', photos=all_photos)


@app.route('/photos/<filename>')
def get_photo(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    path = config.NASA_IMAGES_DIR / filename
    if not path.exists():
        abort(404)
    return send_file(path)


@app.route('/apod/image/<path:filename>')
def get_apod_image(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    path = config.NASA_APOD_DIR / filename
    if not path.exists():
        abort(404)
    return send_file(path)


@app.route('/epic/image/<path:filename>')
def get_epic_image(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    path = config.NASA_EPIC_DIR / filename
    if not path.exists():
        abort(404)
    return send_file(path)


@app.route('/epic/data')
def get_epic_data():
    try:
        return jsonify(nasa_epic.get_epic_photos())
    except Exception as e:
        logger.error(f"Error getting EPIC data: {e}")
        return jsonify({"error": "Could not fetch EPIC data"}), 500


@app.route('/apod/data')
def get_apod_data():
    try:
        return jsonify(nasa_apod.get_apod())
    except Exception as e:
        logger.error(f"Error getting APOD data: {e}")
        return jsonify({"error": "Could not fetch APOD data"}), 500


@app.route('/reviews', methods=['POST'])
def add_review():
    author = request.form.get('author', '').strip() or 'Аноним'
    text   = request.form.get('text', '').strip()
    rating = request.form.get('rating')
    if text:
        rating_int = int(rating) if rating and rating.isdigit() else None
        comments_db.add_comment('review', None, author, text, rating_int)
    return redirect(url_for('index') + '#reviews')


@app.route('/api/comments')
def api_get_comments():
    page_type = request.args.get('page_type', 'photo')
    item_id   = request.args.get('item_id')
    return jsonify(comments_db.get_comments(page_type, item_id))


@app.route('/api/photo-comment', methods=['POST'])
def api_add_photo_comment():
    data    = request.get_json(silent=True) or {}
    item_id = data.get('item_id', '').strip()
    author  = data.get('author', '').strip() or 'Аноним'
    text    = data.get('text', '').strip()
    if not text or not item_id:
        return jsonify({'error': 'text and item_id required'}), 400
    new_id = comments_db.add_comment('photo', item_id, author, text)
    return jsonify({'id': new_id, 'ok': True, 'author': author,
                    'text': text, 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')})


@app.route('/api/epic/visibility')
def api_epic_visibility():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        return jsonify({'error': 'lat and lon required as numbers'}), 400

    centroid_file = config.NASA_EPIC_DIR / 'centroid.json'
    if not centroid_file.exists():
        return jsonify({'error': 'No EPIC centroid data available yet'}), 404

    try:
        with open(centroid_file) as f:
            centroid = json.load(f)
    except Exception:
        return jsonify({'error': 'Could not read centroid data'}), 500

    clat = centroid.get('lat', 0)
    clon = centroid.get('lon', 0)

    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    lat2 = math.radians(clat)
    lon2 = math.radians(clon)
    dot  = (math.sin(lat1) * math.sin(lat2) +
            math.cos(lat1) * math.cos(lat2) * math.cos(lon1 - lon2))

    visible = dot > 0
    angle   = math.degrees(math.acos(max(-1.0, min(1.0, dot))))

    return jsonify({
        'visible':            visible,
        'angle_from_center':  round(angle, 1),
        'centroid_lat':       clat,
        'centroid_lon':       clon,
        'image_date':         centroid.get('date', 'unknown'),
    })


@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Страница не найдена / Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {e}")
    return render_template('index.html', error="Ошибка сервера / Server error"), 500
