import json
import os
from typing import Any

import boto3
import requests


def check_endpoint_ready(endpoint_name: str) -> bool:
    sm = boto3.client("sagemaker", region_name=os.getenv("AWS_REGION"))
    resp = sm.describe_endpoint(EndpointName=endpoint_name)
    return resp.get("EndpointStatus") == "InService"


def invoke_bedrock_fallback(prompt: str) -> str:
    """Fallback to Bedrock when SageMaker endpoint is not ready"""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        # Use Claude 3 Haiku via Bedrock
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "system": "You are a strategic business analyst. Provide structured analysis with <strategic_analysis> and <action_plan> XML tags.",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(payload)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body.get('content', [{}])[0].get('text', 'No response from Bedrock')
        
    except Exception as e:
        # Fallback to Claude API if Bedrock fails
        return invoke_claude_fallback(prompt)


def invoke_claude_fallback(prompt: str) -> str:
    """Fallback to Claude API when SageMaker endpoint is not ready"""
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment")
    
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 512,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Claude API error: {response.status_code} - {response.text}")
    
    data = response.json()
    return data["content"][0]["text"]


def enhance_query_with_claude(query: str) -> str:
    """Ask Claude to clarify and specialize a search/strategy query.
    Returns a concise, specific rewrite suitable for Exa + strategy prompting.
    """
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        # If no key, just return original
        return query

    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    system_msg = (
        "Rewrite the user's query to be specific, factual, and scoping-friendly for web search "
        "and organizational strategy. Keep it under 200 characters. Include key entities, timeframes, "
        "and desired outcomes if implied. Output only the rewritten query."
    )
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 128,
        "system": system_msg,
        "messages": [
            {"role": "user", "content": query},
        ],
    }
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=20,
        )
        if resp.status_code != 200:
            return query
        data = resp.json()
        text = data.get("content", [{}])[0].get("text", "").strip()
        return text or query
    except Exception:
        return query


def generate_multiple_search_queries(query: str) -> list[str]:
    """Generate multiple targeted search queries for comprehensive coverage"""
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        return [query]

    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    system_msg = (
        "Generate 3-4 different search queries that would comprehensively cover the user's topic. "
        "Each query should focus on a different aspect: problems/challenges, solutions/best practices, "
        "case studies/examples, and trends/future outlook. Return only the queries, one per line."
    )
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 200,
        "system": system_msg,
        "messages": [
            {"role": "user", "content": f"Topic: {query}"},
        ],
    }
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=20,
        )
        if resp.status_code != 200:
            return [query]
        data = resp.json()
        text = data.get("content", [{}])[0].get("text", "").strip()
        if text:
            queries = [q.strip() for q in text.split('\n') if q.strip()]
            return queries[:4]  # Limit to 4 queries
        return [query]
    except Exception:
        return [query]


def invoke_sagemaker(endpoint_name: str, region: str, prompt: str) -> str:
    runtime = boto3.client("sagemaker-runtime", region_name=region)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }

    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload).encode("utf-8")
    )

    body = response["Body"].read()
    try:
        data = json.loads(body)
    except Exception:
        # Some endpoints return raw text
        return body.decode("utf-8", errors="ignore")

    # Try standard fields used by TGI/vLLM-like handlers
    if isinstance(data, dict):
        if "generated_text" in data:
            return str(data["generated_text"])  # single output
        if "outputs" in data and data["outputs"]:
            # e.g., [{"generated_text": "..."}]
            out0 = data["outputs"][0]
            if isinstance(out0, dict) and "generated_text" in out0:
                return str(out0["generated_text"])
        if "text" in data:
            return str(data["text"])  # generic

    if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
        return str(data[0]["generated_text"])  # list of dicts

    return json.dumps(data)


def invoke_strategy_model(endpoint_name: str, region: str, prompt: str) -> dict:
    """Always use Bedrock for strategy analysis"""
    try:
        print(f"Using Bedrock for strategy analysis")
        text = invoke_bedrock_fallback(prompt)
        return {"text": text, "source": "bedrock"}
    except Exception as bedrock_error:
        print(f"Bedrock failed: {bedrock_error}, trying Claude API")
        try:
            text = invoke_claude_fallback(prompt)
            return {"text": text, "source": "claude"}
        except Exception as claude_error:
            print(f"Claude API failed: {claude_error}")
            # Return error instead of demo response
            return {"text": "Sorry, I encountered an error connecting to AI services. Please try again.", "source": "error"}


