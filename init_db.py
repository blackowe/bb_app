from sqlalchemy import create_engine, text, inspect
from models import Base, PatientReactionProfile
from connect_connector import connect_with_connector
import json

def initialize_database():
    """
    Create and initialize the database schema, including tables, indexes, and denormalized structures.
    """
    engine = connect_with_connector()

    # Create tables from SQLAlchemy models
    print("Creating tables from models...")
    Base.metadata.create_all(engine)

    # Debug: Print table info
    inspector = inspect(engine)
    print("\nVerifying table schemas:")
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  Column: {column['name']} ({column['type']})")

    # Additional schema updates
    with engine.connect() as conn:
        print("\nApplying additional schema updates...")

        # Drop and recreate patient_reaction_profiles table to ensure correct schema
        if "sqlite" in str(engine.url):
            try:
                # Drop the table if it exists
                conn.execute(text("DROP TABLE IF EXISTS patient_reaction_profiles"))
                print("Dropped existing patient_reaction_profiles table")

                # Create the table with the correct schema
                conn.execute(text("""
                CREATE TABLE patient_reaction_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cell_id INTEGER NOT NULL,
                    patient_rxn VARCHAR(10) NOT NULL,
                    is_ruled_out BOOLEAN DEFAULT 0,
                    antigen VARCHAR(50),
                    FOREIGN KEY (cell_id) REFERENCES cells(id),
                    UNIQUE (cell_id)
                )
                """))
                print("Created patient_reaction_profiles table with correct schema")

                # Debug: Verify the table was created correctly
                result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='patient_reaction_profiles'"))
                table_sql = result.fetchone()[0]
                print(f"\nVerified table creation SQL:\n{table_sql}")

            except Exception as e:
                print(f"Error handling patient_reaction_profiles table: {e}")

        # Add new columns to antigen_rules table if they don't exist (SQLite)
        if "sqlite" in str(engine.url):
            try:
                # Check if rule_conditions column exists
                conn.execute(text("SELECT rule_conditions FROM antigen_rules LIMIT 1"))
            except Exception:
                print("Adding rule_conditions column to antigen_rules table...")
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

            try:
                # Check if rule_type column exists
                conn.execute(text("SELECT rule_type FROM antigen_rules LIMIT 1"))
            except Exception:
                print("Adding rule_type column to antigen_rules table...")
                conn.execute(text("""
                ALTER TABLE antigen_rules
                ADD COLUMN rule_type VARCHAR(50) NOT NULL DEFAULT 'homozygous'
                """))

            try:
                # Check if dependencies column exists
                conn.execute(text("SELECT dependencies FROM antigen_rules LIMIT 1"))
            except Exception:
                print("Adding dependencies column to antigen_rules table...")
                conn.execute(text("""
                ALTER TABLE antigen_rules
                ADD COLUMN dependencies TEXT
                """))

            # Update existing rules to use the new rule_type field
            conn.execute(text("""
            UPDATE antigen_rules
            SET rule_type = 'homozygous'
            WHERE rule_type IS NULL
            """))

            # Drop the old rule_antigens column if it exists
            try:
                conn.execute(text("""
                ALTER TABLE antigen_rules DROP COLUMN rule_antigens
                """))
                print("Dropped old rule_antigens column")
            except Exception:
                print("rule_antigens column already removed")

        # Create cell_reactions_summary table (Only for MySQL, not SQLite)
        if "sqlite" not in str(engine.url):
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cell_reactions_summary (
                id INT AUTO_INCREMENT PRIMARY KEY,
                antigram_id INT NOT NULL,
                cell_number INT NOT NULL,
                reactions JSON NOT NULL,
                FOREIGN KEY (antigram_id) REFERENCES antigrams(id) ON DELETE CASCADE
            );
            """))

            # Check if the index already exists (Only for MySQL)
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

            # MySQL Partitioning (Unsupported in SQLite)
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
