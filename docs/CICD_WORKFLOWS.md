# FIFAHub CI/CD Workflows

This document describes the GitHub Actions workflows used to automate testing, building, and deployment of FIFAHub.

## Overview

FIFAHub uses two main CI/CD pipelines:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [CI-CD Dev](#ci-cd-dev-workflow) | Push to `trunk`, `feature/**` branches | Testing and staging deployment |
| [CI-CD Prod](#ci-cd-prod-workflow) | Push to `main` branch | Production release and deployment |

---

## CI-CD Dev Workflow

**File:** `.github/workflows/ci-cd-dev.yml`

This workflow runs on development branches to ensure code quality before merging to production.

### Pipeline Stages

1. **Commits** → 2. **Style Check** → 3. **Tests** → 4. **Deploy Staging** (only on `trunk`)

### Jobs

#### 1. Conventional Commits
- **Purpose**: Validates that commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) format
- **Example valid commits**:
  - `feat: add player search feature`
  - `fix: resolve pagination bug`
  - `docs: update README`

#### 2. Style (black/isort)
- **Purpose**: Ensures consistent Python code formatting
- **Tools**:
  - [Black](https://black.readthedocs.io/) - Code formatter
  - [isort](https://pycqa.github.io/isort/) - Import sorter

#### 3. Tests (pytest + MariaDB)
- **Purpose**: Runs the test suite against a real MariaDB instance
- **Configuration**:
  - Python 3.12
  - MariaDB 12.0.2 service container
  - Excludes Selenium tests (headless browser tests)

#### 4. Deploy to Staging (Render)
- **Trigger**: Only on `trunk` branch, after tests pass
- **Action**: Triggers Render staging webhook to deploy latest changes

---

## CI-CD Prod Workflow

**File:** `.github/workflows/ci-cd-prod.yml`

This workflow handles production releases with automatic semantic versioning.

### Pipeline Stages

1. **Commits** → 2. **Style Check** → 3. **Tests** → 4. **Release Automation** → 5. **Docker Hub Publish** → 6. **Deploy Production**

### Jobs

#### 1-3. Commits, Style, Tests
Same as the Dev workflow - ensures code quality.

#### 4. Release Automation (SemVer)
- **Purpose**: Automatically determines version bump based on commit messages
- **Version Rules**:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `BREAKING CHANGE` or `!` | Major (X.0.0) | `feat!: redesign API` |
| `feat:` | Minor (0.X.0) | `feat: add export feature` |
| `fix:`, `perf:`, `refactor:`, `test:`, `ci:`, `build:`, `chore:`, `docs:` | Patch (0.0.X) | `fix: correct typo` |

- **Output**: Creates a GitHub Release with auto-generated release notes

#### 5. Docker Hub Publish
- **Purpose**: Builds and pushes Docker image to Docker Hub
- **Image**: `<DOCKER_USER>/fifahub:vX.Y.Z` and `:latest`
- **Dockerfile**: `docker/images/Dockerfile.render`

#### 6. Deploy to Production (Render)
- **Trigger**: After Docker image is pushed successfully
- **Action**: Triggers Render production webhook

---

## Required Secrets

Configure these secrets in your GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `DOCKER_USER` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub password or access token |
| `RENDER_STAGING_DEPLOY_HOOK_URL` | Render webhook URL for staging |
| `RENDER_PROD_DEPLOY_HOOK_URL` | Render webhook URL for production |

---

## Branch Strategy

```
main (production)
  ↑
trunk (development/staging)
  ↑
featuretask/* (your work)
```

1. **Create feature branch** from `trunk`: `git checkout -b featuretask/my-feature trunk`
2. **Develop and commit** following conventional commits
3. **Merge to trunk** for staging deployment
4. **Merge trunk to main** for production release

