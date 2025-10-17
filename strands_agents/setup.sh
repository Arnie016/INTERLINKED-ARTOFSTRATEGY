#!/bin/bash

# Strands Agents Project Setup Script
# This script initializes the development environment

set -e  # Exit on error

echo "========================================="
echo "Interlinked - Strands Agents Setup"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
    echo -e "${RED}Error: Python 3.11+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK: $PYTHON_VERSION${NC}"
echo ""

# Check AWS CLI
echo "Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi
AWS_VERSION=$(aws --version 2>&1 | awk '{print $1}')
echo -e "${GREEN}✓ AWS CLI installed: $AWS_VERSION${NC}"
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}Warning: AWS credentials not configured or invalid${NC}"
    echo "Run 'aws configure' to set up credentials"
    echo "See docs/AWS_CREDENTIALS_SETUP.md for details"
else
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    echo -e "${GREEN}✓ AWS credentials configured (Account: $AWS_ACCOUNT)${NC}"
fi
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Create .env file if it doesn't exist
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo -e "${YELLOW}  Please edit .env with your configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi
echo ""

# Verify Bedrock access
echo "Verifying AWS Bedrock access..."
if aws bedrock list-foundation-models --region us-west-2 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ AWS Bedrock access confirmed${NC}"
else
    echo -e "${YELLOW}Warning: Unable to verify Bedrock access${NC}"
    echo "  Make sure you have proper IAM permissions"
    echo "  See docs/AWS_CREDENTIALS_SETUP.md for required permissions"
fi
echo ""

# Create logs directory
echo "Creating directories..."
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Success message
echo "========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Review docs/AWS_CREDENTIALS_SETUP.md for AWS setup"
echo "4. Start development!"
echo ""
echo "Useful commands:"
echo "  - Run tests: pytest tests/ -v"
echo "  - Start dev server: uvicorn src.api.main:app --reload"
echo ""
