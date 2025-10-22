import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure we can import local libs
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Local services
from .services.graph_context import get_graph_context
from .services.sagemaker_client import (
    check_endpoint_ready,
    invoke_strategy_model,
    enhance_query_with_claude,
    generate_multiple_search_queries,
)
from .services.exa_client import exa_search, exa_search_multiple_queries
from .prompting.strategy_prompt import build_prompt


class StrategyRequest(BaseModel):
    query: str
    useExa: Optional[bool] = False
    maxNodes: Optional[int] = 25
    enhance: Optional[bool] = False
    deepSearch: Optional[bool] = False


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
        "endpoint": endpoint,
        "region": region,
    }
    try:
        if endpoint and region:
            status["sagemaker_ready"] = check_endpoint_ready(endpoint)
        else:
            status["sagemaker_ready"] = False
            status["note"] = "Missing SAGEMAKER_ENDPOINT_NAME or AWS_REGION"
    except Exception as e:
        status["sagemaker_ready"] = False
        status["error"] = str(e)
    return status


@app.get("/api/graph-context")
def graph_context(maxNodes: int = Query(25, ge=1, le=50), q: Optional[str] = None) -> Dict[str, Any]:
    try:
        summary, graph = get_graph_context(query=q or "", max_nodes=maxNodes)
        return {"summary": summary, "graph": graph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GraphContextError: {e}")


@app.post("/api/strategy")
def strategy(req: StrategyRequest) -> Dict[str, Any]:
    # Use Bedrock Agent directly (skip SageMaker)
    endpoint = "bedrock-agent-strategy"  # Not used anymore
    region = os.getenv("AWS_REGION", "us-east-1")

    # Optionally enhance query first (Claude) for better Exa and graph retrieval
    user_query = req.query
    if req.enhance:
        user_query = enhance_query_with_claude(user_query)

    # Fetch graph context first (Backend-First Integration)
    try:
        graph_summary, graph_payload = get_graph_context(query=user_query, max_nodes=int(req.maxNodes or 25))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GraphContextError: {e}")

    # Optionally augment with Exa.ai snippets using enhanced search
    exa_snippets: List[Dict[str, str]] = []
    if req.useExa:
        try:
            if req.deepSearch:
                # Generate multiple targeted queries for comprehensive coverage
                search_queries = generate_multiple_search_queries(user_query)
                print(f"Deep search - Generated queries: {search_queries}")
                
                # Use enhanced Exa search with multiple queries
                exa_snippets = exa_search_multiple_queries(search_queries, top_k_per_query=2)
                
                # If no results from multiple queries, fall back to single enhanced search
                if not exa_snippets:
                    exa_snippets = exa_search(user_query, top_k=5, use_autoprompt=True)
            else:
                # Quick search with single enhanced query
                print(f"🔍 Quick search - Query: {user_query}")
                exa_snippets = exa_search(user_query, top_k=5, use_autoprompt=True)
                print(f"🔍 Exa search returned {len(exa_snippets)} results")
                if exa_snippets:
                    print(f"🔍 First result: {exa_snippets[0].get('title', 'No title')}")
                else:
                    print("🔍 No results from Exa search")
                
        except Exception as e:
            # Graceful fallback - log error but continue without Exa
            print(f"⚠️ Exa search failed: {e}")
            exa_snippets = []

    # Build prompt with strict structured output and smart Exa integration
    prompt = build_prompt(query=user_query, graph_summary=graph_summary, exa_snippets=exa_snippets)

    # Invoke Bedrock Agent
    try:
        result = invoke_strategy_model(endpoint_name=endpoint, region=region, prompt=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BedrockAgent InvokeError: {e}")

    # Support both legacy string and new dict with source
    if isinstance(result, dict):
        return {"text": result.get("text", ""), "source": result.get("source", "unknown"), "links": exa_snippets, "graph": graph_payload}
    else:
        return {"text": str(result), "source": "sagemaker", "links": exa_snippets, "graph": graph_payload}


class EnhanceRequest(BaseModel):
    query: str


@app.post("/api/enhance")
def enhance(req: EnhanceRequest) -> Dict[str, str]:
    try:
        rewritten = enhance_query_with_claude(req.query)
        return {"query": rewritten}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EnhanceError: {e}")


# --- Compatibility endpoints for current frontend (will be removed later) ---

@app.get("/api/agents")
def agents_catalogue() -> Dict[str, Any]:
    return {
        "graph": {
            "name": "Graph Strategy Agent",
            "role": "Injects Neo4j graph context and returns strategy",
            "available_tools": ["neo4j", "sagemaker", "exa"],
            "description": "Graph-aware strategy assistant",
        }
    }


class ChatRequest(BaseModel):
    message: str
    agent_type: Optional[str] = "graph"


@app.post("/api/chat")
def legacy_chat(req: ChatRequest) -> Dict[str, Any]:
    # Map to strategy endpoint
    out = strategy(StrategyRequest(query=req.message, useExa=False))
    return {"response": out.get("text", ""), "agent_type": req.agent_type, "timestamp": ""}


@app.get("/api/graph")
def legacy_graph() -> Dict[str, Any]:
    # Map to graph-context endpoint and return only graph for legacy UI path
    data = graph_context(maxNodes=25)
    return data.get("graph", {})


