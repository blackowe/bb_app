from sqlalchemy import create_engine, text
from models import Base
from connect_connector import connect_with_connector

def initialize_database():
    """
    Create and initialize the database schema, including tables, indexes, and denormalized structures.
    """
    engine = connect_with_connector()

    # Create tables from SQLAlchemy models
    print("Creating tables from models...")
    Base.metadata.create_all(engine)

    # Additional schema updates
    with engine.connect() as conn:
        print("Applying additional schema updates...")

        # Create the cell_reactions_summary table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cell_reactions_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            antigram_id INT NOT NULL,
            cell_number INT NOT NULL,
            reactions JSON NOT NULL,
            FOREIGN KEY (antigram_id) REFERENCES antigrams(id) ON DELETE CASCADE
        );
        """))

        # Create index if it doesn't already exist
        index_exists_query = text("""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'cell_reactions_summary'
          AND INDEX_NAME = 'idx_cell_reactions_antigram';
        """)
        index_exists = conn.execute(index_exists_query).scalar()

        if index_exists == 0:
            conn.execute(text("""
            CREATE INDEX idx_cell_reactions_antigram ON cell_reactions_summary (antigram_id);
            """))
            print("Index idx_cell_reactions_antigram created successfully.")
        else:
            print("Index idx_cell_reactions_antigram already exists.")

        # Partitioning is unsupported with foreign keys. Log and skip.
        try:
            conn.execute(text("""
            ALTER TABLE cell_reactions_summary
            PARTITION BY HASH(antigram_id) PARTITIONS 4;
            """))
            print("Partitioning applied successfully.")
        except Exception as e:
            print(f"Partitioning skipped: Foreign keys prevent partitioning. Details: {e}")

    print("Database initialized successfully.")

if __name__ == "__main__":
    initialize_database()
