# 🔧 Backend - Agent Tool Architecture

Python FastAPI backend with AI agents and Neo4j graph database integration.

## 🚀 Quick Start

### **Option 1: Using npm scripts (Recommended)**
```bash
# From the backend directory
npm run dev
```

### **Option 2: Direct Python execution**
```bash
# From the backend/api directory
cd api
source venv/bin/activate
python main.py
```

### **Option 3: Using the startup script**
```bash
# From the project root
./start-dev.sh
```

## 📋 Available Scripts

- `npm run dev` - Start development server
- `npm run start` - Start production server
- `npm run install-deps` - Install Python dependencies
- `npm run test` - Run tests

## 🔧 Manual Setup

### **1. Install Dependencies**
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **2. Environment Variables**
Create a `.env` file in the `backend/` directory:
```bash
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
AWS_REGION=us-east-1
```

### **3. Start the Server**
```bash
python main.py
```

## 🌐 API Endpoints

- **Health Check**: `GET /api/health`
- **List Agents**: `GET /api/agents`
- **Chat with Agent**: `POST /api/chat`
- **Get Graph Data**: `GET /api/graph`
- **Execute Cypher**: `GET /api/graph/cypher?query=...`

## 📚 API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## 🏗️ Architecture

- **FastAPI**: Web framework
- **Agent Orchestrator**: Manages AI agents
- **Neo4j**: Graph database
- **Bedrock AI**: AWS AI services
- **Pydantic**: Data validation

## 🐛 Troubleshooting

### **Backend won't start**
- Check if Python virtual environment is activated
- Verify all dependencies are installed
- Check environment variables are set

### **Neo4j connection issues**
- Verify Neo4j is running
- Check connection credentials
- Ensure network connectivity

### **Agent errors**
- Check AWS credentials for Bedrock
- Verify model IDs are correct
- Check tool implementations
