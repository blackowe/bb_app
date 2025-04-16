from flask import Flask, render_template
from sqlalchemy.orm import scoped_session, sessionmaker
from connect_connector import connect_with_connector
from routes.antigrams import register_antigram_routes
from routes.antibody_id import register_antibody_id_routes
from routes.cell_finder import register_cell_finder_routes
from routes.add_antigram import register_add_antigram_routes
from routes.antigen_rules import register_antigen_rules_routes, initialize_default_rules
from routes.antigens import register_antigen_routes
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from models import Base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    print("SQLite database initialized")
    
    # Initialize default rules
    try:
        with app.app_context():
            initialize_default_rules(db_session)
            print("Default rules initialized successfully")
    except Exception as e:
        print(f"Error initializing default rules: {str(e)}")

# Register routes, passing the database session
register_antigen_routes(app, db_session)
register_antigram_routes(app, db_session)
register_antibody_id_routes(app, db_session)
register_cell_finder_routes(app, db_session)
register_add_antigram_routes(app, db_session)
register_antigen_rules_routes(app, db_session)

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Ensure the scoped session is removed after each request to
    avoid connection leaks.
    """
    db_session.remove()

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

