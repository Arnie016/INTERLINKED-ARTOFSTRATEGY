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

## 🔄 Data Flow

1. **Data Ingestion** → Upload company text/CSV to **S3**
2. **Extraction** → Extractor Agent parses text → structured triples
3. **Graph Loading** → Triples loaded into **Neptune**
4. **Analysis** → Analyzer Agent queries Neptune for patterns
5. **Strategy** → Strategizer Agent generates recommendations
6. **Visualization** → Frontend displays chat insights + graph updates

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM Reasoning** | Amazon Bedrock (Claude 3, Nova) |
| **Agent Framework** | Amazon Bedrock AgentCore |
| **Graph Database** | Amazon Neptune (openCypher) |
| **Fine-tuning** | Amazon SageMaker Training Jobs |
| **Inference** | SageMaker Real-time Endpoints |
| **Data Storage** | Amazon S3 |
| **Frontend** | React, Next.js, Flourish, D3.js |
| **Hosting** | AWS Amplify |
| **APIs** | FastAPI/Lambda + API Gateway |

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

## 🧠 Why Neptune?

**Without Neptune, agents can't reason over structure.**

LLMs like Bedrock are excellent at text processing but don't inherently understand entity relationships. Neptune provides:

✅ **Source of Truth** - Persistent storage of all organizational entities  
✅ **Queryable Memory** - Efficient pattern matching (centrality, dependencies)  
✅ **Context Store** - Structured data for AI reasoning  

**Result:** Real reasoning, not just text summarization.

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

