from flask import Flask, render_template
from sqlalchemy.orm import scoped_session, sessionmaker
from connect_connector import connect_with_connector
from routes.antigrams import register_antigram_routes
from routes.antibody_id import register_antibody_id_routes
from routes.cell_finder import register_cell_finder_routes
from models import Base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set up the SQLAlchemy engine and session
engine = connect_with_connector()
db_session = scoped_session(sessionmaker(bind=engine))

# Initialize the database schema for SQLite
# Only runs when using SQLite
if "sqlite" in str(engine.url):
    Base.metadata.create_all(bind=engine)
    print("SQLite database initialized")

# Register routes, passing the database session
register_antigram_routes(app, db_session)
register_antibody_id_routes(app, db_session)
register_cell_finder_routes(app, db_session)

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
    app.run(debug=True)
