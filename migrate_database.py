#!/usr/bin/env python3
"""
Database migration script to add resolution tracking columns.
Run this once to update existing database.
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import DATABASE_PATH


def migrate_database():
    """Add resolution tracking columns to changes table."""
    print("🔄 Migrating database...")
    print(f"Database: {DATABASE_PATH}")

    if not DATABASE_PATH.exists():
        print("❌ Database not found!")
        print(f"   Expected location: {DATABASE_PATH}")
        return False

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(changes)")
        columns = [col[1] for col in cursor.fetchall()]

        columns_to_add = []

        if 'is_resolved' not in columns:
            columns_to_add.append(('is_resolved', 'INTEGER DEFAULT 0'))

        if 'resolved_by' not in columns:
            columns_to_add.append(('resolved_by', 'TEXT'))

        if 'resolved_at' not in columns:
            columns_to_add.append(('resolved_at', 'DATETIME'))

        if 'resolution_notes' not in columns:
            columns_to_add.append(('resolution_notes', 'TEXT'))

        if not columns_to_add:
            print("✅ Database already up to date!")
            return True

        print(f"\n📝 Adding {len(columns_to_add)} new columns:")

        for col_name, col_type in columns_to_add:
            print(f"   - {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE changes ADD COLUMN {col_name} {col_type}")

        conn.commit()
        conn.close()

        print("\n✅ Database migration completed successfully!")
        print("\n📊 New features available:")
        print("   - Mark changes as resolved")
        print("   - Track resolution notes")
        print("   - Complete audit trail")
        print("\n🚀 You're ready to use the new resolution workflow!")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  SDS Auto-Updater - Database Migration")
    print("=" * 60)
    print()

    success = migrate_database()

    if success:
        print("\n✅ Migration successful!")
        print("\n🎯 Next steps:")
        print("   1. Restart the Streamlit dashboard")
        print("   2. Go to Changes page")
        print("   3. Try marking a change as resolved")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure database file exists")
        print("   2. Check file permissions")
        print("   3. Ensure no other process is using the database")
        sys.exit(1)
