#!/usr/bin/env python3
"""
Quick test script to verify data generation is working.
Run this to see if files are being created.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from tools.mock_generation import generate_mock_data

def main():
    print("="*60)
    print("Testing Mock Data Generation")
    print("="*60)
    print()
    
    company_name = "Quick Test Corp"
    company_size = "small"
    
    print(f"Generating data for: {company_name}")
    print(f"Company size: {company_size}")
    print()
    
    try:
        result = generate_mock_data(company_name, company_size)
        
        if result.get("success"):
            print("✅ SUCCESS! Data generated successfully!")
            print()
            
            # Show statistics
            stats = result.get("statistics", {})
            print("Statistics:")
            for key, value in stats.items():
                print(f"  - {key}: {value}")
            print()
            
            # Show files created
            files = result.get("files", {})
            print("Files created:")
            for file_type, file_path in files.items():
                file_exists = os.path.exists(file_path)
                status = "✅" if file_exists else "❌"
                size = os.path.getsize(file_path) if file_exists else 0
                print(f"  {status} {file_type}: {os.path.basename(file_path)} ({size:,} bytes)")
            print()
            
            # Show where files are
            if files:
                first_file = list(files.values())[0]
                data_dir = os.path.dirname(first_file)
                print(f"📁 Files location: {data_dir}")
                print()
                
                # List all JSON files in data directory
                print("All JSON files in data directory:")
                import glob
                all_json_files = glob.glob(os.path.join(data_dir, "*.json"))
                if all_json_files:
                    for json_file in sorted(all_json_files):
                        size = os.path.getsize(json_file)
                        print(f"  - {os.path.basename(json_file)} ({size:,} bytes)")
                else:
                    print("  (no JSON files found)")
            
            print()
            print("="*60)
            print("✅ Data generation is working correctly!")
            print("="*60)
            print()
            print("Next steps:")
            print("1. Check the data/ folder in your file explorer")
            print("2. Try using the UI 'Generate Data' button")
            print("3. Look for files named after your company name")
            
            return 0
        else:
            print("❌ FAILED: Data generation returned success=False")
            return 1
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

