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

    # Additional schema updates
    with engine.connect() as conn:
        # Add new columns to antigen_rules table if they don't exist (SQLite)
        if "sqlite" in str(engine.url):
            try:
                # Check if rule_conditions column exists
                conn.execute(text("SELECT rule_conditions FROM antigen_rules LIMIT 1"))
            except Exception:
                # First, add the new column
                conn.execute(text("""
                ALTER TABLE antigen_rules
                ADD COLUMN rule_conditions TEXT
                """))
                
                # Then migrate data from rule_antigens to rule_conditions
                rows = conn.execute(text("SELECT id, rule_antigens FROM antigen_rules")).fetchall()
                for row in rows:
                    rule_id = row[0]
                    rule_antigens = row[1]
                    if rule_antigens:
                        # Convert old format to new format
                        antigens = rule_antigens.split(',')
                        conditions = {
                            "antigen": antigens[0],
                            "cell_reaction": "+",
                            "paired_antigen": antigens[1] if len(antigens) > 1 else "",
                            "paired_reaction": "0"
                        }
                        conn.execute(
                            text("UPDATE antigen_rules SET rule_conditions = :conditions WHERE id = :id"),
                            {"conditions": json.dumps(conditions), "id": rule_id}
                        )
                
                conn.commit()

    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()
