#!/bin/bash
# Setup script for FastAPI proxy test environment

set -e  # Exit on error

echo "==================================================================="
echo "FastAPI Proxy Test Environment Setup"
echo "==================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "api" ]; then
    echo -e "${RED}Error: Must run from backend/ directory${NC}"
    exit 1
fi

cd api

echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov -q

echo ""
echo "📦 Installing proxy dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    echo -e "${YELLOW}Warning: requirements.txt not found${NC}"
fi

echo ""
echo "🔧 Setting up environment variables..."

# Export test environment variables
export PROXY_SESSION_BACKEND=file
export PROXY_USE_AGENTCORE_MEMORY=false
export PROXY_ENABLE_ERROR_DETAILS=true
export AWS_REGION=us-west-2

# Neo4j (use existing or defaults)
export NEO4J_URI=${NEO4J_URI:-bolt://localhost:7687}
export NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}

# Anthropic API key (use existing or test value)
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-test-key}

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Create test session directory
mkdir -p .test_sessions
echo -e "${GREEN}✓ Test session directory created${NC}"
echo ""

echo "==================================================================="
echo "Environment Setup Complete!"
echo "==================================================================="
echo ""
echo "Environment Variables:"
echo "  PROXY_SESSION_BACKEND=$PROXY_SESSION_BACKEND"
echo "  PROXY_USE_AGENTCORE_MEMORY=$PROXY_USE_AGENTCORE_MEMORY"
echo "  AWS_REGION=$AWS_REGION"
echo "  NEO4J_URI=$NEO4J_URI"
echo ""
echo "To run tests:"
echo "  ${GREEN}pytest tests/ -v${NC}                 # All tests"
echo "  ${GREEN}pytest tests/ -v -m unit${NC}         # Unit tests only"
echo "  ${GREEN}pytest tests/ -v -m integration${NC}  # Integration tests only"
echo "  ${GREEN}pytest tests/ --cov=proxy${NC}        # With coverage"
echo ""
echo "For more testing options, see: TESTING_GUIDE.md"
echo "==================================================================="
