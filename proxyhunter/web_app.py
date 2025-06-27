"""Modern Flask web dashboard for ProxyHunter."""

from .i18n import get_translation, get_supported_languages, get_language_name
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
from .proxy_session import ProxySession, TrafficMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='public')
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'proxy-hunter-secret-key')

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

# Global ProxyHunter instance
proxy_hunter: Optional[ProxyHunter] = None
refresh_lock = threading.Lock()
last_refresh_time = 0

# Global traffic monitor for web dashboard monitoring
global_traffic_monitor = TrafficMonitor()

# Active proxy sessions tracking
active_sessions = weakref.WeakSet()

# WebSocket clients management (使用普通集合存储session ID)
connected_clients = set()

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

        # Get traffic statistics
        traffic_stats = global_traffic_monitor.get_stats()

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
            traffic_stats=traffic_stats,
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
            traffic_stats={},
            last_updated='N/A'
        )


@app.route("/traffic")
def traffic_dashboard():
    """Traffic monitoring dashboard page."""
    lang = request.args.get("lang", "en")
    trans = get_translation(lang)

    try:
        # Get traffic statistics
        traffic_stats = global_traffic_monitor.get_stats()
        recent_traffic = global_traffic_monitor.get_recent_traffic(100)

        # Get active sessions status
        active_session_count = len(active_sessions)

        return render_template(
            'traffic.html',
            lang=lang,
            trans=trans,
            traffic_stats=traffic_stats,
            recent_traffic=recent_traffic,
            active_sessions=active_session_count,
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    except Exception as e:
        logger.error(f"Error in traffic route: {e}")
        return render_template(
            'traffic.html',
            lang=lang,
            trans=trans,
            traffic_stats={},
            recent_traffic=[],
            active_sessions=0,
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
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Error in api_data: {e}")
        return jsonify({
            "total": 0,
            "success": 0,
            "fail": 0,
            "average": 0,
            "last_updated": "Error"
        }), 500


@app.route("/api/traffic/stats")
def api_traffic_stats():
    """Get current traffic statistics."""
    try:
        traffic_stats = global_traffic_monitor.get_stats()
        traffic_stats['active_sessions'] = len(active_sessions)
        traffic_stats['last_updated'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')

        return jsonify(traffic_stats)

    except Exception as e:
        logger.error(f"Error in api_traffic_stats: {e}")
        return jsonify({
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "unique_proxies": 0,
            "avg_response_time": 0,
            "total_data": 0,
            "session_duration": 0,
            "active_sessions": 0,
            "last_updated": "Error"
        }), 500


@app.route("/api/traffic/recent")
def api_traffic_recent():
    """Get recent traffic logs."""
    try:
        limit = min(int(request.args.get('limit', 50)), 200)  # Max 200 entries
        recent_traffic = global_traffic_monitor.get_recent_traffic(limit)

        return jsonify({
            "traffic": recent_traffic,
            "count": len(recent_traffic),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Error in api_traffic_recent: {e}")
        return jsonify({
            "traffic": [],
            "count": 0,
            "last_updated": "Error"
        }), 500


@app.route("/api/traffic/clear", methods=["POST"])
def api_traffic_clear():
    """Clear traffic logs."""
    try:
        global_traffic_monitor.clear_logs()
        return jsonify({"status": "success", "message": "Traffic logs cleared"})
    except Exception as e:
        logger.error(f"Error clearing traffic logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/proxy/session", methods=["POST"])
def api_create_proxy_session():
    """Create a new monitored proxy session."""
    try:
        data = request.get_json() or {}

        # Create new proxy session
        session = ProxySession(
            proxy_count=data.get('proxy_count', 10),
            rotation_strategy=data.get('rotation_strategy', 'round_robin'),
            country_filter=data.get('country_filter'),
            anonymous_only=data.get('anonymous_only', True)
        )

        # Add to active sessions
        active_sessions.add(session)

        # Get session status
        status = session.get_proxy_status()

        return jsonify({
            "status": "success",
            "message": "Proxy session created",
            "session_id": id(session),
            "proxy_status": status
        })

    except Exception as e:
        logger.error(f"Error creating proxy session: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/favicon.ico")
def favicon():
    """Serve favicon."""
    try:
        favicon_path = Path(__file__).parent / 'public' / 'favicon.ico'
        if favicon_path.exists():
            return send_file(str(favicon_path))
    except Exception:
        pass
    return '', 404


@app.route("/api/export")
def api_export():
    """Export proxy data in various formats."""
    try:
        export_format = request.args.get('format', 'txt').lower()
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000

        hunter = get_hunter()
        working_proxies = hunter.get_working_proxies(limit=limit)

        if not working_proxies:
            return jsonify({"error": "No working proxies available"}), 404

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f'.{export_format}')

        try:
            if export_format == 'txt':
                with open(temp_file.name, 'w') as f:
                    for proxy in working_proxies:
                        f.write(f"{proxy['proxy']}\n")
                mimetype = 'text/plain'

            elif export_format == 'json':
                with open(temp_file.name, 'w') as f:
                    json.dump(working_proxies, f, indent=2)
                mimetype = 'application/json'

            elif export_format == 'csv':
                with open(temp_file.name, 'w', newline='') as f:
                    if working_proxies:
                        writer = csv.DictWriter(
                            f, fieldnames=working_proxies[0].keys())
                        writer.writeheader()
                        writer.writerows(working_proxies)
                mimetype = 'text/csv'

            else:
                return jsonify({"error": "Unsupported format"}), 400

            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'proxies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{export_format}',
                mimetype=mimetype
            )

        finally:
            # Clean up temp file after a delay
            def cleanup():
                time.sleep(10)
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

            threading.Thread(target=cleanup, daemon=True).start()

    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# WebSocket event handlers


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    connected_clients.add(request.sid)
    logger.info(f"Client {request.sid} connected")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    connected_clients.discard(request.sid)
    logger.info(f"Client {request.sid} disconnected")


@socketio.on('request_stats')
def handle_stats_request():
    """Handle request for statistics update."""
    try:
        hunter = get_hunter()
        stats = hunter.get_statistics()

        response_stats = stats.get('response_time_stats', {})
        avg_response_time = response_stats.get('avg_response_time', 0)
        if avg_response_time is not None and avg_response_time > 0:
            avg_response_time = round(float(avg_response_time), 3)
        else:
            avg_response_time = 0

        # Get traffic stats
        traffic_stats = global_traffic_monitor.get_stats()

        emit('stats_update', {
            "total": stats.get('total_proxies', 0),
            "success": stats.get('working_proxies', 0),
            "fail": stats.get('failed_proxies', 0),
            "average": avg_response_time,
            "traffic": traffic_stats,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Error handling stats request: {e}")


@socketio.on('request_traffic')
def handle_traffic_request():
    """Handle request for traffic data update."""
    try:
        traffic_stats = global_traffic_monitor.get_stats()
        recent_traffic = global_traffic_monitor.get_recent_traffic(50)

        emit('traffic_update', {
            "stats": traffic_stats,
            "recent": recent_traffic,
            "active_sessions": len(active_sessions),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Error handling traffic request: {e}")


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

        # Get traffic stats
        traffic_stats = global_traffic_monitor.get_stats()

        socketio.emit('stats_update', {
            "total": stats.get('total_proxies', 0),
            "success": stats.get('working_proxies', 0),
            "fail": stats.get('failed_proxies', 0),
            "average": avg_response_time,
            "traffic": traffic_stats,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        last_broadcast_time = current_time

    except Exception as e:
        logger.error(f"Error broadcasting stats: {e}")


def broadcast_traffic_update():
    """Broadcast traffic update to all connected clients."""
    try:
        traffic_stats = global_traffic_monitor.get_stats()
        recent_traffic = global_traffic_monitor.get_recent_traffic(
            10)  # Only recent 10 for real-time

        socketio.emit('traffic_update', {
            "stats": traffic_stats,
            "recent": recent_traffic,
            "active_sessions": len(active_sessions),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Error broadcasting traffic: {e}")


@app.template_filter('filesizeformat')
def filesizeformat(value):
    """Format file size in human readable format."""
    try:
        value = float(value)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"
    except (ValueError, TypeError):
        return "0 B"

# Global traffic monitoring middleware


class TrafficLoggingMiddleware:
    """Middleware to log proxy traffic from ProxySession instances."""

    def __init__(self, app, traffic_monitor):
        self.app = app
        self.traffic_monitor = traffic_monitor

    def __call__(self, environ, start_response):
        # This middleware can be used to intercept and log traffic
        # For now, we rely on ProxySession to log traffic directly
        return self.app(environ, start_response)


# Apply middleware
app.wsgi_app = TrafficLoggingMiddleware(app.wsgi_app, global_traffic_monitor)

# Auto-cleanup function for memory management


def cleanup_inactive_sessions():
    """Cleanup inactive sessions periodically."""
    while True:
        try:
            time.sleep(300)  # Run every 5 minutes
            # WeakSet automatically removes unreferenced sessions
            logger.info(f"Active sessions: {len(active_sessions)}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Start cleanup thread
cleanup_thread = threading.Thread(
    target=cleanup_inactive_sessions, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    # Development server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
