"""
Graph Analysis Tools - Pattern detection, bottleneck analysis, and metrics.

This module provides analytical tools for understanding organizational patterns,
identifying inefficiencies, and generating insights from the graph data.
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import json


def find_bottlenecks(driver: GraphDatabase, process_type: str = "Process") -> Dict[str, Any]:
    """
    Find processes that are bottlenecks (unassigned or overloaded).
    
    Args:
        driver: Neo4j driver instance
        process_type: Type of process nodes to analyze
    
    Returns:
        Dict containing bottleneck analysis results
    """
    try:
        with driver.session() as session:
            # Find unassigned processes
            unassigned_query = f"""
            MATCH (p:{process_type})
            WHERE NOT (p)<-[:PERFORMS]-(:Person)
            RETURN p.name as process_name, p.description as description, 
                   'unassigned' as bottleneck_type
            """
            
            # Find overloaded processes (more than 3 people assigned)
            overloaded_query = f"""
            MATCH (p:{process_type})<-[:PERFORMS]-(person:Person)
            WITH p, collect(person.name) as assigned_people, count(person) as person_count
            WHERE person_count > 3
            RETURN p.name as process_name, p.description as description,
                   person_count, assigned_people, 'overloaded' as bottleneck_type
            """
            
            unassigned_result = session.run(unassigned_query)
            overloaded_result = session.run(overloaded_query)
            
            bottlenecks = []
            
            # Process unassigned processes
            for record in unassigned_result:
                bottlenecks.append({
                    "process_name": record["process_name"],
                    "description": record["description"],
                    "bottleneck_type": record["bottleneck_type"],
                    "assigned_people": [],
                    "person_count": 0
                })
            
            # Process overloaded processes
            for record in overloaded_result:
                bottlenecks.append({
                    "process_name": record["process_name"],
                    "description": record["description"],
                    "bottleneck_type": record["bottleneck_type"],
                    "assigned_people": record["assigned_people"],
                    "person_count": record["person_count"]
                })
            
            return {
                "success": True,
                "bottlenecks": bottlenecks,
                "total_bottlenecks": len(bottlenecks),
                "unassigned_count": len([b for b in bottlenecks if b["bottleneck_type"] == "unassigned"]),
                "overloaded_count": len([b for b in bottlenecks if b["bottleneck_type"] == "overloaded"])
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding bottlenecks: {str(e)}"}


def analyze_organizational_structure(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Analyze the organizational hierarchy and reporting structure.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing organizational structure analysis
    """
    try:
        with driver.session() as session:
            # Find reporting relationships
            reporting_query = """
            MATCH (manager:Person)-[:REPORTS_TO]->(subordinate:Person)
            RETURN manager.name as manager, subordinate.name as subordinate
            """
            
            # Find people without managers (top level)
            top_level_query = """
            MATCH (p:Person)
            WHERE NOT (p)-[:REPORTS_TO]->(:Person)
            RETURN p.name as name, p.role as role, p.department as department
            """
            
            # Find people without subordinates (individual contributors)
            individual_contributors_query = """
            MATCH (p:Person)
            WHERE NOT (:Person)-[:REPORTS_TO]->(p)
            RETURN p.name as name, p.role as role, p.department as department
            """
            
            reporting_result = session.run(reporting_query)
            top_level_result = session.run(top_level_query)
            individual_contributors_result = session.run(individual_contributors_query)
            
            # Process results
            reporting_relationships = [dict(record) for record in reporting_result]
            top_level_people = [dict(record) for record in top_level_result]
            individual_contributors = [dict(record) for record in individual_contributors_result]
            
            # Calculate span of control
            manager_span = {}
            for rel in reporting_relationships:
                manager = rel["manager"]
                manager_span[manager] = manager_span.get(manager, 0) + 1
            
            # Find managers with high span of control (>5 direct reports)
            high_span_managers = [
                {"manager": manager, "direct_reports": count}
                for manager, count in manager_span.items()
                if count > 5
            ]
            
            return {
                "success": True,
                "reporting_relationships": reporting_relationships,
                "top_level_people": top_level_people,
                "individual_contributors": individual_contributors,
                "manager_span_of_control": manager_span,
                "high_span_managers": high_span_managers,
                "total_people": len(top_level_people) + len(individual_contributors),
                "total_managers": len(manager_span),
                "avg_span_of_control": sum(manager_span.values()) / len(manager_span) if manager_span else 0
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error analyzing organizational structure: {str(e)}"}


def find_process_dependencies(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Find dependencies between processes and identify potential issues.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing process dependency analysis
    """
    try:
        with driver.session() as session:
            # Find direct process dependencies
            dependencies_query = """
            MATCH (p1:Process)-[r:DEPENDS_ON]->(p2:Process)
            RETURN p1.name as dependent_process, p2.name as dependency_process,
                   r.description as dependency_description
            """
            
            # Find circular dependencies
            circular_deps_query = """
            MATCH path = (p1:Process)-[:DEPENDS_ON*2..]->(p1)
            RETURN [node in nodes(path) | node.name] as circular_path
            """
            
            # Find processes with no dependencies
            independent_processes_query = """
            MATCH (p:Process)
            WHERE NOT (p)-[:DEPENDS_ON]->(:Process) AND NOT (:Process)-[:DEPENDS_ON]->(p)
            RETURN p.name as process_name, p.description as description
            """
            
            dependencies_result = session.run(dependencies_query)
            circular_result = session.run(circular_deps_query)
            independent_result = session.run(independent_processes_query)
            
            dependencies = [dict(record) for record in dependencies_result]
            circular_dependencies = [dict(record) for record in circular_result]
            independent_processes = [dict(record) for record in independent_result]
            
            # Analyze dependency chains
            dependency_chains = {}
            for dep in dependencies:
                dependent = dep["dependent_process"]
                if dependent not in dependency_chains:
                    dependency_chains[dependent] = []
                dependency_chains[dependent].append(dep["dependency_process"])
            
            # Find long dependency chains (>3 levels)
            long_chains = []
            for process, deps in dependency_chains.items():
                if len(deps) > 3:
                    long_chains.append({
                        "process": process,
                        "dependency_count": len(deps),
                        "dependencies": deps
                    })
            
            return {
                "success": True,
                "dependencies": dependencies,
                "circular_dependencies": circular_dependencies,
                "independent_processes": independent_processes,
                "dependency_chains": dependency_chains,
                "long_dependency_chains": long_chains,
                "total_dependencies": len(dependencies),
                "circular_dependency_count": len(circular_dependencies),
                "independent_process_count": len(independent_processes)
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding process dependencies: {str(e)}"}


def calculate_organizational_metrics(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Calculate key organizational metrics and KPIs.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing calculated metrics
    """
    try:
        with driver.session() as session:
            # Basic counts
            counts_query = """
            MATCH (p:Person) WITH count(p) as person_count
            MATCH (proc:Process) WITH person_count, count(proc) as process_count
            MATCH (d:Department) WITH person_count, process_count, count(d) as department_count
            MATCH ()-[r]->() WITH person_count, process_count, department_count, count(r) as relationship_count
            RETURN person_count, process_count, department_count, relationship_count
            """
            
            # Process assignment metrics
            assignment_query = """
            MATCH (p:Person)-[:PERFORMS]->(proc:Process)
            WITH p, count(proc) as process_count
            RETURN avg(process_count) as avg_processes_per_person,
                   max(process_count) as max_processes_per_person,
                   min(process_count) as min_processes_per_person
            """
            
            # Department distribution
            department_query = """
            MATCH (p:Person)-[:BELONGS_TO]->(d:Department)
            WITH d.name as department, count(p) as person_count
            RETURN department, person_count
            ORDER BY person_count DESC
            """
            
            counts_result = session.run(counts_query)
            assignment_result = session.run(assignment_query)
            department_result = session.run(department_query)
            
            counts = counts_result.single()
            assignment_metrics = assignment_result.single()
            department_distribution = [dict(record) for record in department_result]
            
            # Calculate additional metrics
            total_people = counts["person_count"] if counts else 0
            total_processes = counts["process_count"] if counts else 0
            total_departments = counts["department_count"] if counts else 0
            
            # Process coverage (percentage of processes assigned to people)
            coverage_query = """
            MATCH (proc:Process)
            WITH count(proc) as total_processes
            MATCH (proc:Process)<-[:PERFORMS]-(:Person)
            WITH total_processes, count(proc) as assigned_processes
            RETURN total_processes, assigned_processes,
                   (assigned_processes * 100.0 / total_processes) as coverage_percentage
            """
            
            coverage_result = session.run(coverage_query)
            coverage = coverage_result.single()
            
            return {
                "success": True,
                "basic_counts": {
                    "total_people": total_people,
                    "total_processes": total_processes,
                    "total_departments": total_departments,
                    "total_relationships": counts["relationship_count"] if counts else 0
                },
                "assignment_metrics": {
                    "avg_processes_per_person": assignment_metrics["avg_processes_per_person"] if assignment_metrics else 0,
                    "max_processes_per_person": assignment_metrics["max_processes_per_person"] if assignment_metrics else 0,
                    "min_processes_per_person": assignment_metrics["min_processes_per_person"] if assignment_metrics else 0
                },
                "department_distribution": department_distribution,
                "process_coverage": {
                    "total_processes": coverage["total_processes"] if coverage else 0,
                    "assigned_processes": coverage["assigned_processes"] if coverage else 0,
                    "coverage_percentage": coverage["coverage_percentage"] if coverage else 0
                }
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error calculating organizational metrics: {str(e)}"}


def find_communication_patterns(driver: GraphDatabase) -> Dict[str, Any]:
    """
    Analyze communication patterns and potential silos in the organization.
    
    Args:
        driver: Neo4j driver instance
    
    Returns:
        Dict containing communication pattern analysis
    """
    try:
        with driver.session() as session:
            # Find inter-departmental collaborations
            inter_dept_query = """
            MATCH (p1:Person)-[:COLLABORATES_WITH]->(p2:Person)
            WHERE p1.department <> p2.department
            RETURN p1.department as dept1, p2.department as dept2, count(*) as collaboration_count
            ORDER BY collaboration_count DESC
            """
            
            # Find intra-departmental collaborations
            intra_dept_query = """
            MATCH (p1:Person)-[:COLLABORATES_WITH]->(p2:Person)
            WHERE p1.department = p2.department
            WITH p1.department as department, count(*) as collaboration_count
            RETURN department, collaboration_count
            ORDER BY collaboration_count DESC
            """
            
            # Find isolated people (no collaborations)
            isolated_query = """
            MATCH (p:Person)
            WHERE NOT (p)-[:COLLABORATES_WITH]-(:Person)
            RETURN p.name as name, p.department as department, p.role as role
            """
            
            inter_dept_result = session.run(inter_dept_query)
            intra_dept_result = session.run(intra_dept_query)
            isolated_result = session.run(isolated_query)
            
            inter_dept_collaborations = [dict(record) for record in inter_dept_result]
            intra_dept_collaborations = [dict(record) for record in intra_dept_result]
            isolated_people = [dict(record) for record in isolated_result]
            
            # Calculate collaboration ratios
            total_inter_dept = sum(c["collaboration_count"] for c in inter_dept_collaborations)
            total_intra_dept = sum(c["collaboration_count"] for c in intra_dept_collaborations)
            
            collaboration_ratio = total_inter_dept / total_intra_dept if total_intra_dept > 0 else 0
            
            return {
                "success": True,
                "inter_departmental_collaborations": inter_dept_collaborations,
                "intra_departmental_collaborations": intra_dept_collaborations,
                "isolated_people": isolated_people,
                "collaboration_metrics": {
                    "total_inter_dept_collaborations": total_inter_dept,
                    "total_intra_dept_collaborations": total_intra_dept,
                    "collaboration_ratio": collaboration_ratio,
                    "isolated_people_count": len(isolated_people)
                }
            }
            
    except Exception as e:
        return {"success": False, "error": f"Error finding communication patterns: {str(e)}"}


# Tool registry for this module
TOOLS = {
    "find_bottlenecks": {
        "function": find_bottlenecks,
        "description": "Find processes that are bottlenecks (unassigned or overloaded)",
        "category": "analysis",
        "permissions": ["analyzer", "admin", "user"]
    },
    "analyze_organizational_structure": {
        "function": analyze_organizational_structure,
        "description": "Analyze the organizational hierarchy and reporting structure",
        "category": "analysis",
        "permissions": ["analyzer", "admin", "user"]
    },
    "find_process_dependencies": {
        "function": find_process_dependencies,
        "description": "Find dependencies between processes and identify potential issues",
        "category": "analysis",
        "permissions": ["analyzer", "admin", "user"]
    },
    "calculate_organizational_metrics": {
        "function": calculate_organizational_metrics,
        "description": "Calculate key organizational metrics and KPIs",
        "category": "analysis",
        "permissions": ["analyzer", "admin", "user"]
    },
    "find_communication_patterns": {
        "function": find_communication_patterns,
        "description": "Analyze communication patterns and potential silos in the organization",
        "category": "analysis",
        "permissions": ["analyzer", "admin", "user"]
    }
}
