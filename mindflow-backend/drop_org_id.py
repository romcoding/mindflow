#!/usr/bin/env python3
"""
SQL migration to drop org_id column from user table
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

def drop_org_id_column():
    """Drop the org_id column from the user table"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL environment variable found")
        return False
    
    # Parse the database URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Connect to the database
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if org_id column exists
        print("🔍 Checking if org_id column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'org_id'
        """)
        
        if cursor.fetchone():
            print("📋 org_id column found, dropping it...")
            
            # Drop the org_id column
            cursor.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS org_id')
            conn.commit()
            
            print("✅ org_id column dropped successfully!")
        else:
            print("ℹ️  org_id column does not exist, nothing to drop")
        
        # Verify the column was dropped
        print("🔍 Verifying column removal...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Current user table columns: {columns}")
        
        if 'org_id' not in columns:
            print("✅ Verification successful: org_id column removed")
            success = True
        else:
            print("❌ Verification failed: org_id column still exists")
            success = False
        
        cursor.close()
        conn.close()
        
        return success
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = drop_org_id_column()
    sys.exit(0 if success else 1)
