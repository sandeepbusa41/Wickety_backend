from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate  # Import Flask-Migrate
from dotenv import load_dotenv
import os
import pusher
from flask_cors import CORS

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Migrate
migrate = Migrate()  # Create a Migrate instance

# Load environment variables
load_dotenv()

# Initialize Pusher at the module level
pusher_client = pusher.Pusher(
    app_id=os.getenv('PUSHER_APP_ID'),
    key=os.getenv('PUSHER_KEY'),
    secret=os.getenv('PUSHER_SECRET'),
    cluster=os.getenv('PUSHER_CLUSTER'),
    ssl=True
)

def create_app():
    app = Flask(__name__)

    # Flask configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the app and db

    # Configure CORS to allow requests from http://localhost:3000
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app