#!/usr/bin/env python3
"""
Simple test to verify the new Airtable fetch methods have correct signatures.
This test doesn't require Airtable credentials or dependencies.
"""

import ast
import sys
import os

def test_method_signatures():
    """Test that the three new methods exist with correct signatures."""
    print("Testing Airtable fetch method signatures...")
    
    try:
        # Read the source file and parse it
        file_path = os.path.join(os.path.dirname(__file__), 'shared', 'configurable_airtable_client.py')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST
        tree = ast.parse(source_code)
        
        # Find the ConfigurableAirtableClient class
        client_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'ConfigurableAirtableClient':
                client_class = node
                break
        
        if not client_class:
            print("✗ ConfigurableAirtableClient class not found")
            return False
        
        print("✓ Found ConfigurableAirtableClient class")
        
        # Find the three required methods
        required_methods = {
            'get_leads_for_outreach': False,
            'get_leads_for_message_generation': False,
            'get_leads_for_engagement': False
        }
        
        method_signatures = {}
        
        for node in client_class.body:
            if isinstance(node, ast.FunctionDef) and node.name in required_methods:
                required_methods[node.name] = True
                
                # Check the method signature
                args = []
                for arg in node.args.args:
                    if arg.arg != 'self':  # Skip self parameter
                        args.append(arg.arg)
                
                # Check for defaults
                defaults = []
                if node.args.defaults:
                    for default in node.args.defaults:
                        if isinstance(default, ast.Constant):
                            defaults.append(default.value)
                        elif isinstance(default, ast.NameConstant):
                            defaults.append(default.value)
                        else:
                            defaults.append("default_value")
                
                method_signatures[node.name] = {
                    'args': args,
                    'defaults': defaults
                }
        
        # Check results
        all_methods_found = True
        for method_name, found in required_methods.items():
            if found:
                print(f"✓ {method_name} method found")
                
                # Check if it has the limit parameter
                sig = method_signatures.get(method_name, {})
                args = sig.get('args', [])
                
                if 'limit' in args:
                    print(f"✓ {method_name} has 'limit' parameter")
                    
                    # Check if limit has Optional[int] = None default
                    defaults = sig.get('defaults', [])
                    if defaults and defaults[-1] is None:
                        print(f"✓ {method_name} limit parameter defaults to None")
                    else:
                        print(f"⚠ {method_name} limit parameter default: {defaults}")
                else:
                    print(f"✗ {method_name} missing 'limit' parameter. Has: {args}")
                    all_methods_found = False
            else:
                print(f"✗ {method_name} method not found")
                all_methods_found = False
        
        # Check for helper methods
        helper_methods = {
            '_fetch_records': False,
            '_formula_for_outreach': False,
            '_formula_for_message_generation': False,
            '_formula_for_engagement': False
        }
        
        for node in client_class.body:
            if isinstance(node, ast.FunctionDef) and node.name in helper_methods:
                helper_methods[node.name] = True
        
        print("\n--- Helper Methods ---")
        for method_name, found in helper_methods.items():
            if found:
                print(f"✓ {method_name} helper method found")
            else:
                print(f"✗ {method_name} helper method not found")
                all_methods_found = False
        
        # Check for field mapping dictionary
        print("\n--- Field Mapping ---")
        field_mapping_found = False
        default_limit_found = False
        
        # Look for self.fields assignment in __init__
        for node in client_class.body:
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and target.attr == 'fields':
                                field_mapping_found = True
                            elif isinstance(target, ast.Attribute) and target.attr == 'default_limit':
                                default_limit_found = True
        
        if field_mapping_found:
            print("✓ self.fields dictionary found in __init__")
        else:
            print("✗ self.fields dictionary not found in __init__")
            all_methods_found = False
        
        if default_limit_found:
            print("✓ self.default_limit found in __init__")
        else:
            print("✗ self.default_limit not found in __init__")
            all_methods_found = False
        
        print("\n--- Summary ---")
        if all_methods_found:
            print("✓ All required methods and helpers are present with correct signatures")
            print("✓ Background jobs should be able to call these methods without AttributeError")
            print("✓ Methods accept limit parameters as expected")
            return True
        else:
            print("✗ Some required methods or features are missing")
            return False
            
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"✗ Error parsing file: {e}")
        return False

if __name__ == "__main__":
    success = test_method_signatures()
    if success:
        print("\n🎉 All signature tests passed! The implementation should work correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some signature tests failed. Check the output above for details.")
        sys.exit(1)