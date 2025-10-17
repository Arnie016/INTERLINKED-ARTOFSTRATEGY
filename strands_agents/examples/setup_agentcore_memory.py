"""
Setup script for creating AgentCore Memory resources.

This script creates both Short-Term Memory (STM) and Long-Term Memory (LTM)
resources for the orchestrator agent.

Run this script once before deploying to AgentCore Runtime.
"""

from bedrock_agentcore.memory import MemoryClient
import uuid
import os

# Configuration
REGION = os.getenv('AWS_REGION', 'us-west-2')

# Connect to AgentCore Memory service
client = MemoryClient(region_name=REGION)

print("=" * 70)
print("AgentCore Memory Setup for Orchestrator Agent")
print("=" * 70)
print()

# === SHORT-TERM MEMORY ===
print("Creating Short-Term Memory (STM)...")
print("  Purpose: Stores raw conversation turns within a session")
print("  Retention: 30 days")
print()

stm = client.create_memory_and_wait(
    name=f"OrgGraph_STM_{uuid.uuid4().hex[:8]}",
    strategies=[],  # No extraction - just raw storage
    event_expiry_days=30
)

print(f"✅ STM Created: {stm['id']}")
print(f"   Name: {stm['name']}")
print()

# === LONG-TERM MEMORY ===
print("Creating Long-Term Memory (LTM)...")
print("  Purpose: Extracts preferences and facts across sessions")
print("  Retention: 180 days")
print("  Extraction Strategies:")
print("    - User preferences (coding style, notification preferences, etc.)")
print("    - Semantic facts (org structure, relationships, key info)")
print()

ltm = client.create_memory_and_wait(
    name=f"OrgGraph_LTM_{uuid.uuid4().hex[:8]}",
    strategies=[
        # Extract user preferences
        {
            "userPreferenceMemoryStrategy": {
                "name": "user_preferences",
                "namespaces": ["/user/preferences", "/user/settings"]
            }
        },
        # Extract organizational facts
        {
            "semanticMemoryStrategy": {
                "name": "org_facts",
                "namespaces": ["/org/structure", "/org/relationships", "/org/facts"]
            }
        }
    ],
    event_expiry_days=180
)

print(f"✅ LTM Created: {ltm['id']}")
print(f"   Name: {ltm['name']}")
print()

# === SUMMARY ===
print("=" * 70)
print("Setup Complete! Choose which memory to use:")
print("=" * 70)
print()
print("For SESSION-BASED MEMORY (remembers within session only):")
print(f"  export MEMORY_ID={stm['id']}")
print()
print("For CROSS-SESSION MEMORY (remembers preferences across sessions):")
print(f"  export MEMORY_ID={ltm['id']}")
print()
print("=" * 70)
print()
print("Next Steps:")
print("  1. Set MEMORY_ID environment variable (choose STM or LTM above)")
print("  2. Configure deployment: agentcore configure --entrypoint examples/agentcore_deployment_handler.py")
print("  3. Deploy: agentcore launch")
print()
print("Memory Comparison:")
print()
print("  SHORT-TERM MEMORY (STM):")
print("    ✓ Instant retrieval")
print("    ✓ Exact conversation recall")
print("    ✗ Session-isolated (doesn't cross sessions)")
print("    ✗ No intelligent extraction")
print()
print("  LONG-TERM MEMORY (LTM):")
print("    ✓ Cross-session memory")
print("    ✓ Intelligent preference extraction")
print("    ✓ Semantic fact recall")
print("    ⚠ 5-10 second extraction delay")
print("    ⚠ Requires more processing")
print()
print("Recommendation: Use LTM for production, STM for testing")
print()

