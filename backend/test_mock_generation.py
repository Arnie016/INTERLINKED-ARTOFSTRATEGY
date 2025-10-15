#!/usr/bin/env python3
"""
Test script for mock data generation.

This script tests the mock data generation functionality without requiring
a Neo4j connection or running the full API server.

Usage:
    python backend/test_mock_generation.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from tools.mock_generation import generate_mock_data


def test_small_company():
    """Test generation of a small company."""
    print("\n" + "="*60)
    print("Testing Small Company Generation")
    print("="*60)
    
    result = generate_mock_data(
        company_name="Small Tech Startup",
        company_size="small"
    )
    
    assert result["success"], "Generation failed"
    stats = result["statistics"]
    
    print(f"\n✓ Small Company Generated Successfully!")
    print(f"  - Employees: {stats['total_employees']}")
    print(f"  - Departments: {stats['total_departments']}")
    print(f"  - Projects: {stats['total_projects']}")
    print(f"  - Systems: {stats['total_systems']}")
    print(f"  - Processes: {stats['total_processes']}")
    print(f"  - Relationships: {stats['total_relationships']}")
    print(f"  - Communications: {stats['total_communications']}")
    
    # Validate ranges for small company
    assert 10 <= stats['total_employees'] <= 50, f"Employee count out of range: {stats['total_employees']}"
    assert 3 <= stats['total_departments'] <= 6, f"Department count out of range: {stats['total_departments']}"
    
    return result


def test_medium_company():
    """Test generation of a medium company."""
    print("\n" + "="*60)
    print("Testing Medium Company Generation")
    print("="*60)
    
    result = generate_mock_data(
        company_name="Mid-Size Enterprise",
        company_size="medium"
    )
    
    assert result["success"], "Generation failed"
    stats = result["statistics"]
    
    print(f"\n✓ Medium Company Generated Successfully!")
    print(f"  - Employees: {stats['total_employees']}")
    print(f"  - Departments: {stats['total_departments']}")
    print(f"  - Projects: {stats['total_projects']}")
    print(f"  - Systems: {stats['total_systems']}")
    print(f"  - Processes: {stats['total_processes']}")
    print(f"  - Relationships: {stats['total_relationships']}")
    print(f"  - Communications: {stats['total_communications']}")
    
    # Validate ranges for medium company
    assert 50 <= stats['total_employees'] <= 200, f"Employee count out of range: {stats['total_employees']}"
    assert 6 <= stats['total_departments'] <= 12, f"Department count out of range: {stats['total_departments']}"
    
    return result


def test_large_company():
    """Test generation of a large company."""
    print("\n" + "="*60)
    print("Testing Large Company Generation")
    print("="*60)
    
    result = generate_mock_data(
        company_name="Large Corporation",
        company_size="large"
    )
    
    assert result["success"], "Generation failed"
    stats = result["statistics"]
    
    print(f"\n✓ Large Company Generated Successfully!")
    print(f"  - Employees: {stats['total_employees']}")
    print(f"  - Departments: {stats['total_departments']}")
    print(f"  - Projects: {stats['total_projects']}")
    print(f"  - Systems: {stats['total_systems']}")
    print(f"  - Processes: {stats['total_processes']}")
    print(f"  - Relationships: {stats['total_relationships']}")
    print(f"  - Communications: {stats['total_communications']}")
    
    # Validate ranges for large company
    assert 200 <= stats['total_employees'] <= 1000, f"Employee count out of range: {stats['total_employees']}"
    assert 12 <= stats['total_departments'] <= 25, f"Department count out of range: {stats['total_departments']}"
    
    return result


def test_data_integrity(result):
    """Test data integrity of generated data."""
    print("\n" + "="*60)
    print("Testing Data Integrity")
    print("="*60)
    
    data = result["data"]
    
    # Check that all employees have departments
    employee_depts = set(emp["department"] for emp in data["employees"])
    dept_names = set(dept["name"] for dept in data["departments"])
    
    assert employee_depts.issubset(dept_names), "Some employees have invalid departments"
    print("✓ All employees belong to valid departments")
    
    # Check that all projects have valid departments
    project_depts = set(proj["department"] for proj in data["projects"])
    assert project_depts.issubset(dept_names), "Some projects have invalid departments"
    print("✓ All projects belong to valid departments")
    
    # Check that department heads exist in employee list
    employee_names = set(emp["name"] for emp in data["employees"])
    for dept in data["departments"]:
        if dept.get("head"):
            assert dept["head"] in employee_names, f"Department head {dept['head']} not found in employees"
    print("✓ All department heads are valid employees")
    
    # Check reporting relationships
    reporting_rels = result["data"]["relationships"]["reporting"]
    for rel in reporting_rels:
        assert rel["from"] in employee_names, f"Reporting relationship from unknown employee: {rel['from']}"
        assert rel["to"] in employee_names, f"Reporting relationship to unknown employee: {rel['to']}"
    print("✓ All reporting relationships are valid")
    
    # Check department membership
    dept_membership = result["data"]["relationships"]["department_membership"]
    for rel in dept_membership:
        assert rel["from"] in employee_names, f"Department membership from unknown employee: {rel['from']}"
        assert rel["to"] in dept_names, f"Department membership to unknown department: {rel['to']}"
    print("✓ All department memberships are valid")
    
    print("\n✓ Data integrity checks passed!")


def test_file_output():
    """Test that files are created correctly."""
    print("\n" + "="*60)
    print("Testing File Output")
    print("="*60)
    
    result = generate_mock_data(
        company_name="Test Company",
        company_size="small"
    )
    
    files = result["files"]
    
    # Check that all expected files exist
    import os
    for file_type, file_path in files.items():
        assert os.path.exists(file_path), f"File not found: {file_path}"
        print(f"✓ {file_type.capitalize()} file created: {os.path.basename(file_path)}")
    
    # Check file sizes are reasonable
    for file_type, file_path in files.items():
        file_size = os.path.getsize(file_path)
        assert file_size > 100, f"File too small: {file_path} ({file_size} bytes)"
        print(f"  Size: {file_size:,} bytes")
    
    print("\n✓ File output checks passed!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MOCK DATA GENERATION TEST SUITE")
    print("="*60)
    
    try:
        # Test different company sizes
        small_result = test_small_company()
        medium_result = test_medium_company()
        large_result = test_large_company()
        
        # Test data integrity
        test_data_integrity(medium_result)
        
        # Test file output
        test_file_output()
        
        # Summary
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)
        print("\nMock data generation is working correctly.")
        print("You can now use the 'Generate Data' button in the UI.")
        print("\nGenerated files can be found in the 'data/' directory.")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

