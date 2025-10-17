# Project Instructions

## Tool Usage Priority

**CRITICAL**: Always prioritize the following tools when searching for information:

1. **First Priority**: Use `strands-agents` MCP server tool for any Strands Agents related queries
2. **Second Priority**: Use `bedrock-agentcore` MCP server tool for any AWS Bedrock AgentCore queries
3. Check project documentation
4. Web search as last resort

## Specific Guidelines

- For agent development questions → use `strands-agents:search_docs` first
- For deployment on AWS Bedrock → use `bedrock-agentcore-mcp-server:search_agentcore_docs` first
- Always fetch full documentation with the corresponding fetch tool if initial search results are insufficient

## Example Workflow

When asked about "how to use MCP tools":
1. Call `strands-agents:search_docs` with query "MCP tools"
2. If needed, call `strands-agents:fetch_doc` with the relevant URL
3. Only search web if documentation is not found

## .taskmaster/tasks/tasks.json

- Use the `task-master` CLI to manage tasks
- Use the `task-master` MCP server tool to manage tasks
- Whenever you are finished with a task, use the `task-master` MCP server tool to mark the task from pending to completed, within ./taskmaster/tasks/tasks.json

## Github Commit Messages
- We use the Conventional Commits format for commit messages    
- Types
  - feat: New feature
  - fix: Bug fix
  - docs: Documentation changes
  - refactor: Code refactoring (no functional changes)
  - test: Adding or updating tests
  - chore: Maintenance tasks (dependencies, build config)
  - perf: Performance improvements
  - style: Code style/formatting changes
- Do not add 🤖 Generated with [Claude Code](https://claude.com/claude-code) to the commit message.

## Security Guidelines

- NEVER commit API keys or secrets
- Use environment variables for sensitive data
- Validate all user inputs
- Sanitize data before database queries
- Use parameterized queries (no string concatenation)
- Enable CORS only for trusted domains

### Input Validation
```python
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    email: str
    age: int
    
    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Invalid age')
        return v
```