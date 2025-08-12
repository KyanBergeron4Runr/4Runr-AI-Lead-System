#!/usr/bin/env python3
"""
Complete system test

Tests the entire 4Runr Multi-Step Email Campaign System end-to-end.
"""

import sys
import os
import importlib.util

# Direct imports
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_system_tests():
    """Run all system tests"""
    print("🚀 4Runr Multi-Step Email Campaign System - Complete Test Suite")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Campaign Foundation
    print("\n1️⃣  Testing Campaign Foundation...")
    try:
        result = os.system("python test_campaign_foundation.py")
        test_results['foundation'] = result == 0
        print(f"   Foundation Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['foundation'] = False
        print(f"   Foundation Test: ❌ Failed ({e})")
    
    # Test 2: Campaign Generation
    print("\n2️⃣  Testing Campaign Generation...")
    try:
        result = os.system("python test_simple_campaign_generation.py")
        test_results['generation'] = result == 0
        print(f"   Generation Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['generation'] = False
        print(f"   Generation Test: ❌ Failed ({e})")
    
    # Test 3: Quality Control
    print("\n3️⃣  Testing Quality Control...")
    try:
        result = os.system("python test_standalone_quality.py")
        test_results['quality'] = result == 0
        print(f"   Quality Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['quality'] = False
        print(f"   Quality Test: ❌ Failed ({e})")
    
    # Test 4: Delivery System
    print("\n4️⃣  Testing Delivery System...")
    try:
        result = os.system("python test_delivery_system.py")
        test_results['delivery'] = result == 0
        print(f"   Delivery Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['delivery'] = False
        print(f"   Delivery Test: ❌ Failed ({e})")
    
    # Test 5: Engager System
    print("\n5️⃣  Testing Engager System...")
    try:
        result = os.system("python test_engager_simple.py")
        test_results['engager'] = result == 0
        print(f"   Engager Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['engager'] = False
        print(f"   Engager Test: ❌ Failed ({e})")
    
    # Test 6: Delivery Pipeline
    print("\n6️⃣  Testing Delivery Pipeline...")
    try:
        result = os.system("python test_delivery_pipeline.py")
        test_results['pipeline'] = result == 0
        print(f"   Pipeline Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['pipeline'] = False
        print(f"   Pipeline Test: ❌ Failed ({e})")
    
    # Test 7: Cold Lead Recycling
    print("\n7️⃣  Testing Cold Lead Recycling...")
    try:
        result = os.system("python test_cold_recycling.py")
        test_results['recycling'] = result == 0
        print(f"   Recycling Test: {'✅ Passed' if result == 0 else '❌ Failed'}")
    except Exception as e:
        test_results['recycling'] = False
        print(f"   Recycling Test: ❌ Failed ({e})")
    
    return test_results


def main():
    """Main test runner"""
    print("🧪 Running Complete System Test Suite\n")
    
    try:
        # Run all tests
        results = run_system_tests()
        
        # Calculate results
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        # Summary
        print("\n" + "=" * 80)
        print("🎉 COMPLETE SYSTEM TEST RESULTS")
        print("=" * 80)
        
        print(f"\n📊 Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for test_name, passed in results.items():
            status = "✅ Passed" if passed else "❌ Failed"
            print(f"  {test_name.title()}: {status}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL!")
            
            print(f"\n🚀 System Components Verified:")
            print(f"  📧 Campaign generation with AI and fallback")
            print(f"  🔒 Quality control and validation")
            print(f"  📥 Campaign injection and scheduling")
            print(f"  📬 Message queue management")
            print(f"  🚀 Delivery processing and tracking")
            print(f"  📊 Analytics and performance monitoring")
            print(f"  🔄 Cold lead recycling and re-engagement")
            
            print(f"\n🎯 Ready for Production Use:")
            print(f"  • Generate high-quality multi-step campaigns")
            print(f"  • Automated scheduling (Day 0, 3, 7)")
            print(f"  • Quality-controlled message delivery")
            print(f"  • Response-based campaign progression")
            print(f"  • Cold lead recycling with strategic re-engagement")
            print(f"  • Comprehensive analytics and tracking")
            
            print(f"\n🔧 Next Steps:")
            print(f"  1. Configure Microsoft Graph API for production email delivery")
            print(f"  2. Set up Airtable integration for lead management")
            print(f"  3. Configure OpenAI API for enhanced message generation")
            print(f"  4. Set up monitoring and alerting for production use")
            print(f"  5. Schedule regular cold lead recycling runs")
            
        else:
            print(f"\n⚠️  Some tests failed - System needs attention")
            print(f"Review the failed tests above and check the detailed logs")
        
        return passed_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)