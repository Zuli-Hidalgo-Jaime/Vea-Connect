#!/usr/bin/env python3
"""
Script to verify that all Azure Functions v4 are properly configured.
Checks function.json files and validates required files exist.
"""

import sys
import os
import json
import glob
from pathlib import Path

def check_functions():
    """
    Verify that all functions are properly configured.
    
    Returns:
        bool: True if all functions are valid, False otherwise
    """
    functions_dir = Path(__file__).parent
    function_dirs = []
    
    # Find all function directories (those containing function.json)
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    if not function_dirs:
        print("No function directories found")
        return False
    
    print(f"Found {len(function_dirs)} function directories")
    print("=" * 50)
    
    all_valid = True
    
    for function_dir in sorted(function_dirs):
        function_name = function_dir.name
        function_json_path = function_dir / "function.json"
        init_py_path = function_dir / "__init__.py"
        
        print(f"\nChecking function: {function_name}")
        print("-" * 30)
        
        # Check if function.json exists
        if not function_json_path.exists():
            print(f"  ERROR: function.json not found in {function_name}")
            all_valid = False
            continue
        
        # Check if __init__.py exists
        if not init_py_path.exists():
            print(f"  ERROR: __init__.py not found in {function_name}")
            all_valid = False
            continue
        
        # Parse function.json and extract binding type
        try:
            with open(function_json_path, 'r', encoding='utf-8') as f:
                function_config = json.load(f)
            
            bindings = function_config.get('bindings', [])
            if not bindings:
                print(f"  ERROR: No bindings found in {function_name}/function.json")
                all_valid = False
                continue
            
            # Get the main binding (first one)
            main_binding = bindings[0]
            binding_type = main_binding.get('type', 'unknown')
            
            print(f"  ✅ function.json: OK")
            print(f"  ✅ __init__.py: OK")
            print(f"  📋 Binding type: {binding_type}")
            
            # Additional binding info
            if binding_type == 'httpTrigger':
                methods = main_binding.get('methods', [])
                route = main_binding.get('route', '')
                print(f"     Methods: {methods}")
                print(f"     Route: {route}")
            elif binding_type == 'eventGridTrigger':
                print(f"     Event Grid trigger configured")
            elif binding_type == 'queueTrigger':
                queue_name = main_binding.get('queueName', '')
                print(f"     Queue: {queue_name}")
            
        except json.JSONDecodeError as e:
            print(f"  ERROR: Invalid JSON in {function_name}/function.json: {e}")
            all_valid = False
        except Exception as e:
            print(f"  ERROR: Failed to parse {function_name}/function.json: {e}")
            all_valid = False
    
    print("\n" + "=" * 50)
    if all_valid:
        print("✅ All functions are properly configured")
    else:
        print("❌ Some functions have configuration issues")
    
    return all_valid

if __name__ == "__main__":
    print("Verifying Azure Functions configuration...")
    success = check_functions()
    
    if not success:
        print("\nExiting with error code 1")
        sys.exit(1)
    else:
        print("\nAll functions verified successfully")
