# Product Requirements Document (PRD)

Title: Interlinked – Strands Agents + AWS Bedrock AgentCore Refactor

Version: 0.1 (Draft)

Date: 2025-10-16

Owner: Stef 

Status: Draft for implementation

## 1. Goals

- Migrate the current custom agent backend to Strands Agents, deployed on AWS Bedrock AgentCore Runtime.
- Adopt the “Agents as Tools” pattern with a single orchestration entrypoint and specialized agents.
- Integrate Neo4j initially via direct Python class-based tools; add AgentCore Gateway for production hardening.
- Introduce AgentCore Identity (Cognito), Memory, Observability, and Gateway where applicable.
- Maintain API compatibility for the existing frontend during development; simplify production by calling AgentCore directly.

## 2. Non‑Goals

- Comprehensive frontend refactor (beyond minor changes for AgentCore direct calls in production).
- Rewriting graph domain logic beyond what’s needed for tool wrapping and safety.
- Implementing complex RBAC beyond simple user/admin roles in the hackathon scope.

## 3. Assumptions

- AgentCore access is available and AWS CLI is configured.
- Region: us-west-2 (unless noted otherwise).
- Model: Bedrock Claude 3.5 Sonnet (tool-calling capable) with Strands integration.
- Neo4j is reachable from dev/prod environments; secrets managed via env locally and AWS Secrets Manager in prod.
- Frontend can switch to calling AgentCore directly for production deployment.

## 4. Current System Overview (Concise)

- Frontend chat component calls `POST /api/chat` on the backend.
- Backend is FastAPI with an `AgentOrchestrator` that selects concrete agents (`GraphAgent`, `AnalyzerAgent`, `ExtractorAgent`, `AdminAgent`).
- Agents share a `BaseAgent` providing: Neo4j driver setup, Bedrock model client, tool registry, memory list, and tool execution helpers.
- Tools live under `backend/tools/` (CRUD, search, analysis, admin utilities) and operate directly on the Neo4j driver/session.

## 5. Target Architecture

### 5.1 Orchestration Pattern

- Use Strands “Agents as Tools”. A primary `OrchestratorAgent` routes the user’s prompt and can call:
  - `GraphAgent` (read/search, analysis)
  - `AnalyzerAgent` (analytics)
  - `ExtractorAgent` (ingestion)
  - `AdminAgent` (admin ops)
- Each specialized agent exposes a curated toolset.

### 5.2 Neo4j Integration Strategy

- Phase 1 (Dev/MVP): Direct Python class-based tools annotated with `@tool` and explicit type hints, using the Neo4j driver.
- Phase 2 (Prod): Wrap Neo4j access behind AgentCore Gateway (Lambda target, OAuth/Cognito), exposed as agent tools; enable rate limiting, authZ, observability.
- Security: no credentials in code; env for dev; AWS Secrets Manager in prod.

### 5.3 Identity & Auth

- AgentCore Identity via Cognito for end-user auth.
- Roles: `user`, `admin` (mapped to tool allowlists).
- Frontend uses Cognito Hosted UI; tokens forwarded to AgentCore.

### 5.4 Memory

- AgentCore Memory for conversation state and tool-call traces.
- No PII persisted beyond session by default; configurable retention flags.
- Minimal local memory fallback in dev only.

### 5.5 Observability

- Enable AgentCore Observability for traces, logs, and metrics (model calls, tool calls, Neo4j gateway calls).

### 5.6 API Compatibility Strategy

- Development: keep FastAPI `/api/chat` proxy to maintain the existing frontend contract.
- Production: remove FastAPI proxy; frontend calls AgentCore Runtime directly (authentication, sessions, rate limiting provided by AgentCore).
- Keep a simple health endpoint if needed for legacy checks.

### 5.7 Deployment Shape

- Dev: local Strands agent runtime + FastAPI proxy + Neo4j (local/remote).
- Prod: Strands agents deployed to AgentCore Runtime; Neo4j via Gateway; frontend → AgentCore directly.

## 6. Tools Matrix, Access, and Safety

High-level mapping; concrete signatures defined during implementation with `@tool` and docstrings.

- GraphAgent (read-only):
  - `search_nodes`, `find_related_nodes`, `get_graph_snapshot`, `explain_path`
  - Deny: any write/delete operations

- AnalyzerAgent (read-only + compute):
  - `centrality_analysis`, `community_detection`, `graph_stats`
  - Deny: writes

- ExtractorAgent (write-limited):
  - `create_node`, `create_relationship`, `bulk_ingest` (schema-validated)
  - Allow only whitelisted labels/relationship types; validate payload size; idempotency where feasible

- AdminAgent (privileged writes):
  - `reindex`, `migrate_labels`, `maintenance_*` tasks
  - Guarded by `admin` role; dry-run flags; explicit confirmation inputs for destructive ops

Safety Principles:
- Strict type hints and parameter schemas; validate before execution.
- Block raw/unrestricted Cypher in user-facing tools.
- Enforce query complexity/timeout limits; paginate large results.
- Log and trace all tool calls; redact secrets from logs.

## 7. Data & Domain Constraints

- No additional invariants declared; implement best-practice validations (unique keys when applicable, label/relationship allowlists for write tools).

## 8. Migration & Delivery Plan

Milestone 1 – Scaffolding (Dev)
- Create Strands project structure; define `OrchestratorAgent` and the four specialized agents.
- Wrap essential read-only tools with `@tool` and types; map to agents.
- Wire Neo4j connection configuration and env management.

Milestone 2 – Orchestrator Integration
- Implement Agents-as-Tools orchestration and prompt routing.
- Replace backend `AgentOrchestrator` usage under the FastAPI proxy with Strands entrypoint.
- Maintain `/api/chat` contract for the existing frontend.

Milestone 3 – AgentCore Runtime Deployment (MVP)
- Package and deploy Strands agent to AgentCore Runtime in `us-west-2`.
- Enable Identity, Memory, Observability.
- Smoke tests: health, simple read path, minimal write path guarded by role.

Milestone 4 – Neo4j via AgentCore Gateway (Prod Hardening)
- Implement Lambda target that connects to Neo4j; define Gateway tools and OAuth authorizer.
- Switch Strands tools to call Gateway instead of direct driver where appropriate.
- Rate limits, retries, and better error handling.

Milestone 5 – Frontend Direct to AgentCore
- Update Next.js to authenticate with Cognito and call AgentCore directly.
- Deprecate FastAPI proxy for production.

Milestone 6 – Cleanup & Docs
- Remove dev-only code paths; finalize docs and operational runbooks.

## 9. Deployment Plan (Concise)

Region & Naming
- Region: `us-west-2`.
- Resource prefixes: `interlinked-aos-<env>`.

Secrets & Config
- Dev: `.env`.
- Prod: AWS Secrets Manager for Neo4j credentials; SSM for non-secrets config as needed.

CI/CD (thin for hackathon)
- Manual deploy via AgentCore CLI/MCP; optional GitHub Actions later.

Rollout
- Dev deploy → verify → prod deploy.
- Feature flags for switching Neo4j access mode (direct vs gateway).

## 10. API Compatibility & Contracts

Development
- Keep `POST /api/chat` signature identical for the frontend; backend proxy forwards to Strands.

Production
- Frontend calls AgentCore Runtime endpoints directly:
  - `POST /invocations` (agent calls)
  - `GET /ping` (health)

## 11. Security

- Cognito-based Identity via AgentCore; short-lived tokens in frontend; no secrets in client.
- Gateway with OAuth for Neo4j; least-privilege execution roles.
- Tool allowlists per role; destructive ops require explicit confirmations.

## 12. Observability & SLOs

- Enable tracing of model/tool calls and Gateway interactions.
- Basic SLOs (hackathon):
  - P50 latency ≤ 1.5s for read queries; ≤ 3s for analysis; ≤ 5s for small writes.
  - Error rate ≤ 2% during demo.

## 13. Acceptance Criteria

- User can authenticate and chat; agent responds using Strands on AgentCore.
- Read-only graph queries succeed via tools; traces visible in AgentCore.
- Admin-only write operation is blocked for non-admin and succeeds for admin under small payloads.
- Frontend works unmodified in dev (via FastAPI proxy) and works in prod via AgentCore direct calls.
- Optional: Neo4j Gateway path demonstrated in production.

## 14. Risks & Mitigations

- Full rewrite risk → phased milestones; keep proxy until prod cutover.
- Gateway complexity → start with direct class-based tools; migrate behind a feature flag.
- Auth wiring time cost → use Cognito Hosted UI; rely on AgentCore Identity defaults.
- Tool safety gaps → strict schemas, allowlists, dry-run flags, confirmations.

## 15. Out of Scope (Hackathon)

- Advanced RBAC, rate-limit policies beyond defaults.
- Complex caching and request transformations.
- Deep performance tuning or cost optimization.

## 16. Appendix – File Pointers (for developers)

- FastAPI entrypoint: `backend/api/main.py`
- Orchestrator: `backend/agents/agent_orchestrator.py`
- Base agent: `backend/agents/base_agent.py`
- Specialized agents: `backend/agents/{graph,analyzer,extractor,admin}_agent.py`
- Neo4j config: `backend/config/database_config.py`
- Tools: `backend/tools/*.py`
- Frontend chat: `frontend/components/AgentChat.tsx`


