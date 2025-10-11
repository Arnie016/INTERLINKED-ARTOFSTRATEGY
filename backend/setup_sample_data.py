#!/usr/bin/env python3
"""
Setup sample organizational data in Neo4j
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def setup_sample_data():
    """Create sample organizational data"""
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create people
        people_queries = [
            "CREATE (alice:Person {name: 'Alice Johnson', role: 'Finance Manager', department: 'Finance'})",
            "CREATE (bob:Person {name: 'Bob Smith', role: 'HR Director', department: 'HR'})",
            "CREATE (carol:Person {name: 'Carol Davis', role: 'Operations Lead', department: 'Operations'})",
            "CREATE (david:Person {name: 'David Wilson', role: 'IT Manager', department: 'IT'})"
        ]
        
        # Create processes
        process_queries = [
            "CREATE (invoice:Process {name: 'Invoice Processing', description: 'Process customer invoices'})",
            "CREATE (payroll:Process {name: 'Payroll Management', description: 'Manage employee payroll'})",
            "CREATE (hiring:Process {name: 'Employee Hiring', description: 'Recruit and hire new employees'})",
            "CREATE (approval:Process {name: 'Budget Approval', description: 'Approve department budgets'})",
            "CREATE (reporting:Process {name: 'Monthly Reporting', description: 'Generate monthly reports'})"
        ]
        
        # Execute creation queries
        for query in people_queries + process_queries:
            session.run(query)
        
        # Create relationships
        relationship_queries = [
            "MATCH (alice:Person {name: 'Alice Johnson'}), (invoice:Process {name: 'Invoice Processing'}) CREATE (alice)-[:PERFORMS]->(invoice)",
            "MATCH (alice:Person {name: 'Alice Johnson'}), (approval:Process {name: 'Budget Approval'}) CREATE (alice)-[:PERFORMS]->(approval)",
            "MATCH (bob:Person {name: 'Bob Smith'}), (payroll:Process {name: 'Payroll Management'}) CREATE (bob)-[:PERFORMS]->(payroll)",
            "MATCH (bob:Person {name: 'Bob Smith'}), (hiring:Process {name: 'Employee Hiring'}) CREATE (bob)-[:PERFORMS]->(hiring)",
            "MATCH (carol:Person {name: 'Carol Davis'}), (reporting:Process {name: 'Monthly Reporting'}) CREATE (carol)-[:PERFORMS]->(reporting)",
            
            # Create dependencies
            "MATCH (invoice:Process {name: 'Invoice Processing'}), (approval:Process {name: 'Budget Approval'}) CREATE (invoice)-[:DEPENDS_ON]->(approval)",
            "MATCH (payroll:Process {name: 'Payroll Management'}), (approval:Process {name: 'Budget Approval'}) CREATE (payroll)-[:DEPENDS_ON]->(approval)",
            
            # Create reporting relationships
            "MATCH (bob:Person {name: 'Bob Smith'}), (alice:Person {name: 'Alice Johnson'}) CREATE (bob)-[:REPORTS_TO]->(alice)",
            "MATCH (carol:Person {name: 'Carol Davis'}), (alice:Person {name: 'Alice Johnson'}) CREATE (carol)-[:REPORTS_TO]->(alice)"
        ]
        
        for query in relationship_queries:
            session.run(query)
        
        print("✅ Sample data created successfully!")
        
        # Verify data
        result = session.run("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = result.single()['total_nodes']
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
        total_relationships = result.single()['total_relationships']
        
        print(f"📊 Created {total_nodes} nodes and {total_relationships} relationships")
    
    driver.close()

if __name__ == "__main__":
    setup_sample_data()