import os
from typing import Dict, List, Optional
import requests


def enhance_query_for_external_search(query: str) -> str:
    """Enhance internal organizational queries for better external search results"""
    query_lower = query.lower()
    
    # Map internal concepts to external search terms
    if "engineering delivery time" in query_lower or "reduce delivery" in query_lower:
        return "software development productivity tools 2024 agile devops CI/CD automation"
    elif "code review" in query_lower:
        return "code review tools automation AI-powered development 2024"
    elif "customer onboarding" in query_lower:
        return "customer onboarding automation tools SaaS platforms 2024"
    elif "ai-powered analytics" in query_lower or "analytics platform" in query_lower:
        return "AI analytics platforms business intelligence tools 2024"
    elif "cross-functional collaboration" in query_lower or "team collaboration" in query_lower:
        return "team collaboration tools project management software 2024"
    elif "process optimization" in query_lower or "workflow automation" in query_lower:
        return "business process automation workflow tools 2024"
    elif "engineering" in query_lower and ("team" in query_lower or "department" in query_lower):
        return "engineering team management software development productivity 2024"
    else:
        # For general business queries, add relevant business/tech context
        return f"{query} business strategy technology trends 2024"


def exa_search(query: str, top_k: int = 5, use_autoprompt: bool = True, 
                include_domains: Optional[List[str]] = None,
                exclude_domains: Optional[List[str]] = None,
                start_published_date: Optional[str] = None,
                end_published_date: Optional[str] = None) -> List[Dict[str, str]]:
    """Enhanced Exa.ai search with better query handling"""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("⚠️ EXA_API_KEY not set - returning empty results")
        return []

    # Enhance query for better external search results
    enhanced_query = enhance_query_for_external_search(query)
    
    url = "https://api.exa.ai/search"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "query": enhanced_query,
        "num_results": max(1, min(top_k, 10)),
        "use_autoprompt": use_autoprompt,  # Let Exa enhance the query
        "type": "neural",  # Use neural search for better relevance
        "text": True,  # Include text snippets
        "summary": True,  # Include summaries
    }
    
    # Add domain filtering
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    
    # Add date filtering
    if start_published_date:
        payload["start_published_date"] = start_published_date
    if end_published_date:
        payload["end_published_date"] = end_published_date

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            print(f"⚠️ Exa API error {resp.status_code}: {resp.text}")
            return []

        data = resp.json()
        items = data.get("results") or data.get("data") or []
        
        # If no results, try a fallback query
        if not items and enhanced_query != query:
            print(f"🔄 No results for enhanced query, trying original: {query}")
            payload["query"] = query
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("results") or data.get("data") or []
        
        out: List[Dict[str, str]] = []
        for it in items:
            out.append(
                {
                    "title": it.get("title") or it.get("name") or "",
                    "url": it.get("url") or it.get("link") or "",
                    "snippet": it.get("snippet") or it.get("summary") or "",
                    "published_date": it.get("published_date", ""),
                    "author": it.get("author", ""),
                    "score": it.get("score", 0.0),  # Relevance score
                }
            )
            if len(out) >= top_k:
                break
        
        print(f"✅ Exa search found {len(out)} results for query: {enhanced_query}")
        return out
        
    except Exception as e:
        print(f"⚠️ Exa search error: {e}")
        return []


def exa_search_multiple_queries(queries: List[str], top_k_per_query: int = 3) -> List[Dict[str, str]]:
    """Search multiple related queries and combine results"""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        print("⚠️ EXA_API_KEY not set - returning empty results")
        return []
        
    all_results = []
    seen_urls = set()
    
    for query in queries:
        try:
            results = exa_search(query, top_k_per_query)
            for result in results:
                if result["url"] not in seen_urls:
                    all_results.append(result)
                    seen_urls.add(result["url"])
        except Exception as e:
            print(f"Exa search failed for query '{query}': {e}")
            continue
    
    # Sort by score if available
    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


def exa_get_content(url: str) -> Optional[str]:
    """Get full content from a URL using Exa.ai"""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return None
    
    url_endpoint = "https://api.exa.ai/contents"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"url": url}
    
    try:
        resp = requests.post(url_endpoint, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("text", "")
    except Exception as e:
        print(f"Failed to get content from {url}: {e}")
    
    return None
