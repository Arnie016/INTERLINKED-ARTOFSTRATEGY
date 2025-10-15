# 🧠 OrgMind AI - Intelligent Organizational Strategy Platform

> **AI-powered operations consultant that visualizes your organization as a knowledge graph and delivers actionable strategic insights.**

[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20Neptune%20%7C%20SageMaker-orange)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Use Cases](#use-cases)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## 🎯 Overview

**OrgMind AI** transforms unstructured organizational data (text, org charts, CSVs) into a **knowledge graph** that AI agents can reason over to detect inefficiencies, bottlenecks, and opportunities for automation.

### Key Features

- 🔍 **Automated Entity Extraction** - Converts raw text into structured relationships
- 📊 **Knowledge Graph Storage** - Maintains persistent organizational memory in Neptune
- 🧠 **Intelligent Analysis** - Detects bottlenecks, gaps, and inefficiencies using AI reasoning
- 💡 **Strategic Recommendations** - Generates actionable business improvement strategies
- 🎨 **Visual Interface** - Interactive chat + graph visualization
- 🎲 **Mock Data Generation** - Generate realistic organizational data (10-1000 employees) for testing and demos

---

## 🏗️ Architecture

```
┌─────────────┐
│  User Input │ (Text/CSV/Org Charts)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              📁 Amazon S3 (Data Lake)               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   1️⃣ EXTRACTOR AGENT (Amazon Bedrock - Claude 3)   │
│   • Entity & Relation Extraction                    │
│   • Outputs: JSON triples (person, process, edge)   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│      🗄️ AMAZON NEPTUNE (Graph Database)            │
│   • Stores nodes (people, processes)                │
│   • Stores edges (owns, depends_on, performs)       │
│   • Supports openCypher/SPARQL queries              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   2️⃣ ANALYZER AGENT (Bedrock AgentCore)            │
│   • Queries Neptune graph                           │
│   • Detects inefficiencies & bottlenecks            │
│   • Outputs: Structured insights (JSON + NL)        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   3️⃣ STRATEGIZER AGENT (SageMaker Endpoint)        │
│   • Fine-tuned model for business strategy          │
│   • Converts insights → actionable recommendations  │
│   • Outputs: Strategic improvement plans            │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│   4️⃣ FRONTEND (React/Next.js + AWS Amplify)        │
│   • Chat interface for queries                      │
│   • Flourish/D3.js graph visualization              │
│   • Real-time insight display                       │
└─────────────────────────────────────────────────────┘
```

---

## 🧩 System Components

### Agent Roles at a Glance

| Agent | Primary Job | Input | Output | Analogy |
|-------|------------|-------|--------|---------|
| **Extractor** | Convert text → graph | Raw text, CSV | JSON triples | 📝 Data entry clerk who organizes information |
| **Analyzer** | Find problems in graph | Neptune graph data | List of inefficiencies | 🔍 Detective who finds patterns and issues |
| **Strategizer** | Create action plans | Problem descriptions | Strategic recommendations | 💡 Business consultant who suggests solutions |

---

### 1️⃣ **Extractor Agent** (Amazon Bedrock)

**Purpose:** Converts unstructured text into structured knowledge graph entities.

- **Input:** Raw text, CSV files from S3
- **Processing:** Entity + relation extraction using Claude 3 / Nova LLM
- **Output:** JSON triples like:
  ```json
  {
    "person": "Alice",
    "process": "Review Reports",
    "relation": "performs"
  }
  ```
- **Value:** Creates the knowledge graph foundation for downstream reasoning

---

### 🗄️ **Neptune Graph Database**

**Purpose:** Persistent storage for organizational relationships.

- **Input:** JSON/CSV triples from Extractor
- **Storage:** 
  - **Nodes:** People, processes, departments
  - **Edges:** `owns`, `depends_on`, `performs`, `approves`
- **Query Languages:** openCypher, SPARQL
- **Value:** Provides queryable structure so AI can reason about real dependencies instead of raw text

---

### 2️⃣ **Analyzer Agent** (Bedrock AgentCore)

**Purpose:** Identifies inefficiencies and organizational bottlenecks.

- **Input:** Graph data from Neptune SDK/API
- **Reasoning Tasks:**
  - Find people overloaded with >3 tasks
  - Detect unassigned processes
  - Identify circular dependencies
  - Spot redundant approval chains
- **Output:** List of inefficiencies (JSON + natural language)
- **Value:** The logic engine that converts graph relationships into actionable insights

---

### 3️⃣ **Strategizer Agent** (SageMaker Endpoint)

**Purpose:** Generates strategic business recommendations.

- **Input:** Inefficiency descriptions from Analyzer
- **Model:** Fine-tuned instruction model (RLHF/DPO training)
- **Training Data:** Examples of organizational improvements and automation tactics
- **Output:** Strategic recommendations like:
  - "Automate low-value approvals via Slackbot"
  - "Restructure Finance approval chain to reduce 3-day delay"
- **Value:** Turns diagnosis into strategy with domain-specific business intelligence

---

### 4️⃣ **Frontend** (React/Next.js)

**Purpose:** User interface for interaction and visualization.

- **Input:** User queries ("Show inefficiencies in HR")
- **Features:**
  - **Left Panel:** Chat interface with Bedrock AgentCore
  - **Right Panel:** Interactive Flourish graph with:
    - Red nodes = bottlenecks
    - Green nodes = optimized processes
    - Edge thickness = dependency strength
- **Hosting:** AWS Amplify
- **Value:** Makes complex insights accessible through conversation and visual exploration

---

## 🔄 Data Flow & Reasoning Pipeline

### High-Level Flow

1. **Data Ingestion** → Upload company text/CSV to **S3**
2. **Extraction** → Extractor Agent parses text → structured triples
3. **Graph Loading** → Triples loaded into **Neptune**
4. **Analysis** → Analyzer Agent queries Neptune for patterns
5. **Strategy** → Strategizer Agent generates recommendations
6. **Visualization** → Frontend displays chat insights + graph updates

### 🧠 The Reasoning Loop (What Makes This Intelligent)

```
Neptune Graph (Source of Truth)
         ↓
Analyzer queries: "Find bottlenecks"
         ↓
Structured results: [Process X, Person Y]
         ↓
Bedrock LLM interprets: "X blocks 3 processes, Y is overloaded"
         ↓
Impact scoring: High priority (0.87)
         ↓
Strategizer generates: "Automate X, reassign Y's tasks"
         ↓
Frontend shows: Red nodes on graph + chat recommendations
```

**Key Innovation:** AI doesn't just read text — it **queries the organizational structure** and **reasons over relationships**.

---

## 🛠️ Tech Stack

| Layer | Technology | SDK/Package |
|-------|-----------|-------------|
| **LLM Reasoning** | Amazon Bedrock (Claude 3, Nova) | `anthropic`, `boto3`, `langchain-aws` |
| **Agent Framework** | Amazon Bedrock AgentCore | `boto3-stubs[bedrock-runtime]` |
| **Graph Database** | Amazon Neptune (openCypher) | `gremlinpython`, `rdflib`, `SPARQLWrapper` |
| **Graph Analytics** | NetworkX | `networkx`, `py2neo` |
| **Fine-tuning** | Amazon SageMaker Training Jobs | `sagemaker>=2.200.0` |
| **Inference** | SageMaker Real-time Endpoints | `boto3.client('sagemaker-runtime')` |
| **Data Storage** | Amazon S3 | `boto3-stubs[s3]`, `s3fs` |
| **Frontend** | React, Next.js, D3.js | `@aws-sdk/client-*`, `react-force-graph` |
| **Hosting** | AWS Amplify | `aws-amplify`, `@aws-amplify/ui-react` |
| **APIs** | FastAPI + Uvicorn | `fastapi>=0.109.0`, `uvicorn[standard]` |

📦 **[Complete SDK Mapping](./SDK_MAPPING.md)** - Detailed breakdown of all dependencies and usage examples

---

## 🚀 Getting Started

### Prerequisites

- AWS Account with Bedrock, Neptune, and SageMaker access
- Python 3.9+
- Node.js 18+
- AWS CLI configured

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/INTERLINKED-ARTOFSTRATEGY.git
cd INTERLINKED-ARTOFSTRATEGY

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### Configuration

1. **Set up AWS credentials:**
   ```bash
   aws configure
   ```

2. **Create `.env` file:**
   ```bash
   AWS_REGION=us-east-1
   NEPTUNE_ENDPOINT=your-neptune-endpoint
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   SAGEMAKER_ENDPOINT=your-strategizer-endpoint
   ```

3. **Initialize Neptune graph schema:**
   ```bash
   python scripts/init_neptune_schema.py
   ```

### Running the Application

```bash
# Start backend
python app.py

# Start frontend (in separate terminal)
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access the UI.

---

## 💼 Use Cases

### 1. **Organizational Audit**
- Upload org chart → Detect reporting inefficiencies
- Find departments with unclear ownership

### 2. **Process Optimization**
- Identify approval bottlenecks
- Suggest automation opportunities

### 3. **Resource Allocation**
- Find overloaded team members
- Rebalance workload distribution

### 4. **Compliance & Risk**
- Detect missing process owners
- Identify single points of failure

---

## 🗺️ Roadmap

- [ ] Multi-tenant support
- [ ] Real-time collaboration features
- [ ] Integration with Slack/Teams
- [ ] Automated report generation
- [ ] Custom fine-tuning UI
- [ ] Enterprise SSO support

---

## 🧠 How Graph Reasoning Works (The Core Innovation)

### Why Neptune + Bedrock Together?

**Traditional AI Problem:** LLMs can read text but can't inherently understand *structural relationships* between entities.

**Our Solution:** Combine Neptune's graph database with Bedrock's reasoning to enable AI agents that think through organizational structure, not just text.

---

### 🧩 Step-by-Step: Graph Reasoning in Action

| Stage | What Happens | Tools Used | Example |
|-------|-------------|------------|---------|
| **1️⃣ Graph Storage** | Company data stored as nodes (people/processes) and edges (relationships) | **Amazon Neptune** | `(Alice)-[:PERFORMS]->(Review Reports)`<br>`(Review Reports)-[:DEPENDS_ON]->(Finance Approval)` |
| **2️⃣ Query Formulation** | Analyzer formulates structured graph queries | **Bedrock AgentCore + Neptune SDK** | "Find processes that have no assigned person" |
| **3️⃣ Structured Results** | Neptune returns matching nodes/edges | **Neptune Query Engine** | `["Finance Approval", "QA Testing"]` |
| **4️⃣ LLM Reasoning** | Bedrock interprets results and infers inefficiencies | **Bedrock (Claude 3/Nova)** | "Finance Approval has no owner, causing delays in 3 downstream processes" |
| **5️⃣ Scoring** | Agent ranks issues by impact and priority | **Bedrock reasoning + Graph metrics** | "High priority: affects 3 downstream processes" |
| **6️⃣ Strategy Output** | Insights sent to Strategizer for recommendations | **JSON via Lambda/FastAPI** | `{"inefficiency": "unassigned", "impact_score": 0.87}` |

---

### 📊 Concrete Example: Finding Bottlenecks

**Scenario:** Your organization has this structure:

```
Alice → Review Reports → Finance Approval → Send Invoice
Bob   → Approve Budget → Finance Approval
```

#### Query 1: Find Unassigned Processes

```cypher
MATCH (p:Process)
WHERE NOT (p)<-[:PERFORMS]-(:Person)
RETURN p.name;
```

**Neptune Returns:** `["Finance Approval"]`

**Analyzer LLM Reasoning:**
> "Finance Approval is unassigned but is depended on by 2 upstream processes (Review Reports, Approve Budget). This creates a critical bottleneck affecting invoice delivery."

---

#### Query 2: Find Overloaded Team Members

```cypher
MATCH (p:Person)-[:PERFORMS]->(t:Process)
WITH p, count(t) AS taskCount
WHERE taskCount > 3
RETURN p.name, taskCount
ORDER BY taskCount DESC;
```

**Neptune Returns:** 
```json
[
  {"name": "Alice", "taskCount": 4},
  {"name": "Bob", "taskCount": 2}
]
```

**Analyzer LLM Reasoning:**
> "Alice manages 4 processes, exceeding optimal workload capacity. Risk of burnout and delays. Consider task redistribution."

---

#### Query 3: Detect Circular Dependencies

```cypher
MATCH path = (d1:Department)-[:DEPENDS_ON*]->(d1)
RETURN path;
```

**Neptune Returns:** `Finance → HR → Legal → Finance`

**Analyzer LLM Reasoning:**
> "Circular dependency detected in approval chain. Finance waits on HR, HR on Legal, Legal on Finance. This creates an unresolvable deadlock."

---

### 🎯 Output to Strategizer

The Analyzer packages insights:

```json
{
  "inefficiencies": [
    {
      "type": "unassigned_process",
      "entity": "Finance Approval",
      "impact_score": 0.87,
      "affected_processes": 3,
      "recommendation_needed": true
    },
    {
      "type": "overload",
      "entity": "Alice",
      "task_count": 4,
      "impact_score": 0.72,
      "recommendation_needed": true
    }
  ]
}
```

**Strategizer Agent Response** (from fine-tuned SageMaker model):

```json
{
  "recommendations": [
    {
      "issue": "Finance Approval unassigned",
      "action": "Assign to Finance Ops Lead (Sarah)",
      "implementation": "Update RACI matrix, set up approval Slackbot for <$5K requests",
      "expected_impact": "Reduce approval time by 60%",
      "priority": "high"
    },
    {
      "issue": "Alice overloaded",
      "action": "Automate report compilation",
      "implementation": "Deploy Python script to auto-generate weekly reports",
      "expected_impact": "Free up 8 hours/week",
      "priority": "medium"
    }
  ]
}
```

---

### 🔄 How Bedrock AgentCore Enables This

AgentCore allows the Analyzer to use **reasoning tools** modularly:

```python
# Analyzer Agent Configuration
agent_tools = [
    {
        "name": "query_neptune",
        "description": "Execute graph queries to find patterns",
        "handler": lambda query: neptune_client.execute(query)
    },
    {
        "name": "compute_centrality",
        "description": "Calculate node importance metrics",
        "handler": graph_analytics.betweenness_centrality
    },
    {
        "name": "rank_inefficiencies",
        "description": "Score issues by business impact",
        "handler": impact_scorer.calculate
    }
]

# Agent Reasoning Flow
if query_result := agent.query_neptune("find_unassigned"):
    impact = agent.compute_centrality(query_result)
    ranked = agent.rank_inefficiencies(impact)
    return agent.generate_insights(ranked)
```

Each step is **transparent and traceable** — you can see exactly which queries were run and how the AI reasoned through the results.

---

### ⚡ Why This Approach Is Powerful

| Traditional AI Approach | Graph Reasoning (OrgMind AI) |
|------------------------|------------------------------|
| 📝 Reads text, guesses relationships | 🎯 **Knows exact dependencies** from graph structure |
| ❓ Hard to trace reasoning logic | ✅ **Transparent queries** + explicit reasoning steps |
| 🌐 Generic responses | 🔍 **Targeted insights** tied to org structure |
| 🔄 No persistent context | 💾 **Graph acts as memory** across sessions |
| 📊 One-shot answers | 🔄 **Continuous reasoning** over evolving org graph |

**Key Insight:** You're giving AI a *map of the organization*, not just words — enabling logical reasoning through structure.

---

### 🧮 Real-World Impact

**Before OrgMind AI:**
- "I think Finance might be a bottleneck, but I'm not sure..."
- Manual org chart analysis takes weeks
- Inefficiencies hidden in silos

**After OrgMind AI:**
- "Finance Approval is unassigned and blocks 3 critical processes"
- Automated analysis in minutes
- AI suggests specific, actionable fixes

The graph enables **precision** where traditional AI only offers **probability**.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Amazon Web Services for Bedrock, Neptune, and SageMaker infrastructure
- Anthropic Claude for advanced reasoning capabilities
- The open-source community for invaluable tools and libraries

---

## 📧 Contact

**Project Maintainer:** [Your Name]  
**Email:** your.email@example.com  
**Project Link:** [https://github.com/yourusername/INTERLINKED-ARTOFSTRATEGY](https://github.com/yourusername/INTERLINKED-ARTOFSTRATEGY)

---

<div align="center">
  <strong>Built with ❤️ using AWS AI Services</strong>
</div>

