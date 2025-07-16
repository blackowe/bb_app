from flask import Flask, render_template, request
from sqlalchemy.orm import scoped_session, sessionmaker
import logging
from connect_connector import connect_with_connector
from api.antigram_routes import register_antigram_routes
from api.antibody_routes import register_antibody_routes
from api.utility_routes import register_utility_routes
from api.antigen_routes import register_antigen_routes
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager, PandasTemplateManager

import json
import os
import time

from models import Base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Set up the SQLAlchemy engine and session
engine = connect_with_connector()
db_session = scoped_session(sessionmaker(bind=engine))

# Initialize the database schema for SQLite
# Only runs when using SQLite
if "sqlite" in str(engine.url):
    Base.metadata.create_all(bind=engine)
    logger.info("SQLite database initialized")
    
    # Initialize default rules
    try:
        with app.app_context():
            from default_rules import get_default_rules
            from models import AntigenRule
            
            # Clear existing rules
            db_session.query(AntigenRule).delete()
            
            # Get default rules
            default_rules = get_default_rules()
            
            # Add new rules
            for rule_data in default_rules:
                rule = AntigenRule(**rule_data)
                db_session.add(rule)
            
            db_session.commit()
            logger.info("Default rules initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing default rules: {str(e)}")

# Initialize pandas managers
antigram_manager = PandasAntigramManager(db_session)
patient_reaction_manager = PandasPatientReactionManager(db_session)
template_manager = PandasTemplateManager(db_session) 

# Load existing data from database
try:
    antigram_manager.load_from_database(db_session)
    patient_reaction_manager.load_from_database(db_session)
    template_manager.load_from_database(db_session)
    logger.info("✅ Loaded existing antigram, patient reaction, and template data from database")
except Exception as e:
    logger.warning(f"⚠️  Error loading existing data from database: {e}")
    logger.info("Starting with empty data - this is normal for first run")

# Store managers in Flask app context for access in routes
app.config['antigram_manager'] = antigram_manager
app.config['patient_reaction_manager'] = patient_reaction_manager
app.config['template_manager'] = template_manager


# Register routes, passing the database session
register_antigen_routes(app, db_session)
register_antigram_routes(app, db_session)
register_antibody_routes(app, db_session)
register_utility_routes(app, db_session)


@app.before_request
def start_timer():
    """Start timer for request performance monitoring"""
    request.start_time = time.time()

@app.before_request
def log_request_info():
    """Log incoming request information"""
    logger.info(f"Request: {request.method} {request.url}")
    if request.method == 'POST':
        logger.info(f"Request data: {request.get_json() if request.is_json else request.form}")

@app.after_request
def log_response_info(response):
    """Log response information with performance metrics"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.info(f"Response: {response.status_code} for {request.method} {request.url} - Duration: {duration:.3f}s")
    else:
        logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
    return response

@app.route("/")
def home():
    return render_template("home.html")

@app.teardown_appcontext
def save_data_on_shutdown(exception=None):
    """Save all data to database when the app context is torn down."""
    try:
        if 'antigram_manager' in app.config:
            app.config['antigram_manager'].save_all_to_database()
        if 'patient_reaction_manager' in app.config:
            app.config['patient_reaction_manager'].save_all_to_database()
        if 'template_manager' in app.config:
            app.config['template_manager'].save_all_to_database()
        logger.info("Data saved to database on shutdown")
    except Exception as e:
        logger.error(f"Error saving data on shutdown: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

