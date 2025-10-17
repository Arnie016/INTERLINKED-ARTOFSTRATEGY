"""
Testing Utilities for Strands Agents

Provides test helpers including:
- Mock Neo4j responses
- Sample graph data fixtures
- Request/response mocks
- Test data generators
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


# ============================================================================
# Mock Neo4j Responses
# ============================================================================

class MockNeo4jRecord:
    """Mock Neo4j record for testing."""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getitem__(self, key: str):
        return self._data[key]
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()


class MockNeo4jResult:
    """Mock Neo4j result for testing."""
    
    def __init__(self, records: List[Dict[str, Any]]):
        self._records = [MockNeo4jRecord(r) for r in records]
        self._index = 0
    
    def __iter__(self):
        return iter(self._records)
    
    def __next__(self):
        if self._index >= len(self._records):
            raise StopIteration
        record = self._records[self._index]
        self._index += 1
        return record
    
    def data(self):
        """Return records as list of dictionaries."""
        return [dict(r._data) for r in self._records]
    
    def single(self):
        """Return single record or None."""
        return self._records[0] if self._records else None


# ============================================================================
# Sample Graph Data Fixtures
# ============================================================================

def create_mock_person_node(
    node_id: int = 1,
    name: str = "Alice Johnson",
    email: str = "alice@example.com",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock Person node.
    
    Args:
        node_id: Node ID
        name: Person name
        email: Email address
        **kwargs: Additional properties
    
    Returns:
        Mock node dictionary
    """
    node = {
        "id": node_id,
        "label": "Person",
        "properties": {
            "name": name,
            "email": email,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "active"
        }
    }
    
    # Add any additional properties
    node["properties"].update(kwargs)
    
    return node


def create_mock_organization_node(
    node_id: int = 1,
    name: str = "Acme Corp",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock Organization node.
    
    Args:
        node_id: Node ID
        name: Organization name
        **kwargs: Additional properties
    
    Returns:
        Mock node dictionary
    """
    node = {
        "id": node_id,
        "label": "Organization",
        "properties": {
            "name": name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "active"
        }
    }
    
    node["properties"].update(kwargs)
    
    return node


def create_mock_project_node(
    node_id: int = 1,
    name: str = "Project Alpha",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock Project node.
    
    Args:
        node_id: Node ID
        name: Project name
        **kwargs: Additional properties
    
    Returns:
        Mock node dictionary
    """
    node = {
        "id": node_id,
        "label": "Project",
        "properties": {
            "name": name,
            "description": f"Description for {name}",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "active"
        }
    }
    
    node["properties"].update(kwargs)
    
    return node


def create_mock_relationship(
    rel_id: int = 1,
    rel_type: str = "WORKS_AT",
    from_node_id: int = 1,
    to_node_id: int = 2,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock relationship.
    
    Args:
        rel_id: Relationship ID
        rel_type: Relationship type
        from_node_id: Source node ID
        to_node_id: Target node ID
        **kwargs: Additional properties
    
    Returns:
        Mock relationship dictionary
    """
    relationship = {
        "id": rel_id,
        "type": rel_type,
        "from_node": from_node_id,
        "to_node": to_node_id,
        "properties": {
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    relationship["properties"].update(kwargs)
    
    return relationship


def create_mock_graph(
    num_people: int = 5,
    num_orgs: int = 2,
    num_projects: int = 3
) -> Dict[str, Any]:
    """
    Create a mock graph with people, organizations, and projects.
    
    Args:
        num_people: Number of Person nodes
        num_orgs: Number of Organization nodes
        num_projects: Number of Project nodes
    
    Returns:
        Dictionary with nodes and relationships
    """
    nodes = []
    relationships = []
    current_id = 1
    
    # Create person nodes
    people_ids = []
    for i in range(num_people):
        node = create_mock_person_node(
            node_id=current_id,
            name=f"Person {i+1}",
            email=f"person{i+1}@example.com",
            title=random.choice(["Engineer", "Manager", "Designer", "Analyst"])
        )
        nodes.append(node)
        people_ids.append(current_id)
        current_id += 1
    
    # Create organization nodes
    org_ids = []
    for i in range(num_orgs):
        node = create_mock_organization_node(
            node_id=current_id,
            name=f"Organization {i+1}",
            description=f"Description for Organization {i+1}"
        )
        nodes.append(node)
        org_ids.append(current_id)
        current_id += 1
    
    # Create project nodes
    project_ids = []
    for i in range(num_projects):
        node = create_mock_project_node(
            node_id=current_id,
            name=f"Project {i+1}"
        )
        nodes.append(node)
        project_ids.append(current_id)
        current_id += 1
    
    # Create WORKS_AT relationships
    rel_id = 1
    for person_id in people_ids:
        org_id = random.choice(org_ids)
        rel = create_mock_relationship(
            rel_id=rel_id,
            rel_type="WORKS_AT",
            from_node_id=person_id,
            to_node_id=org_id,
            since=datetime.utcnow().isoformat() + "Z"
        )
        relationships.append(rel)
        rel_id += 1
    
    # Create PARTICIPATES_IN relationships
    for person_id in people_ids:
        project_id = random.choice(project_ids)
        rel = create_mock_relationship(
            rel_id=rel_id,
            rel_type="PARTICIPATES_IN",
            from_node_id=person_id,
            to_node_id=project_id,
            role=random.choice(["contributor", "lead", "reviewer"])
        )
        relationships.append(rel)
        rel_id += 1
    
    return {
        "nodes": nodes,
        "relationships": relationships,
        "node_count": len(nodes),
        "relationship_count": len(relationships)
    }


# ============================================================================
# Request/Response Mocks
# ============================================================================

def create_mock_agent_request(
    query: str = "Find all people",
    session_id: Optional[str] = None,
    auth_token: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock agent request.
    
    Args:
        query: User query
        session_id: Optional session ID
        auth_token: Optional auth token
        **kwargs: Additional request fields
    
    Returns:
        Mock request dictionary
    """
    request = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if session_id:
        request["session_id"] = session_id
    
    if auth_token:
        request["auth_token"] = auth_token
    
    request.update(kwargs)
    
    return request


def create_mock_agent_response(
    data: Any,
    status: str = "success",
    execution_time_ms: float = 125.5,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock agent response.
    
    Args:
        data: Response data
        status: Response status
        execution_time_ms: Execution time
        **kwargs: Additional response fields
    
    Returns:
        Mock response dictionary
    """
    response = {
        "status": status,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metadata": {
            "execution_time_ms": execution_time_ms
        }
    }
    
    response.update(kwargs)
    
    return response


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_random_person() -> Dict[str, Any]:
    """Generate random person data for testing."""
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]
    titles = ["Engineer", "Manager", "Designer", "Analyst", "Director", "VP"]
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    return {
        "name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}@example.com",
        "title": random.choice(titles)
    }


def generate_random_organization() -> Dict[str, Any]:
    """Generate random organization data for testing."""
    prefixes = ["Tech", "Global", "Advanced", "Digital", "Smart"]
    suffixes = ["Corp", "Systems", "Solutions", "Dynamics", "Industries"]
    
    return {
        "name": f"{random.choice(prefixes)} {random.choice(suffixes)}",
        "description": "A leading organization in the industry"
    }


def generate_test_dataset(size: str = "small") -> Dict[str, Any]:
    """
    Generate test dataset of varying sizes.
    
    Args:
        size: Dataset size (small, medium, large)
    
    Returns:
        Test dataset with nodes and relationships
    """
    sizes = {
        "small": (5, 2, 3),
        "medium": (20, 5, 10),
        "large": (100, 20, 50)
    }
    
    num_people, num_orgs, num_projects = sizes.get(size, sizes["small"])
    
    return create_mock_graph(num_people, num_orgs, num_projects)


# ============================================================================
# Mock Auth Context
# ============================================================================

def create_mock_auth_context(
    user_id: str = "test-user",
    role: str = "user"
) -> Dict[str, Any]:
    """
    Create mock authentication context.
    
    Args:
        user_id: User identifier
        role: User role
    
    Returns:
        Mock auth context
    """
    return {
        "user_id": user_id,
        "username": user_id,
        "role": role,
        "permissions": ["read:graph", "write:graph"] if role == "user" else ["read:graph"]
    }


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_valid_node(node: Dict[str, Any]):
    """Assert that a node has required fields."""
    assert "id" in node, "Node missing 'id' field"
    assert "label" in node, "Node missing 'label' field"
    assert "properties" in node, "Node missing 'properties' field"


def assert_valid_relationship(rel: Dict[str, Any]):
    """Assert that a relationship has required fields."""
    assert "id" in rel, "Relationship missing 'id' field"
    assert "type" in rel, "Relationship missing 'type' field"
    assert "from_node" in rel, "Relationship missing 'from_node' field"
    assert "to_node" in rel, "Relationship missing 'to_node' field"


def assert_valid_response(response: Dict[str, Any]):
    """Assert that a response has required structure."""
    assert "status" in response, "Response missing 'status' field"
    assert "timestamp" in response, "Response missing 'timestamp' field"
    assert response["status"] in ["success", "error", "partial"], "Invalid status value"

