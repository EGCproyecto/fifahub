# Contributing to FIFAHub

Thank you for contributing to FIFAHub! This guide will help you understand our workflow and conventions.

## Table of Contents

- [Development Setup](#development-setup)
- [Branch Workflow](#branch-workflow)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)

---

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/fifahub.git
   cd fifahub
   ```

2. **Set up environment**
   ```bash
   cp .env.docker.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker**
   ```bash
   docker compose up --build -d
   ```

4. **Access the application** at http://localhost:5000

---

## Branch Workflow

We use a trunk-based development workflow:

```
main (production)
  ↑
trunk (development/staging)
  ↑
featuretask/* (your work)
```

### Branch Types

| Branch | Purpose | Created From | Merges To |
|--------|---------|--------------|----------|
| `main` | Production code | - | - |
| `trunk` | Development/staging | `main` | `main` |
| `featuretask/*` | New features and fixes | `trunk` | `trunk` |

### Creating a Feature Branch

```bash
# Start from trunk
git checkout trunk
git pull origin trunk

# Create your feature branch
git checkout -b featuretask/my-feature

# Work on your changes...
git add .
git commit -m "feat: add my feature"

# Push and create PR to trunk
git push -u origin featuretask/my-feature
```

---

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `docs` | Documentation only | Patch |
| `style` | Code style (formatting) | Patch |
| `refactor` | Code refactoring | Patch |
| `perf` | Performance improvement | Patch |
| `test` | Adding/updating tests | Patch |
| `ci` | CI/CD changes | Patch |
| `build` | Build system changes | Patch |
| `chore` | Other changes | Patch |

### Examples

```bash
# Feature
git commit -m "feat(dataset): add CSV export functionality"

# Bug fix
git commit -m "fix(upload): resolve file size validation error"

# Documentation
git commit -m "docs: update README with new setup instructions"

# Breaking change (appends ! or includes BREAKING CHANGE in footer)
git commit -m "feat!: redesign API endpoints"
```

---

## Pull Request Process

1. **Create your branch** from `trunk`
2. **Make your changes** following our conventions
3. **Ensure tests pass** locally
4. **Push your branch** and create a Pull Request to `trunk`
5. **Wait for CI checks** to pass
6. **Request review** from a team member
7. **Merge to trunk** after approval
8. **Merge trunk to main** for production release

### PR Title Format

Use the same format as commit messages:
```
feat(scope): description of changes
```

---

## Code Style

We use automated formatting tools:

- **[Black](https://black.readthedocs.io/)** - Python code formatter
- **[isort](https://pycqa.github.io/isort/)** - Import sorter

### Before Committing

```bash
# Format code
black app rosemary core
isort --profile black app rosemary core

# Check formatting (CI will run these)
black --check app rosemary core
isort --check-only --profile black app rosemary core
```

### Pre-commit Hooks

We recommend using pre-commit hooks to automatically format code:

```bash
pip install pre-commit
pre-commit install
```

---

## Testing

### Running Tests Locally

```bash
# Ensure MariaDB is running (Docker does this automatically)
pytest app/modules/ --ignore-glob='*selenium*'

# Run with coverage
pytest app/modules/ --cov=app --ignore-glob='*selenium*'

# Run specific test file
pytest app/modules/tabular/tests/test_unit.py -v
```

### Test Structure

Tests are located in each module's `tests/` directory:
```
app/modules/
├── tabular/
│   └── tests/
│       ├── test_unit.py
│       ├── test_integration.py
│       └── locustfile.py
├── dataset/
│   └── tests/
│       └── ...
```

### Writing Tests

- Use `pytest` fixtures for common setup
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use descriptive names: `test_upload_rejects_non_fifa_schema`

---

## Questions?

If you have questions or need help, please:
1. Check existing documentation in `docs/`
2. Search existing issues
3. Create a new issue with your question

Thank you for contributing! 
