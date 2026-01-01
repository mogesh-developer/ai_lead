"""
AI Lead Outreach Backend - Flask Application
Main entry point for the application with modular architecture
"""
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database module
try:
    import db
    db.init_db()
    print("[OK] Database initialized")
except Exception as e:
    print(f"[WARN] Database initialization warning: {e}")

# Import configuration (lazy loading for APIs)
try:
    from config import GEMINI_API_KEY, GROQ_API_KEY, get_genai, get_groq
    print("[OK] Configuration loaded (APIs will load on first use)")
except Exception as e:
    print(f"[ERROR] Error loading configuration: {e}")
    sys.exit(1)

# Import routes
try:
    from routes import api
    print("✅ Routes loaded")
except Exception as e:
    print(f"❌ Error loading routes: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Add OPTIONS method support for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

# Register API blueprint
app.register_blueprint(api)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "gemini": bool(GEMINI_API_KEY),
        "groq": bool(GROQ_API_KEY),
        "version": "1.0.0"
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    print(f"\n[START] AI Lead Outreach Backend starting...")
    print(f"[INFO] Running on http://localhost:{port}")
    print(f"[INFO] API endpoint: http://localhost:{port}/api")
    print(f"[INFO] Health check: http://localhost:{port}/health")
    print(f"[OK] Press CTRL+C to stop\n")
    app.run(host='0.0.0.0', port=port, debug=False)
