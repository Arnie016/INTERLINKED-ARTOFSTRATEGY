# OrgMind AI - Clean Repository Structure

```
orgmind-ai/
├── README.md                    # Main project documentation
├── HACKATHON_SUBMISSION.md     # Hackathon submission details
├── LICENSE                     # MIT License
├── package.json               # Root package.json
├── requirements.txt           # Python dependencies
├── tsconfig.json             # TypeScript configuration
├── vercel.json               # Vercel deployment config
├── env.example               # Environment variables template
│
├── frontend/                 # Next.js Frontend
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── types/               # TypeScript types
│   ├── package.json         # Frontend dependencies
│   └── next.config.js       # Next.js configuration
│
├── backend/                  # FastAPI Backend
│   └── api/
│       ├── server.py         # Main FastAPI application
│       ├── services/         # Business logic services
│       ├── prompting/        # AI prompt templates
│       └── config.py         # Configuration management
│
├── data/                     # Demo Data
│   ├── custom_demo_entities.json
│   ├── custom_demo_relationships.json
│   └── custom_demo_summary.json
│
└── strands_agents/          # Neo4j Integration
    ├── src/
    │   ├── agents/           # Neo4j agents
    │   ├── config/           # Neo4j configuration
    │   ├── llm_interface/    # LLM interfaces
    │   └── tools/            # Neo4j tools
    └── requirements.txt      # Neo4j dependencies
```

## **Key Files**

- **`frontend/components/AgentChat.tsx`** - Main chat interface
- **`frontend/components/GraphVisualization.tsx`** - Graph visualization
- **`backend/api/server.py`** - FastAPI application
- **`backend/api/services/exa_client.py`** - Exa.ai integration
- **`backend/api/services/sagemaker_client.py`** - Bedrock integration
- **`data/custom_demo_*.json`** - Demo organizational data

## **Environment Variables**

- `EXA_API_KEY` - Exa.ai API key
- `AWS_REGION` - AWS region
- `NEO4J_URI` - Neo4j database URI (optional)
- `NEO4J_USERNAME` - Neo4j username (optional)
- `NEO4J_PASSWORD` - Neo4j password (optional)

## **Deployment**

- **Vercel**: Frontend + Backend deployment
- **Environment**: Production-ready with proper error handling
- **Demo Data**: Fallback to local JSON if Neo4j unavailable
