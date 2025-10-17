import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.agents import create_orchestrator_agent
from dotenv import load_dotenv

load_dotenv()
orchestrator = create_orchestrator_agent(user_role="user")

print("🤖 Orchestrator Ready! Type your query:")
while True:
    query = input("\nYou: ").strip()
    if query.lower() in ['exit', 'quit']: break
    if not query: continue
    print(f"\nOrchestrator: {orchestrator(query)}")
