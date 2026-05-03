"""
Database migration script to add email, oauth_provider, and oauth_id fields to User model.
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add new columns to users table for authentication."""
    conn = sqlite3.connect('bobshare.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add email column if it doesn't exist
        if 'email' not in columns:
            logger.info("Adding email column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            logger.info("✅ Email column added successfully")
        else:
            logger.info("Email column already exists")
        
        # Add oauth_provider column if it doesn't exist
        if 'oauth_provider' not in columns:
            logger.info("Adding oauth_provider column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50)")
            logger.info("✅ OAuth provider column added successfully")
        else:
            logger.info("OAuth provider column already exists")
        
        # Add oauth_id column if it doesn't exist
        if 'oauth_id' not in columns:
            logger.info("Adding oauth_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(255)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_oauth_id ON users(oauth_id)")
            logger.info("✅ OAuth ID column added successfully")
        else:
            logger.info("OAuth ID column already exists")
        
        conn.commit()
        logger.info("🎉 Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

# Made with Bob
