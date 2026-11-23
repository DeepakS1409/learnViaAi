import os
from flask import Flask
from app.config import Config
from app.auth import get_current_user

from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db_dir = os.path.dirname(app.config['DATABASE_PATH'])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.student import student_bp
    from app.routes.faculty import faculty_bp
    from app.routes.admin import admin_bp
    from app.routes.materials_routes import materials_bp
    from app.routes.chat_routes import chat_bp
    from app.routes.profile_routes import profile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(profile_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'current_user': get_current_user(),
            'current_year': datetime.now().year,
            'app_name': 'Padika AI'
        }

    # Custom Jinja filters
    @app.template_filter('filesizeformat')
    def filesize_filter(bytes_val):
        try:
            bytes_val = float(bytes_val)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.1f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.1f} TB"
        except Exception:
            return "0 B"

    @app.template_filter('datetimeformat')
    def datetime_filter(val, format='%b %d, %Y'):
        if not val:
            return ""
        if isinstance(val, str):
            try:
                # Handle SQLite timestamp 'YYYY-MM-DD HH:MM:SS'
                dt = datetime.strptime(val.split('.')[0], '%Y-%m-%d %H:%M:%S')
                return dt.strftime(format)
            except Exception:
                return val
        elif isinstance(val, datetime):
            return val.strftime(format)
        return str(val)

    return app
