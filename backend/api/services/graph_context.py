import os
import sys
import json
from typing import Any, Dict, List, Tuple

# Ensure project root on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


def _prune_nodes(nodes: List[Dict[str, Any]], max_nodes: int) -> List[Dict[str, Any]]:
    if len(nodes) <= max_nodes:
        return nodes
    # Simple heuristic: prioritize nodes having a 'name' then truncate
    scored = []
    for n in nodes:
        score = 1 if "name" in n.get("properties", {}) else 0
        scored.append((score, n))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, n in scored[:max_nodes]]


def _build_summary(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    # List key entities
    persons = [n for n in nodes if "Person" in n.get("labels", []) or n.get("type") == "Person"]
    departments = [n for n in nodes if "Department" in n.get("labels", []) or n.get("type") == "Department"]
    processes = [n for n in nodes if "Process" in n.get("labels", []) or n.get("type") == "Process"]
    projects = [n for n in nodes if "Project" in n.get("labels", []) or n.get("type") == "Project"]

    if persons:
        parts.append("People: " + ", ".join([str(n.get("properties", {}).get("name", n.get("id"))) for n in persons[:8]]))
    if departments:
        parts.append("Departments: " + ", ".join([str(n.get("properties", {}).get("name", n.get("id"))) for n in departments[:8]]))
    if processes:
        parts.append("Processes: " + ", ".join([str(n.get("properties", {}).get("name", n.get("id"))) for n in processes[:8]]))
    if projects:
        parts.append("Projects: " + ", ".join([str(n.get("properties", {}).get("name", n.get("id"))) for n in projects[:8]]))

    # Relationship counts
    rel_counts: Dict[str, int] = {}
    for e in edges:
        rel_type = e.get("type") or e.get("label") or "REL"
        rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
    if rel_counts:
        parts.append("Relationships: " + ", ".join([f"{k}={v}" for k, v in sorted(rel_counts.items())]))

    return " | ".join(parts)[:3000]


def _convert_to_frontend_graph(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Convert to GraphVisualization.tsx expected shape
    frontend_nodes = []
    for n in nodes:
        node_type = n.get("labels", [None])[0] if n.get("labels") else n.get("properties", {}).get("type")
        frontend_nodes.append({
            "id": n.get("id"),
            "label": n.get("properties", {}).get("name") or ",".join(n.get("labels", [])) or n.get("id"),
            "type": node_type or "Node",
            "properties": n.get("properties", {}),
        })

    frontend_edges = []
    for e in edges:
        frontend_edges.append({
            "id": e.get("id"),
            "source": e.get("start_node", {}).get("id") or e.get("source"),
            "target": e.get("end_node", {}).get("id") or e.get("target"),
            "type": e.get("type") or e.get("label") or "REL",
            "properties": e.get("properties", {}),
        })

    return {"nodes": frontend_nodes, "edges": frontend_edges}


def get_graph_context(query: str, max_nodes: int = 25) -> Tuple[str, Dict[str, Any]]:
    # Try Neo4j first, but fall back to local JSON demo data when unavailable
    try:
        # Lazy import to avoid crashing when Neo4j env is missing
        from strands_agents.src.tools.neo4j_tool import Neo4jTool  # type: ignore

        tool = Neo4jTool()
        nodes = tool.get_all_nodes(limit=max_nodes * 2)
        rels = tool.get_all_relationships(limit=max_nodes * 3)
    except Exception:
        # Demo mode fallback using local JSON
        data_dir = os.path.join(ROOT_DIR, "data")
        entities_fp = os.path.join(data_dir, "custom_demo_entities.json")
        rels_fp = os.path.join(data_dir, "custom_demo_relationships.json")
        nodes: List[Dict[str, Any]] = []
        rels: List[Dict[str, Any]] = []
        try:
            with open(entities_fp, "r", encoding="utf-8") as f:
                ents = json.load(f)
                for e in ents:
                    nodes.append({
                        "id": e.get("id") or e.get("uuid") or str(e.get("name", "node")),
                        "labels": [e.get("type", "Node")],
                        "properties": {k: v for k, v in e.items() if k not in {"id", "uuid", "type"}},
                    })
            with open(rels_fp, "r", encoding="utf-8") as f:
                rs = json.load(f)
                for r in rs:
                    rels.append({
                        "id": r.get("id") or r.get("uuid") or f"rel-{len(rels)}",
                        "type": r.get("type", "REL"),
                        "start_node": {"id": r.get("source")},
                        "end_node": {"id": r.get("target")},
                        "properties": {k: v for k, v in r.items() if k not in {"id", "uuid", "type", "source", "target"}},
                    })
        except Exception:
            # Last resort: empty graph
            nodes, rels = [], []

    # Map node ids to keep relevant edges only
    pruned_nodes = _prune_nodes(nodes, max_nodes)
    keep_ids = {n["id"] for n in pruned_nodes}
    pruned_edges = [
        e for e in rels
        if (e.get("start_node", {}).get("id") in keep_ids) and (e.get("end_node", {}).get("id") in keep_ids)
    ][: max_nodes * 2]

    summary = _build_summary(pruned_nodes, pruned_edges)
    graph_payload = _convert_to_frontend_graph(pruned_nodes, pruned_edges)
    return summary, graph_payload


