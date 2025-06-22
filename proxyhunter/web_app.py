"""Modern Flask web dashboard for ProxyHunter."""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, request, render_template, jsonify, send_file
from flask_socketio import SocketIO, emit
import tempfile
import csv
import io
import weakref

from .core import ProxyHunter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='public')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'proxy-hunter-secret-key')

# Initialize SocketIO with memory-efficient settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
    async_mode='threading',
    max_http_buffer_size=1024*1024  # 1MB limit
)

# Import i18n support
from .i18n import get_translation, get_supported_languages, get_language_name

# Global ProxyHunter instance
proxy_hunter: Optional[ProxyHunter] = None
refresh_lock = threading.Lock()
last_refresh_time = 0

# WebSocket clients management (使用弱引用避免記憶體洩漏)
connected_clients = weakref.WeakSet()

# Rate limiting for WebSocket events
last_broadcast_time = 0
BROADCAST_COOLDOWN = 2  # seconds

def get_hunter() -> ProxyHunter:
    """Get or create ProxyHunter instance."""
    global proxy_hunter
    if proxy_hunter is None:
        db_path = Path(__file__).parent.parent / 'db' / 'proxy_dashboard.db'
        proxy_hunter = ProxyHunter(
            threads=20,
            timeout=10,
            db_path=str(db_path)
        )
    return proxy_hunter

# get_translation function is now imported from i18n module

@app.route("/")
def index() -> str:
    """Main dashboard page."""
    lang = request.args.get("lang", "en")
    trans = get_translation(lang)
    
    try:
        hunter = get_hunter()
        stats = hunter.get_statistics()
        
        # Get recent working proxies for display
        working_proxies = hunter.get_working_proxies(limit=100)
        
        # Prepare chart data
        chart_data = []
        for proxy in working_proxies[:20]:  # Limit to top 20 for chart
            if proxy.get('response_time'):
                chart_data.append({
                    'proxy': proxy['proxy'],
                    'response_time': proxy['response_time']
                })
        
        # Calculate statistics
        total_proxies = stats.get('total_proxies', 0)
        working_count = stats.get('working_proxies', 0)
        failed_count = stats.get('failed_proxies', 0)
        
        response_stats = stats.get('response_time_stats', {})
        avg_response_time = response_stats.get('avg_response_time', 0)
        if avg_response_time is not None and avg_response_time > 0:
            avg_response_time = round(float(avg_response_time), 3)
        else:
            avg_response_time = 0
        
        return render_template(
            'index.html',
            lang=lang,
            trans=trans,
            results=working_proxies,
            chart_data=json.dumps(chart_data),
            total=total_proxies,
            success=working_count,
            fail=failed_count,
            average=avg_response_time,
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template(
            'index.html',
            lang=lang,
            trans=trans,
            results=[],
            chart_data=json.dumps([]),
            total=0,
            success=0,
            fail=0,
            average=0,
            last_updated='N/A'
        )

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Start proxy refresh in background."""
    global last_refresh_time
    
    # Prevent too frequent refreshes
    current_time = time.time()
    if current_time - last_refresh_time < 30:  # 30 seconds cooldown
        return jsonify({
            "status": "error",
            "message": "Please wait before refreshing again"
        }), 429
    
    if refresh_lock.locked():
        return jsonify({
            "status": "error", 
            "message": "Refresh already in progress"
        }), 409
    
    def refresh_task():
        """Background refresh task."""
        global last_refresh_time
        with refresh_lock:
            try:
                hunter = get_hunter()
                logger.info("Starting proxy refresh...")
                
                # Fetch new proxies
                proxies = hunter.fetch_proxies()
                logger.info(f"Fetched {len(proxies)} proxies")
                
                # Validate proxies
                results = hunter.validate_proxies(proxies)
                logger.info(f"Validated {len(results)} proxies")
                
                # Save to database
                hunter.save_to_database(results)
                logger.info("Saved results to database")
                
                # Broadcast update to WebSocket clients
                broadcast_stats_update()
                
                last_refresh_time = time.time()
                
            except Exception as e:
                logger.error(f"Refresh task error: {e}")
    
    # Start background task
    thread = threading.Thread(target=refresh_task, daemon=True)
    thread.start()
    
    return jsonify({"status": "started"})

@app.route("/api/data")
def api_data():
    """Get current proxy statistics."""
    try:
        hunter = get_hunter()
        stats = hunter.get_statistics()
        
        response_stats = stats.get('response_time_stats', {})
        avg_response_time = response_stats.get('avg_response_time', 0)
        if avg_response_time is not None and avg_response_time > 0:
            avg_response_time = round(float(avg_response_time), 3)
        else:
            avg_response_time = 0
        
        return jsonify({
            "total": stats.get('total_proxies', 0),
            "success": stats.get('working_proxies', 0),
            "fail": stats.get('failed_proxies', 0),
            "average": avg_response_time,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in api_data: {e}")
        return jsonify({
            "total": 0,
            "success": 0,
            "fail": 0,
            "average": 0,
            "last_updated": "N/A"
        })

@app.route("/favicon.ico")
def favicon():
    """Serve favicon.ico to avoid 404 errors."""
    # Return a simple 1x1 transparent GIF as favicon
    import base64
    transparent_gif = base64.b64decode(
        'R0lGODlhAQABAID/AMDAwAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='
    )
    from flask import Response
    return Response(transparent_gif, mimetype='image/gif')

@app.route("/api/export")
def api_export():
    """Export proxy data in various formats."""
    try:
        format_type = request.args.get('format', 'txt').lower()
        status_filter = request.args.get('status', 'ok').lower()
        
        hunter = get_hunter()
        
        if status_filter == 'ok':
            proxies = hunter.get_working_proxies()
        else:
            proxies = hunter.get_working_proxies()
        
        if format_type == 'json':
            output = json.dumps(proxies, indent=2, ensure_ascii=False)
            mimetype = 'application/json'
            filename = 'proxies.json'
            
        elif format_type == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['proxy', 'status', 'response_time', 'data_size'])
            writer.writeheader()
            for proxy in proxies:
                writer.writerow({
                    'proxy': proxy.get('proxy', ''),
                    'status': proxy.get('status', ''),
                    'response_time': proxy.get('response_time', ''),
                    'data_size': proxy.get('data_size', '')
                })
            output = output.getvalue()
            mimetype = 'text/csv'
            filename = 'proxies.csv'
            
        else:  # txt format
            output = '\n'.join([proxy.get('proxy', '') for proxy in proxies])
            mimetype = 'text/plain'
            filename = 'proxies.txt'
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'.{format_type}')
        temp_file.write(output)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    
@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_stats')
def handle_stats_request():
    """Handle request for current statistics."""
    try:
        hunter = get_hunter()
        stats = hunter.get_statistics()
        
        response_stats = stats.get('response_time_stats', {})
        avg_response_time = response_stats.get('avg_response_time', 0)
        if avg_response_time is not None and avg_response_time > 0:
            avg_response_time = round(float(avg_response_time), 3)
        else:
            avg_response_time = 0
        
        emit('stats_update', {
            "total": stats.get('total_proxies', 0),
            "success": stats.get('working_proxies', 0),
            "fail": stats.get('failed_proxies', 0),
            "average": avg_response_time,
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error handling stats request: {e}")
        emit('error', {'message': str(e)})

def broadcast_stats_update():
    """Broadcast statistics update to all connected clients."""
    global last_broadcast_time
    current_time = time.time()
    
    # Rate limiting
    if current_time - last_broadcast_time < BROADCAST_COOLDOWN:
        return
    
    try:
        hunter = get_hunter()
        stats = hunter.get_statistics()
        
        response_stats = stats.get('response_time_stats', {})
        avg_response_time = response_stats.get('avg_response_time', 0)
        if avg_response_time is not None and avg_response_time > 0:
            avg_response_time = round(float(avg_response_time), 3)
        else:
            avg_response_time = 0
        
        socketio.emit('stats_update', {
            "total": stats.get('total_proxies', 0),
            "success": stats.get('working_proxies', 0),
            "fail": stats.get('failed_proxies', 0),
            "average": avg_response_time,
            "last_updated": datetime.now().isoformat()
        })
        
        last_broadcast_time = current_time
        
    except Exception as e:
        logger.error(f"Error broadcasting stats: {e}")

# Custom filters for Jinja2
@app.template_filter('filesizeformat')
def filesizeformat(value):
    """Format file size in human readable format."""
    try:
        value = int(value)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
    except (ValueError, TypeError):
        return "0 B"

if __name__ == "__main__":
    import os
    is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG', '').lower() in ('true', '1')
    
    if is_development:
        logger.warning("Running in development mode. For production, use a WSGI server like Gunicorn.")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=True)
    else:
        # 生產環境建議
        logger.info("Starting ProxyHunter web interface with WebSocket support...")
        logger.info("For production deployment, consider using:")
        logger.info("  gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 proxyhunter.web_app:app")
        logger.info("  or with uwsgi: uwsgi --http 0.0.0.0:5000 --gevent 1000 --http-websockets --master --wsgi-file proxyhunter/web_app.py --callable app")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
