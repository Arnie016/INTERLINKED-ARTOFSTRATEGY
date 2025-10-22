"""
Vercel entry point for the FastAPI backend
"""

import os
import sys

# Add the project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Import and create the FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

# Import our services
from backend.api.services.graph_context import get_graph_context
from backend.api.services.sagemaker_client import (
    check_endpoint_ready,
    invoke_strategy_model,
    enhance_query_with_claude,
    generate_multiple_search_queries,
)
from backend.api.services.exa_client import exa_search, exa_search_multiple_queries
from backend.api.prompting.strategy_prompt import build_prompt

class StrategyRequest(BaseModel):
    query: str
    useExa: Optional[bool] = False
    maxNodes: Optional[bool] = 25
    enhance: Optional[bool] = False
    deepSearch: Optional[bool] = False

# Create FastAPI app
app = FastAPI(title="Interlinked Strategy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health() -> Dict[str, Any]:
    endpoint = os.getenv("SAGEMAKER_ENDPOINT_NAME")
    region = os.getenv("AWS_REGION")
    status = {
        "ok": True,
        "timestamp": "2024-01-01T00:00:00Z",
        "endpoint": endpoint,
        "region": region,
        "exa_key_set": bool(os.getenv("EXA_API_KEY")),
    }
    return status

@app.get("/api/graph-context")
def graph_context() -> Dict[str, Any]:
    """Get organizational graph context"""
    try:
        graph_data = get_graph_context()
        return graph_data
    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}

@app.post("/api/strategy")
def strategy(request: StrategyRequest) -> Dict[str, Any]:
    """Generate strategic analysis"""
    try:
        # Get graph context
        graph_data = get_graph_context()
        graph_summary = f"Organizational graph with {len(graph_data.get('nodes', []))} nodes and {len(graph_data.get('edges', []))} relationships"
        
        # Get external intelligence if requested
        exa_snippets = []
        if request.useExa:
            try:
                if request.deepSearch:
                    queries = generate_multiple_search_queries(request.query)
                    exa_snippets = exa_search_multiple_queries(queries)
                else:
                    exa_snippets = exa_search(request.query)
            except Exception as e:
                print(f"⚠️ Exa search failed: {e}")
                exa_snippets = []
        
        # Build prompt
        prompt = build_prompt(request.query, graph_summary, exa_snippets)
        
        # Get AI response
        endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME", "bedrock-primary")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        result = invoke_strategy_model(endpoint_name, region, prompt)
        
        return {
            "text": result["text"],
            "source": result["source"],
            "links": exa_snippets,
            "graph": graph_data
        }
        
    except Exception as e:
        return {"error": str(e), "text": "Sorry, I encountered an error. Please try again."}

@app.post("/api/enhance")
def enhance_query(request: Dict[str, str]) -> Dict[str, str]:
    """Enhance query for better results"""
    try:
        query = request.get("query", "")
        enhanced = enhance_query_with_claude(query)
        return {"enhanced_query": enhanced}
    except Exception as e:
        return {"error": str(e), "enhanced_query": query}