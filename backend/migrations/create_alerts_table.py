"""
Database migration: Add alerts table
Run this script to create the alerts table in PostgreSQL
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.postgres import engine, Base
from backend.models.alert import Alert
from backend.models.user import User, UserPreferences

def run_migration():
    """Create alerts table in database"""
    print("Running alerts table migration...")
    
    try:
        # This will create the alerts table if it doesn't exist
        Base.metadata.create_all(bind=engine, tables=[Alert.__table__])
        print("✅ Alerts table created successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
