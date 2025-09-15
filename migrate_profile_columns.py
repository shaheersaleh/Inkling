#!/usr/bin/env python3

from app import create_app, db
import sqlite3
import os

def migrate_database():
    app = create_app()
    
    with app.app_context():
        # Get the database file path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Database path: {db_path}")
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if columns exist
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Existing columns: {columns}")
            
            # Add profile_image_data column if it doesn't exist
            if 'profile_image_data' not in columns:
                print("Adding profile_image_data column...")
                cursor.execute("ALTER TABLE user ADD COLUMN profile_image_data BLOB")
                print("profile_image_data column added successfully!")
            else:
                print("profile_image_data column already exists.")
            
            # Add profile_image_mimetype column if it doesn't exist
            if 'profile_image_mimetype' not in columns:
                print("Adding profile_image_mimetype column...")
                cursor.execute("ALTER TABLE user ADD COLUMN profile_image_mimetype VARCHAR(100)")
                print("profile_image_mimetype column added successfully!")
            else:
                print("profile_image_mimetype column already exists.")
            
            # Commit changes
            conn.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    migrate_database()
