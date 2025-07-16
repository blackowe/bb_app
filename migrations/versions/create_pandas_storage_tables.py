#!/usr/bin/env python3
"""
Migration script to create tables for storing pandas antigram and patient reaction data.
This ensures data persistence for the pandas-based system.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import sessionmaker
from connect_connector import connect_with_connector
from models import Base
from core.pandas_models import AntigramMatrixStorage, PatientReactionStorage

def create_pandas_storage_tables():
    """Create tables for storing pandas data."""
    print("=" * 60)
    print("PANDAS STORAGE TABLES MIGRATION")
    print("=" * 60)
    print("Creating tables for pandas data persistence...")
    print()
    
    # Create database connection
    print("Connecting to database...")
    engine = connect_with_connector()
    
    try:
        # Create tables
        print("Creating pandas storage tables...")
        Base.metadata.create_all(engine)
        
        # Verify tables were created
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        
        print("\n✅ Tables created successfully!")
        print("Created tables:")
        for table in tables:
            if 'storage' in table or 'template' in table:
                print(f"  - {table}")
        
        print(f"\nTotal tables: {len(tables)}")
        
        # Test table structure
        print("\nTesting table structure...")
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        try:
            # Test AntigramMatrixStorage
            test_storage = AntigramMatrixStorage(
                antigram_id=999999,  # Test ID
                matrix_data='{"test": "data"}',
                matrix_metadata='{"test": "metadata"}',
                created_at=datetime.now().date(),
                updated_at=datetime.now().date()
            )
            db_session.add(test_storage)
            db_session.commit()
            
            # Verify it was saved
            saved = db_session.query(AntigramMatrixStorage).filter_by(antigram_id=999999).first()
            if saved:
                print("✅ AntigramMatrixStorage table working correctly")
                # Clean up test data
                db_session.delete(saved)
                db_session.commit()
            else:
                print("❌ AntigramMatrixStorage table test failed")
            
            # Test PatientReactionStorage
            test_reaction = PatientReactionStorage(
                antigram_id=999999,  # Test ID
                cell_number=1,
                patient_reaction="+",
                created_at=datetime.now().date(),
                updated_at=datetime.now().date()
            )
            db_session.add(test_reaction)
            db_session.commit()
            
            # Verify it was saved
            saved_reaction = db_session.query(PatientReactionStorage).filter_by(
                antigram_id=999999, cell_number=1
            ).first()
            if saved_reaction:
                print("✅ PatientReactionStorage table working correctly")
                # Clean up test data
                db_session.delete(saved_reaction)
                db_session.commit()
            else:
                print("❌ PatientReactionStorage table test failed")
                
        except Exception as e:
            print(f"❌ Table test failed: {e}")
            db_session.rollback()
        finally:
            db_session.close()
        
        print("\n🎉 Migration completed successfully!")
        print("Your pandas data will now persist across server restarts.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_pandas_storage_tables()
    if success:
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Create some antigrams and templates")
        print("3. Restart the server to verify data persistence")
    else:
        print("\nMigration failed. Please check the error messages above.")
        sys.exit(1) 