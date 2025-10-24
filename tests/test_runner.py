#!/usr/bin/env python3
"""
Custom script to run tests for VEA WebApp application.

This script provides a convenient way to run different types of tests
with proper configuration and reporting.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type: str):
    """
    Run tests according to the specified type.
    
    Args:
        test_type (str): Type of tests to run (unit, functional, integration, e2e, all)
    """
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    
    # Base pytest command
    base_cmd = [
        'python', '-m', 'pytest',
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ]
    
    # Test paths based on type
    test_paths = {
        'unit': ['tests/unit/'],
        'functional': ['tests/functional/'],
        'integration': ['tests/integration/'],
        'e2e': ['tests/e2e/'],
        'all': ['tests/']
    }
    
    if test_type not in test_paths:
        print(f"Error: Invalid test type '{test_type}'")
        print("Valid types: unit, functional, integration, e2e, all")
        sys.exit(1)
    
    # Build command
    cmd = base_cmd + test_paths[test_type]
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Run tests
        result = subprocess.run(cmd, check=True)
        print("-" * 50)
        print(f"✅ {test_type} tests completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print("-" * 50)
        print(f"❌ {test_type} tests failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run VEA WebApp tests')
    parser.add_argument(
        'test_type',
        choices=['unit', 'functional', 'integration', 'e2e', 'all'],
        help='Type of tests to run'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run with coverage report'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Run with verbose output'
    )
    
    args = parser.parse_args()
    
    # Add coverage if requested
    if args.coverage:
        os.environ['COVERAGE'] = '1'
    
    # Add verbose if requested
    if args.verbose:
        os.environ['PYTEST_VERBOSE'] = '1'
    
    # Run tests
    exit_code = run_tests(args.test_type)
    sys.exit(exit_code)

if __name__ == '__main__':
    main() 