"""
FindIt Campus — Flask Application Factory
Creates and configures the Flask application with all extensions.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from config import get_config

# Initialize extensions (created here, bound to app in create_app)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=None):
    """
    Application factory pattern.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    ma.init_app(app)
    # Use memory storage for rate limiter when Redis is not configured (e.g. Vercel)
    if not app.config.get('REDIS_URL'):
        app.config['RATELIMIT_STORAGE_URI'] = 'memory://'
    limiter.init_app(app)

    # Configure CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
         supports_credentials=True)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register JWT callbacks
    _register_jwt_callbacks(app)

    # Create database tables
    with app.app_context():
        from app.models import student, account, lost_item, found_item, question_answer, match, claim, notification
        from app.models import messaging  # Message + PushSubscription
        db.create_all()

    return app


def _register_blueprints(app):
    """Register all API blueprints."""
    from app.routes.auth_routes import auth_routes_bp
    from app.routes.lost_routes import lost_routes_bp
    from app.routes.found_routes import found_routes_bp
    from app.routes.match_routes import match_routes_bp
    from app.routes.claim_routes import claim_routes_bp
    from app.routes.notification_routes import notification_routes_bp
    from app.routes.profile_routes import profile_routes_bp
    from app.routes.upload import upload_bp
    from app.routes.pages import pages_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.routes.feature_routes import (
        leaderboard_bp, stats_bp, timeline_bp, map_bp,
        push_bp, message_bp, import_bp
    )

    app.register_blueprint(auth_routes_bp, url_prefix='/api/auth')
    app.register_blueprint(lost_routes_bp, url_prefix='/api/lost')
    app.register_blueprint(found_routes_bp, url_prefix='/api/found')
    app.register_blueprint(match_routes_bp, url_prefix='/api/match')
    app.register_blueprint(claim_routes_bp, url_prefix='/api/claim')
    app.register_blueprint(claim_routes_bp, url_prefix='/api/claims', name='claims_routes_bp')
    app.register_blueprint(notification_routes_bp, url_prefix='/api/notifications')
    app.register_blueprint(profile_routes_bp, url_prefix='/api/profile')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(timeline_bp, url_prefix='/api/timeline')
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(push_bp, url_prefix='/api/push')
    app.register_blueprint(message_bp, url_prefix='/api/messages')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(pages_bp, url_prefix='/')


def _register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad Request', 'message': str(error)}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'You do not have permission to access this resource'}, 403

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found', 'message': 'The requested resource was not found'}, 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {'error': 'Too Many Requests', 'message': 'Rate limit exceeded. Please try again later.'}, 429

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500


def _register_jwt_callbacks(app):
    """Register JWT error callbacks for better error messages."""

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token Expired', 'message': 'Your session has expired. Please log in again.'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid Token', 'message': 'The provided token is invalid.'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Missing Token', 'message': 'Authentication token is required.'}, 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {'error': 'Revoked Token', 'message': 'This token has been revoked.'}, 401
