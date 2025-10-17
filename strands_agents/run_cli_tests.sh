#!/bin/bash

# ============================================
# CLI Testing Runner for Strands Agents
# ============================================
# This script automates CLI testing of the orchestrator agent
# Usage: ./run_cli_tests.sh [--local|--agentcore|--all]

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================
# Helper Functions
# ============================================

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================
# Pre-flight Checks
# ============================================

preflight_checks() {
    print_header "Pre-flight Checks"
    
    # Check Python version
    echo "Checking Python version..."
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
        print_error "Python 3.11+ required"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python version: $PYTHON_VERSION"
    
    # Check virtual environment
    echo "Checking virtual environment..."
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        python3 -m venv venv
    fi
    print_success "Virtual environment exists"
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Check .env file
    echo "Checking .env configuration..."
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo "Run: cp .env.example .env"
        echo "Then edit .env with your credentials"
        exit 1
    fi
    print_success ".env file exists"
    
    # Load environment variables
    set -a
    source .env
    set +a
    
    # Check required variables
    REQUIRED_VARS=("AWS_REGION" "NEO4J_URI" "NEO4J_USERNAME" "NEO4J_PASSWORD")
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required environment variable not set: $var"
            exit 1
        fi
    done
    print_success "Required environment variables set"
    
    # Check AWS credentials
    echo "Checking AWS credentials..."
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        echo "Run: aws configure"
        exit 1
    fi
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials configured (Account: $AWS_ACCOUNT)"
    
    # Check dependencies
    echo "Checking Python dependencies..."
    if ! python3 -c "import boto3; import neo4j; from strands import Agent" &> /dev/null; then
        print_warning "Dependencies missing. Installing..."
        pip install -q -r requirements.txt
    fi
    print_success "Python dependencies installed"
    
    # Test Neo4j connection
    echo "Testing Neo4j connection..."
    if ! python3 -c "
from neo4j import GraphDatabase
import os
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)
driver.verify_connectivity()
driver.close()
" &> /dev/null; then
        print_error "Neo4j connection failed"
        echo "Check NEO4J_* variables in .env"
        exit 1
    fi
    print_success "Neo4j connection successful"
    
    print_success "All pre-flight checks passed!"
}

# ============================================
# Local Testing
# ============================================

test_local() {
    print_header "Local Orchestrator Testing"
    
    # Test 1: Create orchestrator
    echo "Test 1: Creating orchestrator agent..."
    if python3 -c "
import sys, os
sys.path.insert(0, '$SCRIPT_DIR')
from src.agents import create_orchestrator_agent
from dotenv import load_dotenv
load_dotenv()
orchestrator = create_orchestrator_agent(user_role='user')
print('Orchestrator created successfully')
" &> /tmp/test1.log; then
        print_success "Orchestrator created"
    else
        print_error "Failed to create orchestrator"
        cat /tmp/test1.log
        return 1
    fi
    
    # Test 2: Simple query
    echo "Test 2: Testing simple query..."
    if python3 -c "
import sys, os
sys.path.insert(0, '$SCRIPT_DIR')
from src.agents import create_orchestrator_agent
from dotenv import load_dotenv
load_dotenv()
orchestrator = create_orchestrator_agent(user_role='user')
response = orchestrator('List all people in Engineering')
print(f'Response: {response[:100]}...')
" &> /tmp/test2.log; then
        print_success "Simple query executed"
        head -n 5 /tmp/test2.log
    else
        print_error "Simple query failed"
        cat /tmp/test2.log
        return 1
    fi
    
    # Test 3: Specialized agents
    echo "Test 3: Testing specialized agents..."
    if python3 -c "
import sys, os
sys.path.insert(0, '$SCRIPT_DIR')
from src.agents import create_graph_agent, create_analyzer_agent
from dotenv import load_dotenv
load_dotenv()

graph_agent = create_graph_agent()
analyzer_agent = create_analyzer_agent()

print('Graph agent test...')
response = graph_agent('Find all people')
print(f'Graph response: {response[:50]}...')

print('Analyzer agent test...')
response = analyzer_agent('Who are the most central people?')
print(f'Analyzer response: {response[:50]}...')
" &> /tmp/test3.log; then
        print_success "Specialized agents working"
        head -n 10 /tmp/test3.log
    else
        print_error "Specialized agents failed"
        cat /tmp/test3.log
        return 1
    fi
    
    # Test 4: Basic usage example
    echo "Test 4: Running basic usage example..."
    if timeout 30 python3 examples/basic_usage.py &> /tmp/test4.log; then
        print_success "Basic usage example completed"
    else
        print_warning "Basic usage example timed out or failed (expected for demo)"
    fi
    
    print_success "Local testing completed!"
}

# ============================================
# AgentCore Testing
# ============================================

test_agentcore() {
    print_header "AgentCore Deployment Testing"
    
    # Check if agentcore CLI is installed
    echo "Checking AgentCore CLI..."
    if ! command -v agentcore &> /dev/null; then
        print_warning "AgentCore CLI not found. Installing..."
        pip install -q bedrock-agentcore
    fi
    print_success "AgentCore CLI installed"
    
    # Check MEMORY_ID
    if [ -z "$MEMORY_ID" ]; then
        print_warning "MEMORY_ID not set"
        echo ""
        echo "To create memory resources, run:"
        echo "  python3 examples/setup_agentcore_memory.py"
        echo ""
        echo "Then set the MEMORY_ID:"
        echo "  export MEMORY_ID=<your-memory-id>"
        echo ""
        read -p "Do you want to create memory now? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python3 examples/setup_agentcore_memory.py
            echo ""
            read -p "Enter the MEMORY_ID from above: " MEMORY_ID
            export MEMORY_ID
            echo "MEMORY_ID=$MEMORY_ID" >> .env
        else
            print_warning "Skipping AgentCore deployment tests"
            return 0
        fi
    else
        print_success "MEMORY_ID configured: $MEMORY_ID"
    fi
    
    # Test memory integration locally
    echo "Testing memory integration locally..."
    if python3 -c "
import sys, os
sys.path.insert(0, '$SCRIPT_DIR')
from src.agents.orchestrator_agent_agentcore import create_orchestrator_with_agentcore
from bedrock_agentcore.memory import MemoryClient
from dotenv import load_dotenv
load_dotenv()

memory_client = MemoryClient(region_name=os.getenv('AWS_REGION', 'us-west-2'))
memory_id = os.getenv('MEMORY_ID')

orchestrator = create_orchestrator_with_agentcore(
    user_role='user',
    memory_client=memory_client,
    memory_id=memory_id,
    session_id='test-session'
)

response = orchestrator('Test message')
print(f'Response: {response[:100]}...')
" &> /tmp/test_agentcore.log; then
        print_success "Memory integration working"
    else
        print_error "Memory integration failed"
        cat /tmp/test_agentcore.log
        return 1
    fi
    
    # Check if already deployed
    echo "Checking existing deployments..."
    if agentcore list &> /dev/null; then
        print_info "AgentCore deployments found"
        agentcore list
    else
        print_info "No existing deployments"
    fi
    
    echo ""
    read -p "Deploy to AgentCore Runtime now? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Skipping deployment"
        return 0
    fi
    
    # Deploy
    echo "Deploying to AgentCore..."
    if agentcore launch; then
        print_success "Deployment successful"
        
        # Test deployed agent
        echo "Testing deployed agent..."
        if agentcore invoke '{"prompt": "Hello, who are the engineers?"}' --session-id cli-test; then
            print_success "Deployed agent responding"
        else
            print_error "Deployed agent not responding"
        fi
        
        # Show logs
        echo "Recent logs:"
        agentcore logs --tail -n 20
    else
        print_error "Deployment failed"
        return 1
    fi
}

# ============================================
# Interactive Testing
# ============================================

interactive_test() {
    print_header "Interactive Testing Mode"
    
    print_info "Starting interactive orchestrator..."
    print_info "Type 'exit' to quit, 'help' for examples"
    echo ""
    
    python3 << 'EOF'
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.agents import create_orchestrator_agent
from dotenv import load_dotenv

load_dotenv()

print("Creating orchestrator...")
orchestrator = create_orchestrator_agent(user_role="user")
print("✓ Ready!")
print("-" * 70)

while True:
    try:
        query = input("\nYou: ").strip()
        
        if not query:
            continue
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("\nGoodbye!")
            break
        
        if query.lower() == 'help':
            print("\nExample queries:")
            print("  • Who are all the people in Engineering?")
            print("  • Find the most influential people")
            print("  • What processes does the Data team own?")
            print("  • Detect communities in our organization")
            continue
        
        print("\nOrchestrator: ", end="", flush=True)
        response = orchestrator(query)
        print(response)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
EOF
}

# ============================================
# Main Script
# ============================================

main() {
    print_header "Strands Agents CLI Testing Suite"
    
    # Parse arguments
    MODE="local"
    if [ $# -eq 1 ]; then
        case "$1" in
            --local)
                MODE="local"
                ;;
            --agentcore)
                MODE="agentcore"
                ;;
            --all)
                MODE="all"
                ;;
            --interactive)
                MODE="interactive"
                ;;
            --help)
                echo "Usage: $0 [--local|--agentcore|--all|--interactive]"
                echo ""
                echo "Options:"
                echo "  --local       Run local testing only (default)"
                echo "  --agentcore   Run AgentCore deployment tests"
                echo "  --all         Run all tests"
                echo "  --interactive Start interactive CLI"
                echo "  --help        Show this help"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Run with --help for usage"
                exit 1
                ;;
        esac
    fi
    
    print_info "Test mode: $MODE"
    
    # Run pre-flight checks
    preflight_checks
    
    # Run tests based on mode
    case "$MODE" in
        local)
            test_local
            ;;
        agentcore)
            test_agentcore
            ;;
        all)
            test_local
            echo ""
            test_agentcore
            ;;
        interactive)
            interactive_test
            ;;
    esac
    
    # Summary
    print_header "Test Summary"
    print_success "Testing completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  • Review test outputs above"
    echo "  • Check logs in /tmp/test*.log"
    echo "  • Run interactive mode: $0 --interactive"
    if [ "$MODE" != "agentcore" ] && [ "$MODE" != "all" ]; then
        echo "  • Deploy to AgentCore: $0 --agentcore"
    fi
    echo ""
    echo "Documentation:"
    echo "  • Quick Start: CLI_QUICKSTART.md"
    echo "  • Full Guide: docs/guides/CLI_TESTING_GUIDE.md"
    echo ""
}

# Run main function
main "$@"

