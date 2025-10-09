# 🏗️ OrgMind AI - Detailed Architecture

## System Architecture Overview

This document provides an in-depth technical explanation of the OrgMind AI architecture, component interactions, and data flows.

---

## 📊 Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  ┌────────────────┐              ┌─────────────────────────┐    │
│  │  Chat Interface│              │  Graph Visualization    │    │
│  │  (React/Next)  │◄────────────►│  (Flourish/D3.js)      │    │
│  └────────┬───────┘              └──────────┬──────────────┘    │
│           │                                  │                    │
└───────────┼──────────────────────────────────┼────────────────────┘
            │                                  │
            ▼                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / BACKEND                       │
│                     (FastAPI / AWS Lambda)                       │
└───────────┬──────────────────────────────────┬───────────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────┐      ┌──────────────────────────────┐
│   Amazon Bedrock        │      │   Amazon Neptune             │
│   Agent Runtime         │◄────►│   Graph Database             │
│                         │      │                              │
│  ┌──────────────────┐   │      │  Nodes:                      │
│  │ Extractor Agent  │   │      │  • People                    │
│  │ (Entity Extract) │   │      │  • Processes                 │
│  └──────────────────┘   │      │  • Departments               │
│                         │      │                              │
│  ┌──────────────────┐   │      │  Edges:                      │
│  │ Analyzer Agent   │───┼─────►│  • performs                  │
│  │ (Find Issues)    │   │      │  • owns                      │
│  └──────────────────┘   │      │  • depends_on                │
└─────────┬───────────────┘      │  • approves                  │
          │                      └──────────────────────────────┘
          ▼
┌─────────────────────────┐
│   Amazon SageMaker      │
│   Inference Endpoint    │
│                         │
│  ┌──────────────────┐   │
│  │ Strategizer      │   │
│  │ (Fine-tuned LLM) │   │
│  └──────────────────┘   │
└─────────────────────────┘
          │
          ▼
    Recommendations
```

---

## 🔄 Detailed Data Flow

### Phase 1: Data Ingestion & Extraction

```
User Upload (CSV/Text)
         │
         ▼
    Amazon S3
    (Raw Data)
         │
         ▼
  Extractor Agent
  (Bedrock Claude 3)
         │
         ├─► Entity Recognition
         ├─► Relation Extraction
         └─► Triple Generation
         │
         ▼
    JSON Triples
    {
      "subject": "Alice",
      "predicate": "performs",
      "object": "Review Reports"
    }
```

### Phase 2: Knowledge Graph Construction

```
    JSON Triples
         │
         ▼
  Neptune Loader
  (Gremlin/SPARQL)
         │
         ├─► Create Vertices (Nodes)
         ├─► Create Edges (Relationships)
         └─► Index Properties
         │
         ▼
    Neptune Graph
    
    Example Graph:
    
    (Alice:Person)──[performs]──>(Review Reports:Process)
          │
          └──[reports_to]──>(Bob:Person)
          
    (Finance:Dept)──[owns]──>(Budget Approval:Process)
          │
          └──[depends_on]──>(HR:Dept)
```

### Phase 3: Analysis & Reasoning

```
User Query: "Find bottlenecks in Finance"
         │
         ▼
  Analyzer Agent
  (Bedrock AgentCore)
         │
         ├─► Query Neptune Graph
         │   SELECT * FROM vertices
         │   WHERE dept = 'Finance'
         │   AND degree > 5
         │
         ├─► Pattern Detection
         │   • High centrality nodes
         │   • Circular dependencies
         │   • Unassigned processes
         │
         └─► Generate Insights
         │
         ▼
    Inefficiency Report
    [
      {
        "type": "bottleneck",
        "entity": "Budget Approval",
        "severity": "high",
        "impact": "3-day delay",
        "affected_processes": [...]
      }
    ]
```

### Phase 4: Strategic Recommendation

```
  Inefficiency Report
         │
         ▼
  Strategizer Agent
  (SageMaker Endpoint)
         │
         ├─► Load Fine-tuned Model
         ├─► Apply Business Logic
         ├─► Generate Strategies
         │
         ▼
    Strategic Plan
    {
      "recommendation": "Automate Budget Approval",
      "implementation": "Deploy Slackbot for <$5K approvals",
      "expected_impact": "Reduce approval time by 60%",
      "priority": "high",
      "effort": "medium"
    }
```

### Phase 5: Visualization

```
    Strategic Plan
         │
         ▼
    Frontend API
         │
         ├─► Update Chat UI
         │   (Display recommendations)
         │
         └─► Update Graph Visualization
             │
             ├─► Highlight Bottlenecks (Red)
             ├─► Show Optimizations (Green)
             └─► Animate Data Flow
```

---

## 🧩 Component Deep Dive

### 1. Extractor Agent (Bedrock)

**Technology:** Amazon Bedrock with Claude 3 Sonnet/Opus

**Input Schema:**
```json
{
  "text": "Alice manages the Review Reports process and reports to Bob.",
  "extraction_type": "entity_relation",
  "schema": {
    "entities": ["Person", "Process", "Department"],
    "relations": ["manages", "reports_to", "owns", "depends_on"]
  }
}
```

**Processing Logic:**
1. **Named Entity Recognition (NER)**
   - Identify people, processes, departments
   - Extract attributes (role, department, email)

2. **Relation Extraction**
   - Parse dependencies between entities
   - Classify relationship types

3. **Triple Generation**
   - Convert text to (subject, predicate, object) triples
   - Validate schema compliance

**Output:**
```json
{
  "entities": [
    {"id": "e1", "type": "Person", "name": "Alice", "role": "Manager"},
    {"id": "e2", "type": "Person", "name": "Bob", "role": "Director"},
    {"id": "e3", "type": "Process", "name": "Review Reports"}
  ],
  "relations": [
    {"subject": "e1", "predicate": "manages", "object": "e3"},
    {"subject": "e1", "predicate": "reports_to", "object": "e2"}
  ]
}
```

---

### 2. Neptune Graph Database

**Graph Schema:**

```cypher
// Node Types
CREATE CONSTRAINT ON (p:Person) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT ON (pr:Process) ASSERT pr.id IS UNIQUE;
CREATE CONSTRAINT ON (d:Department) ASSERT d.id IS UNIQUE;

// Relationship Types
(:Person)-[:performs]->(:Process)
(:Person)-[:reports_to]->(:Person)
(:Person)-[:works_in]->(:Department)
(:Process)-[:owned_by]->(:Department)
(:Process)-[:depends_on]->(:Process)
(:Department)-[:depends_on]->(:Department)
```

**Query Examples:**

```cypher
// Find overloaded people (>3 processes)
MATCH (p:Person)-[:performs]->(pr:Process)
WITH p, count(pr) as process_count
WHERE process_count > 3
RETURN p.name, process_count
ORDER BY process_count DESC;

// Find processes with no owner
MATCH (pr:Process)
WHERE NOT (pr)<-[:owns]-()
RETURN pr.name;

// Find circular dependencies
MATCH path = (d1:Department)-[:depends_on*]->(d1)
RETURN path;
```

---

### 3. Analyzer Agent (Bedrock AgentCore)

**Reasoning Templates:**

```python
ANALYSIS_PROMPTS = {
    "bottleneck_detection": """
    Query the graph for nodes with:
    - High in-degree (many dependencies)
    - High betweenness centrality
    - Single point of failure patterns
    
    Return structured analysis.
    """,
    
    "efficiency_gaps": """
    Identify:
    - Processes with no assigned owner
    - Duplicate approval chains
    - Unnecessary dependencies
    """,
    
    "workload_balance": """
    Analyze person nodes for:
    - Uneven task distribution
    - Skill-task mismatch
    - Capacity constraints
    """
}
```

**Agent Configuration:**
```python
{
    "agent_name": "OrgAnalyzer",
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "instruction": "You are an organizational efficiency expert...",
    "tools": [
        {
            "name": "query_neptune",
            "description": "Execute Cypher queries on the org graph",
            "schema": {...}
        },
        {
            "name": "calculate_metrics",
            "description": "Compute graph centrality metrics",
            "schema": {...}
        }
    ]
}
```

---

### 4. Strategizer Agent (SageMaker)

**Fine-tuning Dataset Format:**

```jsonl
{"prompt": "Bottleneck detected: Budget Approval process has 5-day delay with 15 dependent processes.", "completion": "Recommendation: Implement tiered approval system. For <$5K: auto-approve. $5K-$50K: manager approval via Slack. >$50K: committee review. Expected impact: 70% reduction in approval time."}

{"prompt": "Gap identified: Marketing campaign process has no assigned owner and 3 stakeholders.", "completion": "Recommendation: Assign single DRI (Directly Responsible Individual) from Marketing. Create RACI matrix. Set up weekly sync. Risk: Without clear ownership, campaigns will continue to miss deadlines."}
```

**Model Architecture:**
- Base Model: LLaMA 3 70B or Mistral 7B
- Fine-tuning: LoRA + RLHF
- Training: SageMaker Training Jobs
- Deployment: SageMaker Real-time Endpoint

**Inference API:**
```python
import boto3

runtime = boto3.client('sagemaker-runtime')

response = runtime.invoke_endpoint(
    EndpointName='strategizer-endpoint',
    ContentType='application/json',
    Body=json.dumps({
        "inputs": "Bottleneck: Finance approval delays",
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9
        }
    })
)

recommendation = json.loads(response['Body'].read())
```

---

## 🔐 Security Architecture

### Authentication & Authorization
- AWS IAM roles for service-to-service communication
- JWT tokens for frontend-backend auth
- Row-level security in Neptune (future)

### Data Protection
- Encryption at rest (S3, Neptune, SageMaker)
- Encryption in transit (TLS 1.3)
- PII masking in logs

### Network Security
- VPC isolation for Neptune
- Security groups for service communication
- API Gateway throttling and WAF

---

## 📈 Scalability Considerations

### Horizontal Scaling
- **Bedrock:** Auto-scales with request volume
- **Neptune:** Read replicas for query distribution
- **SageMaker:** Multi-model endpoints or auto-scaling
- **Frontend:** AWS Amplify CDN + edge locations

### Performance Optimization
- **Graph Queries:** Index frequently queried properties
- **Caching:** Redis for frequently accessed insights
- **Async Processing:** SQS + Lambda for batch extraction

---

## 🛠️ Technology Justification

| Component | Technology | Why This Choice |
|-----------|-----------|----------------|
| **LLM** | Amazon Bedrock | Managed service, no infrastructure, multiple models, built-in guardrails |
| **Graph DB** | Amazon Neptune | Serverless, ACID compliance, supports Cypher and SPARQL, integrates with AWS |
| **Fine-tuning** | SageMaker | Custom model hosting, version control, A/B testing, monitoring |
| **Frontend** | React/Next.js | Fast, modern, great ecosystem, AWS Amplify support |
| **Visualization** | Flourish + D3.js | Interactive graphs, easy embedding, real-time updates |

---

## 🔮 Future Enhancements

1. **Real-time Updates:** WebSocket integration for live graph changes
2. **Multi-tenancy:** Separate graphs per organization
3. **Advanced Analytics:** Predictive modeling for future bottlenecks
4. **Integration Hub:** Slack, Teams, Jira, Asana connectors
5. **Automated Actions:** Auto-create tickets, send notifications
6. **Version Control:** Track organizational changes over time

---

## 📚 References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Neptune Guide](https://docs.aws.amazon.com/neptune/)
- [SageMaker Inference](https://docs.aws.amazon.com/sagemaker/)
- [OpenCypher Query Language](https://opencypher.org/)
- [Graph Theory for Analysis](https://en.wikipedia.org/wiki/Graph_theory)

