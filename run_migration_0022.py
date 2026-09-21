"""Run migration 0022 - Content Performance Insights"""

import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "apps" / "sme" / "sme-api"
sys.path.insert(0, str(app_dir))

from app.db import get_service_client

def run_migration():
    """Run migration 0022"""
    print("Running migration 0022: Create content_performance_insights table...")

    # Read the migration file
    migration_file = Path(__file__).parent / "supabase" / "migrations" / "0022_create_content_performance_insights.sql"

    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # Get the Supabase client
    client = get_service_client()

    try:
        # Execute the SQL using Supabase's rpc or direct SQL execution
        # Since Supabase doesn't have a direct SQL execution method, we'll use psycopg2
        import os
        import psycopg2

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("ERROR: DATABASE_URL not found in environment")
            return

        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Execute the migration
        cursor.execute(sql)

        print("[OK] Migration 0022 completed successfully!")
        print("     Table 'content_performance_insights' created with:")
        print("     - Performance tracking fields")
        print("     - AI analysis and recommendations")
        print("     - Comparative insights (vs user average, vs platform)")
        print("     - Full indexing and RLS policies")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
