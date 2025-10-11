#!/usr/bin/env python3
"""
Test runner for the Agent Tool Architecture tests.
"""

import os
import sys
import subprocess

# Add the parent directory (backend) to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_file):
    """Run a specific test file."""
    print(f"\n🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🚀 Agent Tool Architecture Test Suite")
    print("=" * 50)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of test files to run
    test_files = [
        "test_architecture.py",
        "test_neo4j_connection.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        # Check if test file exists in the same directory as this script
        test_path = os.path.join(script_dir, test_file)
        if os.path.exists(test_path):
            results[test_file] = run_test(test_path)
        else:
            print(f"⚠️  Test file {test_file} not found in {script_dir}, skipping...")
            results[test_file] = False
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_file, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_file}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
