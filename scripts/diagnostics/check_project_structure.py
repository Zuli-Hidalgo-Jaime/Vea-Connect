#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la estructura del proyecto Django
y identificar problemas con el módulo config.
"""

import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists and display the result."""
    if os.path.exists(filepath):
        print(f"[OK] {description}: {filepath}")
        return True
    else:
        print(f"[ERROR] {description}: {filepath} - NOT FOUND")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and display the result."""
    if os.path.isdir(dirpath):
        print(f"[OK] {description}: {dirpath}")
        return True
    else:
        print(f"[ERROR] {description}: {dirpath} - NOT FOUND")
        return False

def check_module_importable(module_name, description):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"[OK] {description}: {module_name} - IMPORTABLE")
        return True
    except ImportError as e:
        print(f"[ERROR] {description}: {module_name} - IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"[WARNING] {description}: {module_name} - UNEXPECTED ERROR: {e}")
        return False

def main():
    print("=== DJANGO PROJECT STRUCTURE DIAGNOSTIC ===\n")
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    print()
    
    # Check essential files
    print("=== ESSENTIAL FILES VERIFICATION ===")
    essential_files = [
        ("manage.py", "manage.py file"),
        ("requirements.txt", "requirements.txt file"),
        ("config/__init__.py", "__init__.py file in config"),
        ("config/wsgi.py", "wsgi.py file"),
        ("config/settings/__init__.py", "__init__.py file in config/settings"),
        ("config/settings/production.py", "production settings file"),
    ]
    
    all_files_exist = True
    for filepath, description in essential_files:
        if not check_file_exists(filepath, description):
            all_files_exist = False
    
    print()
    
    # Check essential directories
    print("=== DIRECTORY VERIFICATION ===")
    essential_dirs = [
        ("config", "config directory"),
        ("config/settings", "config/settings directory"),
        ("apps", "apps directory"),
    ]
    
    all_dirs_exist = True
    for dirpath, description in essential_dirs:
        if not check_directory_exists(dirpath, description):
            all_dirs_exist = False
    
    print()
    
    # Check module imports
    print("=== MODULE IMPORT VERIFICATION ===")
    
    # Add current directory to path if not present
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to PYTHONPATH")
    
    # Check critical modules
    modules_to_check = [
        ("config", "config module"),
        ("config.wsgi", "config.wsgi module"),
        ("config.settings", "config.settings module"),
        ("config.settings.production", "config.settings.production module"),
        ("django", "Django"),
        ("gunicorn", "Gunicorn"),
    ]
    
    all_modules_importable = True
    for module_name, description in modules_to_check:
        if not check_module_importable(module_name, description):
            all_modules_importable = False
    
    print()
    
    # Check Django configuration
    print("=== DJANGO CONFIGURATION VERIFICATION ===")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
        import django
        django.setup()
        print("[OK] Django configured correctly")
        
        # Check that apps are registered
        from django.conf import settings
        print(f"[OK] Installed apps: {len(settings.INSTALLED_APPS)} apps")
        print(f"[OK] Database configured: {settings.DATABASES['default']['ENGINE']}")
        
    except Exception as e:
        print(f"[ERROR] Error configuring Django: {e}")
        all_modules_importable = False
    
    print()
    
    # Summary
    print("=== SUMMARY ===")
    if all_files_exist and all_dirs_exist and all_modules_importable:
        print("[OK] ALL CHECKS PASSED - Project is correctly configured")
        print("\nThe gunicorn command should work:")
        print("   gunicorn config.wsgi:application --bind=0.0.0.0:8000")
    else:
        print("[ERROR] PROBLEMS DETECTED - Check errors above")
        
        if not all_files_exist:
            print("   - Missing essential files")
        if not all_dirs_exist:
            print("   - Missing essential directories")
        if not all_modules_importable:
            print("   - Problems with module imports")
    
    print()
    print("=== SUGGESTIONS ===")
    print("1. If there are problems with the 'config' module, verify that:")
    print("   - The 'config' directory exists in the project root")
    print("   - The 'config/__init__.py' file exists (even if empty)")
    print("   - PYTHONPATH includes the project root directory")
    print()
    print("2. To run manually:")
    print("   python manage.py runserver")
    print("   gunicorn config.wsgi:application --bind=0.0.0.0:8000")

if __name__ == "__main__":
    main() 