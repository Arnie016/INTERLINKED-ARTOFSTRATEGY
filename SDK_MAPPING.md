# 📦 SDK & Dependency Mapping

Complete mapping of all SDKs, libraries, and dependencies to system components.

---

## 🐍 Backend (Python) SDK Mapping

### AWS Core Services

| SDK Package | Version | Used By | Purpose |
|------------|---------|---------|---------|
| `boto3` | >=1.34.0 | All AWS components | Main AWS SDK - handles S3, Lambda, IAM, CloudWatch |
| `botocore` | >=1.34.0 | All AWS components | Low-level AWS client library (boto3 dependency) |
| `aioboto3` | >=12.3.0 | API Backend | Async AWS operations for high-performance concurrent requests |

**Usage Example:**
```python
import boto3

# S3 client for data upload
s3_client = boto3.client('s3', region_name='us-east-1')
s3_client.upload_file('org_data.csv', 'orgmind-bucket', 'data/org_data.csv')
```

---

### Amazon Bedrock (LLM & Agents)

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `anthropic` | >=0.18.0 | Extractor Agent, Analyzer Agent | Direct Claude 3/Opus API client |
| `boto3-stubs[bedrock-runtime]` | >=1.34.0 | All Bedrock components | Type hints for IDE autocomplete & type checking |
| `langchain` | >=0.1.0 | Agent orchestration | LLM chains, prompt templates, agent loops |
| `langchain-aws` | >=0.1.0 | Bedrock integration | AWS-specific LangChain connectors |

**Usage Example:**
```python
import anthropic
from langchain_aws import BedrockLLM

# Direct Anthropic client
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Extract entities from this text..."}]
)

# LangChain wrapper for Bedrock
llm = BedrockLLM(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-east-1"
)
```

**Why Both?**
- `anthropic`: Direct API access, more control, streaming support
- `langchain`: Agent orchestration, tool use, memory management

---

### Amazon Neptune (Graph Database)

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `gremlinpython` | >=3.7.0 | Neptune client | Gremlin query language (primary Neptune interface) |
| `rdflib` | >=7.0.0 | Neptune SPARQL | RDF triple support, SPARQL queries |
| `SPARQLWrapper` | >=2.0.0 | Neptune SPARQL | SPARQL endpoint HTTP client |
| `networkx` | >=3.2.0 | Graph analytics | Compute centrality, detect cycles, graph algorithms |
| `py2neo` | >=2021.2.3 | Alternative client | Cypher query support (if using openCypher mode) |

**Usage Example:**
```python
from gremlin_python.driver import client, serializer

# Connect to Neptune
neptune_client = client.Client(
    f'wss://{NEPTUNE_ENDPOINT}:8182/gremlin',
    'g',
    message_serializer=serializer.GraphSONSerializersV2d0()
)

# Execute Gremlin query
query = """
g.V().hasLabel('Process')
     .not(__.in('performs'))
     .values('name')
"""
results = neptune_client.submit(query).all().result()
# Returns: ['Finance Approval', 'QA Testing']
```

```python
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper

# SPARQL query
sparql = SPARQLWrapper(f"https://{NEPTUNE_ENDPOINT}:8182/sparql")
sparql.setQuery("""
    SELECT ?process WHERE {
        ?process rdf:type :Process .
        FILTER NOT EXISTS { ?person :performs ?process }
    }
""")
results = sparql.query().convert()
```

**Query Language Breakdown:**
- **Gremlin** (primary): Graph traversal language, best for complex graph patterns
- **SPARQL**: RDF semantic queries, best for ontology-based reasoning
- **openCypher**: SQL-like graph queries (via py2neo if enabled)

---

### Amazon SageMaker (Fine-tuning & Inference)

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `sagemaker` | >=2.200.0 | Strategizer Agent | Training jobs, model deployment, endpoints |
| `boto3-stubs[sagemaker]` | >=1.34.0 | SageMaker components | Type hints for SageMaker SDK |

**Usage Example:**
```python
import boto3
from sagemaker import Session
from sagemaker.huggingface import HuggingFace

# Training job
sagemaker_session = Session()
huggingface_estimator = HuggingFace(
    entry_point='train.py',
    role='SageMakerRole',
    instance_type='ml.p4d.24xlarge',
    transformers_version='4.36',
    pytorch_version='2.1',
    py_version='py310',
    hyperparameters={
        'model_name': 'meta-llama/Llama-3-70b',
        'epochs': 3,
        'learning_rate': 2e-5
    }
)
huggingface_estimator.fit({'train': 's3://bucket/train_data'})

# Inference
runtime = boto3.client('sagemaker-runtime')
response = runtime.invoke_endpoint(
    EndpointName='strategizer-endpoint',
    ContentType='application/json',
    Body=json.dumps({
        "inputs": "Bottleneck detected: Finance approval delays",
        "parameters": {"max_new_tokens": 256}
    })
)
```

---

### Data Processing & Storage

| SDK Package | Version | Used By | Purpose |
|------------|---------|---------|---------|
| `boto3-stubs[s3]` | >=1.34.0 | S3 operations | Type hints for S3 SDK |
| `s3fs` | >=2024.2.0 | Data ingestion | S3 filesystem interface (pandas integration) |
| `pandas` | >=2.1.0 | Extractor Agent | CSV/Excel parsing, data manipulation |
| `numpy` | >=1.26.0 | Data processing | Numerical operations |
| `pyarrow` | >=15.0.0 | Data storage | Parquet file format (efficient columnar storage) |
| `openpyxl` | >=3.1.0 | Data ingestion | Excel file reading |

**Usage Example:**
```python
import pandas as pd
import s3fs

# Read CSV directly from S3
fs = s3fs.S3FileSystem()
with fs.open('s3://orgmind-bucket/data/org_chart.csv', 'r') as f:
    df = pd.read_csv(f)

# Process and save as Parquet (more efficient)
df.to_parquet('s3://orgmind-bucket/processed/org_chart.parquet')
```

---

### Web Framework & API

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `fastapi` | >=0.109.0 | Backend API | Modern async web framework |
| `uvicorn[standard]` | >=0.27.0 | API server | ASGI server with HTTP/2 and WebSocket support |
| `pydantic` | >=2.5.0 | Data validation | Request/response validation, type safety |
| `websockets` | >=12.0 | Real-time updates | WebSocket connections for live graph updates |

**Usage Example:**
```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI()

class AnalysisRequest(BaseModel):
    query: str
    department: str | None = None

@app.post("/analyze")
async def analyze_org(request: AnalysisRequest):
    # Pydantic validates input automatically
    results = await analyzer_agent.query(request.query)
    return results

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Stream real-time graph updates
    async for update in graph_updates():
        await websocket.send_json(update)
```

---

### Security & Authentication

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `python-jose[cryptography]` | >=3.3.0 | Auth middleware | JWT token creation and validation |
| `passlib[bcrypt]` | >=1.7.4 | User auth | Password hashing (if using local auth) |
| `cryptography` | >=42.0.0 | Data encryption | Encrypt sensitive data, TLS certificates |

---

### Monitoring & Logging

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `structlog` | >=24.1.0 | All components | Structured JSON logging |
| `python-json-logger` | >=2.0.7 | CloudWatch integration | JSON log formatting |
| `sentry-sdk[fastapi]` | >=1.40.0 | Error tracking | Real-time error monitoring |

**Usage Example:**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "neptune_query_executed",
    query_type="find_bottlenecks",
    results_count=3,
    duration_ms=145
)
# Output: {"event": "neptune_query_executed", "query_type": "find_bottlenecks", ...}
```

---

### Testing & Mocking

| SDK Package | Version | Purpose |
|------------|---------|---------|
| `pytest` | >=7.4.0 | Test framework |
| `moto[all]` | >=5.0.0 | Mock AWS services (Bedrock, S3, SageMaker) |
| `faker` | >=22.0.0 | Generate test org data |

**Usage Example:**
```python
from moto import mock_s3
import boto3

@mock_s3
def test_s3_upload():
    # Creates in-memory S3 for testing
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    s3.put_object(Bucket='test-bucket', Key='test.csv', Body=b'data')
    
    # Test your code without hitting real AWS
    assert s3.list_objects(Bucket='test-bucket')['Contents'][0]['Key'] == 'test.csv'
```

---

## 🌐 Frontend (JavaScript/TypeScript) SDK Mapping

### AWS SDK for JavaScript v3

| SDK Package | Version | Component | Purpose |
|------------|---------|-----------|---------|
| `@aws-sdk/client-bedrock-runtime` | ^3.500.0 | Chat UI | Stream Claude responses directly to frontend |
| `@aws-sdk/client-s3` | ^3.500.0 | File upload | Upload org charts/CSVs from browser |
| `@aws-sdk/client-sagemaker-runtime` | ^3.500.0 | Strategy UI | Invoke Strategizer endpoint |
| `@aws-sdk/credential-providers` | ^3.500.0 | Auth | AWS Cognito/IAM credential management |
| `aws-amplify` | ^6.0.0 | Full stack | Hosting, auth, API, storage integration |
| `@aws-amplify/ui-react` | ^6.0.0 | UI components | Pre-built AWS Amplify React components |

**Usage Example:**
```typescript
import { BedrockRuntimeClient, InvokeModelWithResponseStreamCommand } from '@aws-sdk/client-bedrock-runtime';

const bedrockClient = new BedrockRuntimeClient({ region: 'us-east-1' });

async function streamChatResponse(userMessage: string) {
  const command = new InvokeModelWithResponseStreamCommand({
    modelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
    contentType: 'application/json',
    body: JSON.stringify({
      messages: [{ role: 'user', content: userMessage }],
      anthropic_version: 'bedrock-2023-05-31',
      max_tokens: 1024
    })
  });

  const response = await bedrockClient.send(command);
  
  for await (const chunk of response.body) {
    // Stream tokens to UI in real-time
    const text = JSON.parse(new TextDecoder().decode(chunk.chunk.bytes));
    updateChatUI(text.delta.text);
  }
}
```

---

### Graph Visualization Libraries

| Library | Version | Purpose | Best For |
|---------|---------|---------|----------|
| `d3` | ^7.8.5 | Custom graph rendering | Full control, custom layouts |
| `react-force-graph` | ^1.43.0 | 2D/3D force-directed graphs | Large org charts (>100 nodes) |
| `cytoscape` | ^3.28.1 | Advanced graph layouts | Complex relationship visualization |
| `vis-network` | ^9.1.9 | Interactive network graphs | Easy integration, good defaults |

**Usage Example:**
```typescript
import ForceGraph2D from 'react-force-graph';

const GraphVisualization = ({ graphData }) => (
  <ForceGraph2D
    graphData={{
      nodes: [
        { id: 'alice', label: 'Alice', group: 'person' },
        { id: 'finance', label: 'Finance Approval', group: 'process' }
      ],
      links: [
        { source: 'alice', target: 'finance', label: 'performs' }
      ]
    }}
    nodeColor={node => node.group === 'process' ? 'red' : 'blue'}
    linkDirectionalArrowLength={6}
  />
);
```

---

### State Management & API

| Library | Version | Purpose |
|---------|---------|---------|
| `@tanstack/react-query` | ^5.17.0 | Server state management, caching |
| `zustand` | ^4.5.0 | Client state (UI, selected nodes) |
| `socket.io-client` | ^4.6.1 | WebSocket for real-time graph updates |

**Usage Example:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';

// Server state (cached automatically)
const useAnalysis = (query: string) => {
  return useQuery({
    queryKey: ['analysis', query],
    queryFn: () => fetch(`/api/analyze?q=${query}`).then(r => r.json()),
    staleTime: 5 * 60 * 1000 // Cache for 5 minutes
  });
};

// Client state
const useGraphStore = create((set) => ({
  selectedNode: null,
  setSelectedNode: (node) => set({ selectedNode: node }),
  highlightedPaths: [],
  addHighlightedPath: (path) => set((state) => ({
    highlightedPaths: [...state.highlightedPaths, path]
  }))
}));
```

---

### UI Components

| Library | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/react-*` | ^1.0.x | Accessible headless components |
| `tailwindcss` | ^3.4.1 | Utility-first CSS framework |
| `lucide-react` | ^0.316.0 | Icon library |

---

## 🔗 SDK Integration Flow

### End-to-End Example: User Asks "Find Finance Bottlenecks"

```
1. FRONTEND (React)
   └─> User types in chat
   └─> socket.io-client sends message to backend
   
2. BACKEND API (FastAPI)
   └─> Receives WebSocket message
   └─> Calls Analyzer Agent
   
3. ANALYZER AGENT (Bedrock + LangChain)
   └─> anthropic SDK: "Translate query to Gremlin"
   └─> gremlinpython: Execute graph query on Neptune
   
4. NEPTUNE (Graph Database)
   └─> Returns: [{"name": "Finance Approval", "degree": 5}]
   
5. ANALYZER AGENT (Bedrock)
   └─> anthropic SDK: "Interpret results"
   └─> Response: "Finance Approval is a bottleneck (5 dependencies)"
   
6. STRATEGIZER AGENT (SageMaker)
   └─> sagemaker SDK: Invoke endpoint
   └─> Response: "Recommend: Automate approvals <$5K"
   
7. BACKEND API
   └─> websockets: Stream response to frontend
   
8. FRONTEND (React)
   └─> Updates chat UI with recommendation
   └─> react-force-graph: Highlights Finance Approval node in red
```

---

## 📊 SDK Version Matrix

### Python Compatibility

| Python Version | All SDKs Compatible? | Notes |
|---------------|---------------------|-------|
| 3.9 | ✅ Yes | Minimum supported |
| 3.10 | ✅ Yes | Recommended |
| 3.11 | ✅ Yes | Best performance |
| 3.12 | ⚠️ Mostly | Some type stub issues |

### Node.js Compatibility

| Node Version | All SDKs Compatible? | Notes |
|--------------|---------------------|-------|
| 16.x | ⚠️ Deprecated | AWS SDK v3 works but outdated |
| 18.x | ✅ Yes | Recommended (LTS) |
| 20.x | ✅ Yes | Latest LTS |

---

## 🚀 Installation Commands

### Backend Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Verify AWS SDK installation
python -c "import boto3; print(boto3.__version__)"
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Verify AWS SDK installation
npm list @aws-sdk/client-bedrock-runtime
```

---

## 🔍 Troubleshooting Common SDK Issues

### Issue: `ModuleNotFoundError: No module named 'gremlinpython'`
**Solution:**
```bash
pip install gremlinpython>=3.7.0
```

### Issue: Neptune connection timeout
**Solution:**
```python
# Increase timeout in Gremlin client
neptune_client = client.Client(
    neptune_endpoint,
    'g',
    message_serializer=serializer.GraphSONSerializersV2d0(),
    pool_size=8,
    max_workers=8,
    timeout=300  # 5 minutes
)
```

### Issue: Bedrock rate limiting
**Solution:**
```python
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=60))
def call_bedrock():
    return anthropic_client.messages.create(...)
```

---

## 📝 SDK Upgrade Strategy

### Semantic Versioning
- `^3.500.0` - Allow patch and minor updates (safe)
- `~3.500.0` - Allow only patch updates (very conservative)
- `>=3.500.0` - Allow all updates (risky for production)

### Recommended Upgrade Schedule
- **Monthly**: Review AWS SDK updates for security patches
- **Quarterly**: Update minor versions after testing
- **Annually**: Major version upgrades with full regression testing

---

## 🔒 Security Best Practices

1. **Never commit AWS credentials** - Use IAM roles or environment variables
2. **Pin production versions** - Use exact versions in production requirements
3. **Scan dependencies** - Run `pip-audit` or `npm audit` regularly
4. **Use private PyPI mirror** - For enterprise deployments
5. **Enable AWS CloudTrail** - Log all SDK API calls

---

## 📚 Additional Resources

- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS SDK for JavaScript v3](https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/)
- [Gremlin Python Docs](https://tinkerpop.apache.org/docs/current/reference/#gremlin-python)
- [LangChain AWS Integrations](https://python.langchain.com/docs/integrations/platforms/aws)

