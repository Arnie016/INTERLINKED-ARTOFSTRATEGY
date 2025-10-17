# Strands Agents Documentation

Welcome to the Strands Agents documentation! This directory contains comprehensive guides and technical documentation for the project.

## 📚 Documentation Structure

### Getting Started Guides

New to the project? Start here:

1. **[Quick Start Guide](guides/quick-start.md)**
   - Prerequisites and setup
   - Environment configuration
   - Basic usage examples
   - Troubleshooting common issues

2. **[AWS Setup Guide](guides/aws-setup.md)**
   - AWS CLI installation
   - Credential configuration
   - IAM permissions setup
   - Secrets Manager configuration

3. **[Neo4j Setup Guide](guides/neo4j-setup.md)**
   - Neo4j connection configuration
   - Environment variables
   - Connection testing
   - Security best practices

4. **[Secrets Manager Setup Guide](guides/secrets-manager-setup.md)**
   - AWS Secrets Manager integration
   - Secret structure and naming
   - Production credential management
   - Caching and fallback strategies

5. **[Admin Operations Guide](guides/admin-operations.md)**
   - Role-based access control
   - Index management operations
   - Label migration procedures
   - Database maintenance and cleanup
   - Safety measures and audit logging

6. **[Performance Optimization Guide](guides/performance-optimization.md)**
   - Result caching strategies
   - Timeout management
   - Performance monitoring
   - Optimization best practices

### Architecture & Design

Understanding the system:

1. **[Architecture Overview](architecture/overview.md)**
   - Agent hierarchy and patterns
   - Graph schema design
   - Temperature tuning strategy
   - Security considerations

2. **[Integration Guide](architecture/integration.md)**
   - Integrating shared utilities
   - Configuration management
   - Error handling patterns
   - Testing strategies

### Implementation Details

For developers working on the codebase:

1. **[Agent Implementation Summary](implementation/agents.md)**
   - Task 1.2 completion details
   - Agent specifications
   - Tool definitions
   - Next steps

2. **[Utilities Implementation Summary](implementation/utilities.md)**
   - Logging infrastructure
   - Error handling system
   - Validation utilities
   - Authentication framework

3. **[Setup Summary](implementation/setup.md)**
   - Project initialization
   - Directory structure
   - Configuration files
   - Verification steps

## 🔍 Quick Reference

### By Role

**I'm a new developer:**
1. Start with [Quick Start Guide](guides/quick-start.md)
2. Read [Architecture Overview](architecture/overview.md)
3. Review [Testing Guide](../tests/README.md)

**I'm configuring the system:**
1. Check [AWS Setup Guide](guides/aws-setup.md)
2. Review [Neo4j Setup Guide](guides/neo4j-setup.md)
3. See [Secrets Manager Setup](guides/secrets-manager-setup.md)
4. Review [Configuration Module Docs](../src/config/README.md)

**I'm performing admin operations:**
1. Read [Admin Operations Guide](guides/admin-operations.md)
2. Understand [RBAC and security](guides/admin-operations.md#role-based-access-control)
3. Review [safety measures](guides/admin-operations.md#safety-measures)
4. Check [audit logging](guides/admin-operations.md#audit-logging)

**I'm integrating agents:**
1. Read [Integration Guide](architecture/integration.md)
2. Review [Utilities Module Docs](../src/utils/README.md)
3. Check [Agent Implementation](implementation/agents.md)

**I'm writing tests:**
1. Start with [Testing Guide](../tests/README.md)
2. Review test helpers in [Utilities Docs](../src/utils/README.md)
3. Check implementation summaries for examples

### By Task

**Setting up the environment:**
- [Quick Start](guides/quick-start.md)
- [AWS Setup](guides/aws-setup.md)
- [Neo4j Setup](guides/neo4j-setup.md)
- [Secrets Manager](guides/secrets-manager-setup.md)

**Performing admin operations:**
- [Admin Operations Guide](guides/admin-operations.md)
- [Performance Optimization](guides/performance-optimization.md)

**Understanding the architecture:**
- [Architecture Overview](architecture/overview.md)
- [Agent Implementation](implementation/agents.md)

**Configuring the system:**
- [Configuration Module](../src/config/README.md)
- [Neo4j Setup](guides/neo4j-setup.md)
- [AWS Setup](guides/aws-setup.md)

**Integrating components:**
- [Integration Guide](architecture/integration.md)
- [Utilities Module](../src/utils/README.md)

**Testing:**
- [Testing Guide](../tests/README.md)
- [Utilities Implementation](implementation/utilities.md)

## 📖 Module Documentation

In-depth technical documentation for specific modules:

- **[Configuration Module](../src/config/README.md)**
  - Configuration loading
  - Environment variables
  - Model configuration
  - Constants and enums

- **[Utilities Module](../src/utils/README.md)**
  - Logging infrastructure
  - Error handling
  - Validation utilities
  - Authentication
  - Response formatting
  - Test helpers

- **[Testing Guide](../tests/README.md)**
  - Running tests
  - Test organization
  - What tests validate
  - Future testing plans

## 🎯 Common Tasks

### First Time Setup
```bash
# Follow these guides in order:
1. Quick Start Guide
2. AWS Setup Guide
3. Neo4j Setup Guide
```

### Daily Development
```bash
# Activate environment
source venv/bin/activate

# Run tests
pytest tests/ -v

# Check specific module docs
cat src/config/README.md
cat src/utils/README.md
```

### Configuration Changes
```bash
# Review configuration docs
cat docs/guides/neo4j-setup.md
cat src/config/README.md

# Update .env file
nano .env
```

### Integration Work
```bash
# Read integration guide
cat docs/architecture/integration.md

# Review utilities
cat src/utils/README.md
```

## 🔗 External Resources

- [Strands Agents SDK](https://github.com/anthropics/strands-agents)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 💡 Tips

1. **Start with guides/** - User-facing documentation for getting started
2. **Move to architecture/** - Technical understanding of the system
3. **Reference implementation/** - Deep dives when needed
4. **Check module docs** - In-depth technical details

## 🆘 Getting Help

If you can't find what you need:

1. **Search this documentation** - Use your editor's search feature
2. **Check the main README** - `../README.md`
3. **Review code comments** - Source files have detailed docstrings
4. **Ask the team** - Create an issue or reach out directly

## 📝 Contributing to Documentation

When adding new documentation:

- **Guides** → `docs/guides/` - User-facing, getting started content
- **Architecture** → `docs/architecture/` - Technical design documents
- **Implementation** → `docs/implementation/` - Detailed implementation summaries
- **Module Docs** → `src/{module}/README.md` - Module-specific technical docs

Keep documentation:
- Clear and concise
- Well-structured with headings
- Rich with examples
- Up-to-date with code changes

