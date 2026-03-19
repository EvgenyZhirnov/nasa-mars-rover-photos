"""
Flask web server for serving Mars Rover animations and photos.
"""
import os
import logging
from flask import Flask, render_template, send_file, jsonify, request, abort, url_for
from datetime import datetime

# Import other modules
import scheduler
import nasa_api
import nasa_apod
import nasa_epic
import utils

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "mars_rover_app_secret")

# Ensure data directories exist
os.makedirs("data/nasa_images", exist_ok=True)
os.makedirs("data/nasa_apod", exist_ok=True)
os.makedirs("data/nasa_epic", exist_ok=True)

# Start the schedulers
scheduler.start_schedulers()

# Get APOD on startup
try:
    apod_path, apod_data = nasa_apod.download_apod()
    if apod_path:
        logger.info(f"Downloaded APOD on startup: {apod_path}")
    elif apod_data and apod_data.get('media_type') != 'image':
        logger.info(f"APOD is not an image: {apod_data.get('media_type')}")
except Exception as e:
    logger.error(f"Error downloading APOD on startup: {e}")

# Get Mars Rover photos on startup
try:
    nasa_api.fetch_and_save_photos()
except Exception as e:
    logger.error(f"Error fetching Mars Rover photos on startup: {e}")

# Get EPIC photos on startup
try:
    epic_count, epic_paths = nasa_epic.download_all_epic_photos()
    if epic_count > 0:
        logger.info(f"Downloaded {epic_count} EPIC photos on startup")
    else:
        logger.warning("No EPIC photos available on startup")
except Exception as e:
    logger.error(f"Error downloading EPIC photos on startup: {e}")

@app.route('/')
def index():
    """Render the main page."""
    # Get APOD data
    apod_info = None
    apod_dir = "data/nasa_apod"
    
    if os.path.exists(apod_dir) and os.listdir(apod_dir):
        # Get the most recent APOD file
        apod_files = [os.path.join(apod_dir, f) for f in os.listdir(apod_dir) 
                     if os.path.isfile(os.path.join(apod_dir, f))]
        
        if apod_files:
            latest_apod = max(apod_files, key=os.path.getmtime)
            relative_path = os.path.relpath(latest_apod, apod_dir)
            
            # Get APOD data
            try:
                apod_data = nasa_apod.get_apod()
                if apod_data:
                    apod_info = {
                        'title': apod_data.get('title', 'Фото дня NASA'),
                        'date': apod_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'explanation': apod_data.get('explanation', ''),
                        'file_path': f"/apod/image/{relative_path}",
                        'media_type': apod_data.get('media_type', 'image'),
                        'url': apod_data.get('url', ''),
                        'copyright': apod_data.get('copyright', 'NASA')
                    }
            except Exception as e:
                logger.error(f"Error getting APOD data: {e}")
    
    return render_template('index.html', apod=apod_info)

@app.route('/animation')
def get_animation():
    """
    Serve the latest Mars Rover animation file.
    """
    animation_path = "data/nasa_animation.mp4"
    gif_path = "data/nasa_animation.gif"
    
    # Check if the animation file exists
    if os.path.exists(animation_path):
        logger.info(f"Serving animation file: {animation_path}")
        return send_file(animation_path, mimetype='video/mp4', as_attachment=True, 
                        download_name=f"mars_rover_animation_{datetime.now().strftime('%Y%m%d')}.mp4")
    elif os.path.exists(gif_path):
        logger.info(f"Serving GIF animation file: {gif_path}")
        return send_file(gif_path, mimetype='image/gif', as_attachment=True,
                        download_name=f"mars_rover_animation_{datetime.now().strftime('%Y%m%d')}.gif")
    else:
        logger.error("Animation file not found")
        return render_template('animation.html', error="Файл анимации пока недоступен. Пожалуйста, проверьте позже.")

@app.route('/animation/view')
def view_animation():
    """
    View the latest Mars Rover animation in the browser.
    """
    return render_template('animation.html', error=None)

@app.route('/status')
def status():
    """
    Get the application status.
    """
    animation_path = "data/nasa_animation.mp4"
    gif_path = "data/nasa_animation.gif"
    
    # Check animations
    has_animation = os.path.exists(animation_path) or os.path.exists(gif_path)
    animation_path = animation_path if os.path.exists(animation_path) else gif_path if os.path.exists(gif_path) else None
    animation_time = None
    
    if animation_path and os.path.exists(animation_path):
        animation_time = datetime.fromtimestamp(os.path.getmtime(animation_path)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Check images directories
    rover_dir = "data/nasa_images"
    apod_dir = "data/nasa_apod"
    epic_dir = "data/nasa_epic"
    
    # Make sure the directories exist
    try:
        os.makedirs(rover_dir, exist_ok=True)
        os.makedirs(apod_dir, exist_ok=True)
        os.makedirs(epic_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        
    # Initialize counters
    has_images = False
    rover_count = 0
    apod_count = 0
    epic_count = 0
    
    # Check Mars Rover images
    if os.path.exists(rover_dir):
        try:
            rover_files = [f for f in os.listdir(rover_dir) if f.endswith(('.jpg', '.png'))]
            rover_count = len(rover_files)
        except Exception as e:
            logger.error(f"Error checking rover images directory: {e}")
    
    # Check APOD images
    if os.path.exists(apod_dir):
        try:
            apod_files = [f for f in os.listdir(apod_dir) if f.endswith(('.jpg', '.png'))]
            apod_count = len(apod_files)
        except Exception as e:
            logger.error(f"Error checking APOD directory: {e}")
            
    # Check EPIC images
    if os.path.exists(epic_dir):
        try:
            epic_files = [f for f in os.listdir(epic_dir) if f.endswith(('.jpg', '.png'))]
            epic_count = len(epic_files)
        except Exception as e:
            logger.error(f"Error checking EPIC directory: {e}")
    
    # Total image count
    total_image_count = rover_count + apod_count + epic_count
    has_images = total_image_count > 0
    
    status_data = {
        "status": "operational",
        "has_animation": has_animation,
        "animation_last_updated": animation_time,
        "total_image_count": total_image_count,
        "rover_image_count": rover_count,
        "apod_image_count": apod_count,
        "epic_image_count": epic_count,
        "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return jsonify(status_data)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    logger.error(f"404 error: {e}")
    return render_template('index.html', error="Страница не найдена"), 404

@app.route('/photos')
def view_photos():
    """View all photos: Mars Rover photos, APOD, and EPIC."""
    all_photos = []
    
    # Make sure the directories exist
    try:
        os.makedirs("data/nasa_images", exist_ok=True)
        os.makedirs("data/nasa_apod", exist_ok=True)
        os.makedirs("data/nasa_epic", exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
    
    # Process images from all sources
    try:
        # Mars Rover photos
        rover_dir = "data/nasa_images"
        if os.path.exists(rover_dir):
            for file in os.listdir(rover_dir):
                if file.endswith(('.jpg', '.png')):
                    all_photos.append({
                        'path': f'/photos/{file}',
                        'name': file,
                        'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(rover_dir, file))).strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'Марсоход',
                        'type': 'rover'
                    })
        
        # APOD photos
        apod_dir = "data/nasa_apod"
        if os.path.exists(apod_dir):
            for file in os.listdir(apod_dir):
                if file.endswith(('.jpg', '.png')):
                    all_photos.append({
                        'path': f'/apod/image/{file}',
                        'name': file,
                        'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(apod_dir, file))).strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'Фото дня NASA',
                        'type': 'apod'
                    })
        
        # EPIC photos
        epic_dir = "data/nasa_epic"
        if os.path.exists(epic_dir):
            for file in os.listdir(epic_dir):
                if file.endswith(('.jpg', '.png')):
                    all_photos.append({
                        'path': f'/epic/image/{file}',
                        'name': file,
                        'date': datetime.fromtimestamp(os.path.getmtime(os.path.join(epic_dir, file))).strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'EPIC (Земля из космоса)',
                        'type': 'epic'
                    })
        
        # Sort by modification time, newest first
        if all_photos:
            all_photos.sort(key=lambda x: x['date'], reverse=True)
    
    except Exception as e:
        logger.error(f"Error processing photos: {e}")
    
    return render_template('photos.html', photos=all_photos)

@app.route('/photos/<filename>')
def get_photo(filename):
    """Serve a Mars Rover photo."""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    file_path = os.path.join("data/nasa_images", filename)
    if not os.path.exists(file_path):
        logger.error(f"Requested photo not found: {file_path}")
        abort(404)
    
    return send_file(file_path)

@app.route('/apod/image/<path:filename>')
def get_apod_image(filename):
    """Serve an APOD image."""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    file_path = os.path.join("data/nasa_apod", filename)
    if not os.path.exists(file_path):
        logger.error(f"Requested APOD not found: {file_path}")
        abort(404)
    
    return send_file(file_path)

@app.route('/epic/image/<path:filename>')
def get_epic_image(filename):
    """Serve an EPIC image."""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    file_path = os.path.join("data/nasa_epic", filename)
    if not os.path.exists(file_path):
        logger.error(f"Requested EPIC photo not found: {file_path}")
        abort(404)
    
    return send_file(file_path)

@app.route('/epic/data')
def get_epic_data():
    """Get the latest EPIC data as JSON."""
    try:
        epic_data = nasa_epic.get_epic_photos()
        return jsonify(epic_data)
    except Exception as e:
        logger.error(f"Error getting EPIC data: {e}")
        return jsonify({"error": "Could not fetch EPIC data"}), 500
        
@app.route('/apod/data')
def get_apod_data():
    """Get the current APOD data as JSON."""
    try:
        apod_data = nasa_apod.get_apod()
        return jsonify(apod_data)
    except Exception as e:
        logger.error(f"Error getting APOD data: {e}")
        return jsonify({"error": "Could not fetch APOD data"}), 500

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"500 error: {e}")
    return render_template('index.html', error="Ошибка сервера. Пожалуйста, попробуйте позже."), 500
