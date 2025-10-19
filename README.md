# 🧠 Graph Database Agent POC

> **Proof of Concept: AI agents manipulating graph databases using Neo4j and conversational interfaces**

[![Neo4j](https://img.shields.io/badge/Neo4j-Graph%20Database-green)](https://neo4j.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Overview

This is a **proof of concept** demonstrating how AI agents can interact with and manipulate graph databases through natural language conversations. The system uses Neo4j as the graph database backend and provides a conversational interface for querying and modifying graph data.

## 🏗️ Architecture

```
User Input (Natural Language) → Chat Interface (chat.py) → AI Agent → Neo4j Database → Response
```

## 🧩 Key Files

### 💬 **`chat.py`** - Main Entry Point
The most important file in the project. Handles natural language input and coordinates with AI agents to process graph database queries.

### 🗄️ **Neo4j Connection** (`strands_agents/src/config/neo4j_config.py`)
Manages the graph database connection, query execution, and error handling.

### 🤖 **Neo4j Agent** (`strands_agents/src/agents/neo4j_agent.py`)
Translates natural language queries into Cypher graph queries and executes them.

### 🎨 **Frontend** (`frontend/`)
React/Next.js interface for graph visualization and chat interaction.

## 🔄 How It Works

1. **User Input** → Natural language query via chat interface
2. **AI Processing** → Agent translates query to Cypher graph queries  
3. **Database Query** → Neo4j executes the query and returns results
4. **Response** → Results are formatted and displayed to user

### Example
```
User: "Show me all people who work in Engineering"
↓
Agent: MATCH (p:Person)-[:WORKS_IN]->(d:Department {name: 'Engineering'}) RETURN p
↓
Response: "Here are the people in Engineering: Alice, Bob, Charlie"
```

## 🛠️ Tech Stack

- **Graph Database:** Neo4j
- **AI Agents:** Python + LLM APIs
- **Backend:** Python
- **Frontend:** React/Next.js
- **Visualization:** D3.js/Cytoscape

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Neo4j database (local or cloud)

### Installation
```bash
git clone https://github.com/ElSancturioDeThomas/POC_Graph_Agents.git
cd POC_Graph_Agents

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install
```

### Configuration
1. Set up Neo4j connection in `strands_agents/src/config/neo4j_config.py`
2. Configure environment variables for your Neo4j instance

### Running
```bash
# Start chat interface
python chat.py

# Start frontend (separate terminal)
cd frontend && npm run dev
```

## 💡 POC Features

- ✅ Natural Language to Graph Queries
- ✅ Interactive Graph Visualization  
- ✅ Real-time Chat Interface
- ✅ Flexible Graph Operations (CRUD)

## 🎯 What This Demonstrates

This POC shows how AI agents can:
- Understand natural language and convert it to database queries
- Interact with graph databases through conversation
- Visualize complex relationships intuitively
- Bridge human language and technical database operations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">
  <strong>🧠 Graph Database Agent Proof of Concept</strong>
</div>