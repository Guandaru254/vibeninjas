#!/usr/bin/env python
"""
Database Migration Script for Supabase
Run this script to migrate from SQLite to Supabase PostgreSQL
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.management.commands.dumpdata import Command as DumpDataCommand
from django.core.management.commands.loaddata import Command as LoadDataCommand
from io import StringIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DopeEvents.settings')
django.setup()

def migrate_to_supabase():
    """Migrate data from SQLite to Supabase"""
    
    print("🚀 Starting migration to Supabase...")
    
    # Step 1: Dump data from SQLite
    print("📦 Dumping data from SQLite...")
    output = StringIO()
    dump_command = DumpDataCommand()
    dump_command.stdout = output
    dump_command.handle(exclude=['contenttypes', 'auth.Permission'], indent=2)
    
    # Save dump to file
    with open('data_dump.json', 'w') as f:
        f.write(output.getvalue())
    
    print("✅ Data dumped to data_dump.json")
    
    # Step 2: Switch to Supabase (set DEBUG=False in settings)
    print("🔄 Switching to Supabase database...")
    os.environ['DEBUG'] = 'False'
    
    # Step 3: Run migrations on Supabase
    print("🏗️  Running migrations on Supabase...")
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    # Step 4: Load data into Supabase
    print("📥 Loading data into Supabase...")
    execute_from_command_line(['manage.py', 'loaddata', 'data_dump.json'])
    
    # Step 5: Create superuser for Supabase
    print("👤 Creating superuser for Supabase...")
    print("Please create a superuser manually:")
    print("python manage.py createsuperuser")
    
    print("✅ Migration completed successfully!")
    print("🧹 Clean up: Remove data_dump.json file")

def create_supabase_migrations():
    """Create migration files for Supabase-specific optimizations"""
    
    print("🔧 Creating Supabase-optimized migrations...")
    
    # Create custom migration for Cloudinary fields
    migration_content = '''
# Generated migration for Cloudinary integration
from django.db import migrations, models
import cloudinary.models

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=cloudinary.models.CloudinaryField('profile_pics', blank=True, null=True),
        ),
    ]
'''
    
    # Write migration file
    with open('events/migrations/0002_cloudinary_profile_pics.py', 'w') as f:
        f.write(migration_content)
    
    print("✅ Cloudinary migration created")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'create-migrations':
        create_supabase_migrations()
    else:
        migrate_to_supabase()
