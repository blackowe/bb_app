from sqlalchemy import create_engine, text, inspect
from models import Base
from connect_connector import connect_with_connector
import json
import logging

logger = logging.getLogger(__name__)

def initialize_database():
    """
    Create and initialize the database schema for the pandas-based system.
    """
    engine = connect_with_connector()

    # Create tables from SQLAlchemy models
    Base.metadata.create_all(engine)

    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()
