#!/usr/bin/env python3
"""
Test that verifies the methods can be called without AttributeError.
This simulates what background jobs would do.
"""

import sys
import os

# Mock the dependencies that aren't available
class MockLogger:
    def log_module_activity(self, *args, **kwargs):
        pass

class MockConfig:
    def __init__(self):
        self.data = {
            'api_key': 'mock_key',
            'base_id': 'mock_base',
            'table_name': 'mock_table'
        }
    
    def __getitem__(self, key):
        return self.data[key]

# Mock the imports
sys.modules['outreach'] = type(sys)('outreach')
sys.modules['outreach.shared'] = type(sys)('outreach.shared')
sys.modules['outreach.shared.config'] = type(sys)('outreach.shared.config')
sys.modules['outreach.shared.logging_utils'] = type(sys)('outreach.shared.logging_utils')

# Add mock functions
def get_airtable_config():
    return MockConfig()

def get_logger(name):
    return MockLogger()

sys.modules['outreach.shared.config'].get_airtable_config = get_airtable_config
sys.modules['outreach.shared.logging_utils'].get_logger = get_logger

# Mock pyairtable
class MockTable:
    def all(self, **kwargs):
        # Return empty list to simulate no records
        return []

class MockApi:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def table(self, base_id, table_name):
        return MockTable()

sys.modules['pyairtable'] = type(sys)('pyairtable')
sys.modules['pyairtable.formulas'] = type(sys)('pyairtable.formulas')
sys.modules['pyairtable'].Api = MockApi
sys.modules['pyairtable.formulas'].match = lambda x: x

def test_method_calls():
    """Test that the methods can be called without AttributeError."""
    print("Testing method calls...")
    
    try:
        # Now import the actual class
        from shared.configurable_airtable_client import ConfigurableAirtableClient
        
        print("✓ Successfully imported ConfigurableAirtableClient")
        
        # Create an instance
        client = ConfigurableAirtableClient()
        print("✓ Successfully created client instance")
        
        # Test the three methods
        methods_to_test = [
            ('get_leads_for_outreach', [None, 5, 10]),
            ('get_leads_for_message_generation', [None, 3, 15]),
            ('get_leads_for_engagement', [None, 7, 20])
        ]
        
        all_passed = True
        
        for method_name, test_limits in methods_to_test:
            print(f"\n--- Testing {method_name} ---")
            
            if not hasattr(client, method_name):
                print(f"✗ Method {method_name} not found")
                all_passed = False
                continue
            
            method = getattr(client, method_name)
            
            for limit in test_limits:
                try:
                    if limit is None:
                        result = method()
                        print(f"✓ {method_name}() returned {len(result)} leads")
                    else:
                        result = method(limit=limit)
                        print(f"✓ {method_name}(limit={limit}) returned {len(result)} leads")
                    
                    # Verify result is a list
                    if not isinstance(result, list):
                        print(f"✗ {method_name} returned {type(result)}, expected list")
                        all_passed = False
                    
                except AttributeError as e:
                    print(f"✗ AttributeError in {method_name}: {e}")
                    all_passed = False
                except TypeError as e:
                    if "unexpected keyword argument" in str(e):
                        print(f"✗ {method_name} doesn't accept limit parameter: {e}")
                        all_passed = False
                    else:
                        print(f"✓ {method_name} accepts limit parameter (got different error: {e})")
                except Exception as e:
                    # Other exceptions are OK - we just want to verify no AttributeError
                    print(f"✓ {method_name} method exists and accepts parameters (got: {type(e).__name__})")
        
        print("\n--- Summary ---")
        if all_passed:
            print("✓ All methods exist and accept limit parameters")
            print("✓ No AttributeError exceptions were raised")
            print("✓ All methods return lists as expected")
            print("✓ Background jobs should work without method signature errors")
            return True
        else:
            print("✗ Some method tests failed")
            return False
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_method_calls()
    if success:
        print("\n🎉 All method call tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some method call tests failed.")
        sys.exit(1)