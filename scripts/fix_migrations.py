#!/usr/bin/env python
"""
Script to fix migration inconsistencies in WhatsApp Bot app.
"""

import os
import sys
import django
from django.db import connection

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def fix_whatsapp_migrations():
    """Fix WhatsApp Bot migration inconsistencies."""
    print("🔧 Fixing WhatsApp Bot migrations...")
    
    try:
        with connection.cursor() as cursor:
            # Check current migration state
            cursor.execute("""
                SELECT app, name FROM django_migrations 
                WHERE app = 'whatsapp_bot' 
                ORDER BY name
            """)
            current_migrations = cursor.fetchall()
            
            print(f"Current migrations: {current_migrations}")
            
            # Check if we have the correct migrations
            migration_names = [m[1] for m in current_migrations]
            
            if '0002_event_grid_tables' in migration_names and '0003_delete_whatsappdeliveryreport_and_more' in migration_names:
                print("✅ All required migrations are present")
                
                # Check if we need to add the missing migration record
                if '0002_event_grid_tables_fixed' not in migration_names:
                    print("❌ Migration 0002_event_grid_tables_fixed is missing")
                    
                    # Insert the missing migration record
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('whatsapp_bot', '0002_event_grid_tables_fixed', datetime('now'))
                    """)
                    
                    print("✅ Added missing migration record for 0002_event_grid_tables_fixed")
                else:
                    print("✅ Migration 0002_event_grid_tables_fixed is present")
                
            else:
                print("✅ Migration state looks correct")
                
        print("🎉 Migration fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing migrations: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Starting migration fix...")
    
    success = fix_whatsapp_migrations()
    
    if success:
        print("✅ All migrations fixed successfully!")
    else:
        print("❌ Migration fix failed!")

if __name__ == "__main__":
    main() 