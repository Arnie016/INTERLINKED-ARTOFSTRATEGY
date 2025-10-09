# Contributing to OrgMind AI

Thank you for your interest in contributing to OrgMind AI! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/INTERLINKED-ARTOFSTRATEGY.git
   cd INTERLINKED-ARTOFSTRATEGY
   ```
3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/INTERLINKED-ARTOFSTRATEGY.git
   ```

## 🔧 Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- AWS CLI configured
- Git

### Installation

```bash
# Backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Frontend
cd frontend
npm install
```

### Running Tests

```bash
# Python tests
pytest tests/

# JavaScript tests
cd frontend
npm test
```

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear and structured commit messages.

### Format
```
<type>(scope): <summary>

[optional body]

[optional footer]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **refactor**: Code refactoring (no functional changes)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build config)
- **perf**: Performance improvements
- **style**: Code style/formatting changes

### Examples
```bash
feat(extractor): add support for PDF org charts
fix(neptune): resolve connection timeout issue
docs(readme): update installation instructions
refactor(analyzer): simplify bottleneck detection logic
test(strategizer): add unit tests for recommendation engine
```

## 🌿 Branch Strategy

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Keep your branch updated:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

3. **Push to your fork:**
   ```bash
   git push origin feat/your-feature-name
   ```

## 🔍 Code Quality Standards

### Python
- Use **type hints** for all public functions
- Add **docstrings** (Google style)
- Follow **PEP 8** style guide
- Run **black** for formatting: `black .`
- Run **flake8** for linting: `flake8 .`
- Use **mypy** for type checking: `mypy .`

### JavaScript/TypeScript
- Use **TypeScript** with strict mode
- Follow **ESLint** configuration
- Run **Prettier** for formatting: `npm run format`
- Prefer **functional components** and hooks in React

### General
- Write **clear, self-documenting code**
- Add **comments for complex logic**
- Keep functions **small and focused**
- Validate **inputs and handle errors**

## 🧪 Testing Requirements

All contributions must include appropriate tests:

### Unit Tests
- Cover new functions and methods
- Test edge cases and error conditions
- Use **pytest** (Python) or **vitest/jest** (TypeScript)

### Integration Tests
- Test component interactions
- Mock external services (Bedrock, Neptune, SageMaker)
- Ensure deterministic test results

### Test Coverage
- Maintain **>80% code coverage**
- Run coverage reports:
  ```bash
  pytest --cov=. --cov-report=html
  ```

## 📋 Pull Request Process

1. **Ensure all tests pass:**
   ```bash
   pytest tests/
   npm test
   ```

2. **Update documentation** if needed:
   - README.md
   - Code comments
   - API documentation

3. **Create pull request** with a clear description:
   ```markdown
   ## Summary
   Brief description of changes

   ## Motivation
   Why is this change needed?

   ## Changes
   - Bullet point list of changes
   - Include screenshots for UI changes

   ## Testing
   How did you test this?

   ## Risks
   Any potential breaking changes or concerns?

   ## Rollback Plan
   How to revert if issues arise?
   ```

4. **Link related issues:**
   ```markdown
   Closes #123
   Related to #456
   ```

5. **Request review** from maintainers

## 🛡️ Security Guidelines

- **Never commit secrets** or credentials
- Use **.env.example** for environment variable templates
- **Validate all inputs** from external sources
- **Mask PII** in logs and error messages
- Follow **AWS security best practices**
- Report security issues privately to maintainers

## 🐛 Bug Reports

When reporting bugs, include:

1. **Description:** Clear summary of the issue
2. **Steps to Reproduce:** Detailed reproduction steps
3. **Expected Behavior:** What should happen
4. **Actual Behavior:** What actually happens
5. **Environment:**
   - OS version
   - Python/Node.js version
   - AWS region
   - Browser (for frontend issues)
6. **Logs/Screenshots:** Relevant error messages or visuals

## 💡 Feature Requests

For new features, provide:

1. **Problem Statement:** What problem does this solve?
2. **Proposed Solution:** How should it work?
3. **Alternatives Considered:** Other approaches you've thought of
4. **Use Cases:** Real-world scenarios where this is useful
5. **Implementation Ideas:** Technical approach (optional)

## 📞 Communication

- **GitHub Issues:** Bug reports and feature requests
- **Pull Requests:** Code contributions and discussions
- **Discussions:** General questions and ideas

## 🎯 Areas for Contribution

We especially welcome contributions in:

- 🧪 **Testing:** Expanding test coverage
- 📚 **Documentation:** Tutorials, examples, API docs
- 🐛 **Bug Fixes:** Resolving open issues
- ✨ **Features:** Check "good first issue" label
- 🎨 **UI/UX:** Frontend improvements
- 🔧 **DevOps:** CI/CD, deployment automation
- 🧠 **AI/ML:** Model fine-tuning, prompt engineering

## ✅ Review Checklist

Before submitting, verify:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow conventional commits
- [ ] No secrets or PII in code
- [ ] PR description is clear and complete

## 🙏 Thank You!

Your contributions make OrgMind AI better for everyone. We appreciate your time and effort!

---

**Questions?** Open a GitHub Discussion or reach out to the maintainers.

