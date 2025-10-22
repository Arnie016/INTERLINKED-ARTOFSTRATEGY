#!/usr/bin/env python3
"""
Neo4j Configuration Example

This example shows how to use the Neo4j configuration for basic operations.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.neo4j_driver import get_neo4j_driver, execute_query, execute_write_query


def create_sample_data():
    """Create some sample data for demonstration."""
    # Clear existing data (optional - be careful in production!)
    print("Clearing existing data...")
    execute_write_query("MATCH (n) DETACH DELETE n")
    
    # Create sample nodes
    print("Creating sample data...")
    execute_write_query("""
        CREATE (alice:Person {name: 'Alice', age: 30, role: 'Engineer'})
        CREATE (bob:Person {name: 'Bob', age: 25, role: 'Designer'})
        CREATE (charlie:Person {name: 'Charlie', age: 35, role: 'Manager'})
        CREATE (engineering:Department {name: 'Engineering', budget: 1000000})
        CREATE (design:Department {name: 'Design', budget: 500000})
    """)
    
    # Create relationships
    execute_write_query("""
        MATCH (alice:Person {name: 'Alice'}), (engineering:Department {name: 'Engineering'})
        CREATE (alice)-[:WORKS_IN]->(engineering)
        
        MATCH (bob:Person {name: 'Bob'}), (design:Department {name: 'Design'})
        CREATE (bob)-[:WORKS_IN]->(design)
        
        MATCH (charlie:Person {name: 'Charlie'}), (engineering:Department {name: 'Engineering'})
        CREATE (charlie)-[:MANAGES]->(engineering)
        
        MATCH (alice:Person {name: 'Alice'}), (charlie:Person {name: 'Charlie'})
        CREATE (alice)-[:REPORTS_TO]->(charlie)
    """)
    
    print("✅ Sample data created!")


def query_sample_data():
    """Query the sample data."""
    print("\n🔍 Querying sample data:")
    
    # Get all people
    print("\n1. All people:")
    results = execute_query("MATCH (p:Person) RETURN p.name as name, p.age as age, p.role as role")
    for record in results:
        print(f"   {record['name']} (age: {record['age']}, role: {record['role']})")
    
    # Get people by department
    print("\n2. People by department:")
    results = execute_query("""
        MATCH (p:Person)-[:WORKS_IN]->(d:Department)
        RETURN d.name as department, collect(p.name) as people
    """)
    for record in results:
        people = ", ".join(record['people'])
        print(f"   {record['department']}: {people}")
    
    # Get management structure
    print("\n3. Management structure:")
    results = execute_query("""
        MATCH (manager:Person)-[:MANAGES]->(d:Department)<-[:WORKS_IN]-(employee:Person)
        RETURN manager.name as manager, d.name as department, collect(employee.name) as employees
    """)
    for record in results:
        employees = ", ".join(record['employees'])
        print(f"   {record['manager']} manages {record['department']}: {employees}")


def main():
    """Main example function."""
    print("🗄️  Neo4j Driver Example")
    print("=" * 40)
    
    try:
        # Get driver instance
        driver = get_neo4j_driver()
        
        # Test connection first
        if not driver.test_connection():
            print("❌ Cannot connect to Neo4j. Please check your .env configuration.")
            return
        
        print("✅ Connected to Neo4j successfully!")
        
        # Create sample data
        create_sample_data()
        
        # Query the data
        query_sample_data()
        
        # Show final database info
        print("\n📊 Final database state:")
        info = driver.get_database_info()
        print(f"   Nodes: {info.get('node_count', 0)}")
        print(f"   Relationships: {info.get('relationship_count', 0)}")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Valid .env file with Neo4j credentials")
        print("2. Neo4j Aura instance running")
        print("3. Proper permissions to create/delete data")


if __name__ == "__main__":
    main()
