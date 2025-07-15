from flask import Flask, request, jsonify
from flask_cors import CORS
from src.models.user import db, User, Project, ProjectFile, Session as UserSession
from src.routes.user import user_bp
import os
from datetime import datetime

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "neoncode-secret-key-2024")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///neoncode.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Enable CORS for all routes
    CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix="/api")
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@neoncode.dev",
                full_name="NeonCode Administrator"
            )
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
            print("Created default admin user: admin/admin123")
    
    # Root route
    @app.route("/")
    def index():
        return jsonify({
            "message": "NeonCode Backend API",
            "version": "2.0.0",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "health": "/api/health",
                "register": "/api/register",
                "login": "/api/login",
                "logout": "/api/logout",
                "profile": "/api/profile",
                "projects": "/api/projects"
            }
        })
    
    # Health check route
    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "service": "NeonCode Backend API"
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden"}), 403
    
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Run the application
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"Starting NeonCode Backend API on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )


