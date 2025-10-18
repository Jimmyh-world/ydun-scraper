# GitHub Actions Deployment Guide for ydun-scraper

**Created:** 2025-10-18
**Status:** Planning Document (Not Implemented)
**Current Deployment:** Local Docker Compose
**Target:** Automated CI/CD Pipeline via GitHub Actions

---

## Table of Contents

1. [Overview](#overview)
2. [Current vs Proposed](#current-vs-proposed)
3. [Prerequisites](#prerequisites)
4. [Implementation Steps](#implementation-steps)
5. [Workflow Configuration](#workflow-configuration)
6. [Registry Options](#registry-options)
7. [Deployment Integration](#deployment-integration)
8. [Monitoring & Validation](#monitoring--validation)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

---

## Overview

This document provides a complete roadmap for implementing automated CI/CD deployment of ydun-scraper using GitHub Actions. When implemented, it will:

✅ Automatically build Docker images on code changes
✅ Run tests and validations before deployment
✅ Push images to a container registry
✅ Deploy to production Beast server
✅ Provide automated rollback capability
✅ Generate deployment notifications

---

## Current vs Proposed

### Current Flow (Local)
```
Developer Push to GitHub
         ↓
Manual SSH to Beast
         ↓
Manual: git pull
         ↓
Manual: docker compose build
         ↓
Manual: docker compose up -d
         ↓
Manual: verify health endpoint
```

**Issues:**
- Manual process prone to errors
- No version control of deployments
- No automated testing before deploy
- Slow feedback loop
- No easy rollback

### Proposed Flow (GitHub Actions)
```
Developer Push to GitHub
         ↓
GitHub Actions Triggered
         ↓
Step 1: Checkout code
Step 2: Run tests/linting
Step 3: Build Docker image
Step 4: Push to registry
Step 5: Deploy to Beast (via webhook/SSH)
Step 6: Run health checks
Step 7: Notify status
         ↓
Production Updated (or rolled back if failed)
```

**Benefits:**
- Fully automated
- Consistent deployments
- Automatic rollback on failure
- Version history
- Fast feedback
- Audit trail

---

## Prerequisites

Before implementing GitHub Actions for ydun-scraper, ensure:

### 1. Repository Requirements
- [x] Repository is on GitHub
- [x] Repository: `git@github.com:Jimmyh-world/ydun-scraper.git`
- [x] Main branch is protected (recommended)
- [ ] Branch protection rules configured (optional)

### 2. Docker Registry Access

**Choose ONE of the following:**

#### Option A: GitHub Container Registry (GHCR)
```
Registry: ghcr.io
Auth: GitHub Token (built-in)
Cost: Free for public images, included with GitHub
Benefit: No separate account, integrated with GitHub
```

#### Option B: Docker Hub
```
Registry: docker.io
Auth: Docker Hub credentials
Cost: Free tier available, paid for private
Benefit: Industry standard, easy to use
```

#### Option C: Private Registry
```
Registry: self-hosted (optional)
Auth: Custom credentials
Cost: Server hosting cost
Benefit: Full control, no external dependency
```

**Recommendation:** Start with **GitHub Container Registry (GHCR)** - no additional setup needed.

### 3. Deployment Access

#### Beast Server SSH Access
```bash
# Verify SSH access to Beast
ssh -i ~/.ssh/id_rsa jimmyb@192.168.1.100
# or
ssh beast.local

# Verify Docker is running
docker ps
docker compose --version
```

#### Create Deploy Key (Optional)
For GitHub Actions to deploy without password:
```bash
# On Beast server
ssh-keygen -t ed25519 -f ~/.ssh/github-deploy-key -C "github-actions"

# Add to ~/.ssh/authorized_keys
cat ~/.ssh/github-deploy-key.pub >> ~/.ssh/authorized_keys

# Get private key for GitHub
cat ~/.ssh/github-deploy-key
```

### 4. GitHub Secrets Configuration

Navigate to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:

```
DEPLOY_HOST=192.168.1.100  (or beast.local)
DEPLOY_USER=jimmyb
DEPLOY_KEY=<private SSH key content>
DOCKER_REGISTRY=ghcr.io
DOCKER_USERNAME=<github-username>
DOCKER_PASSWORD=<github-token>
```

**Create GitHub Token:**
1. Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Select scopes:
   - `repo` (full control of repositories)
   - `write:packages` (upload to GitHub Container Registry)
   - `read:packages` (download from GitHub Container Registry)
4. Copy token and save as `DOCKER_PASSWORD` secret

---

## Implementation Steps

### Step 1: Create Workflows Directory

```bash
cd /home/jimmyb/ydun-scraper
mkdir -p .github/workflows
```

### Step 2: Create Build & Push Workflow

**File:** `.github/workflows/build-and-push.yml`

This workflow builds and pushes the Docker image on every push to main.

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    paths:
      - 'src/**'
      - 'Dockerfile'
      - 'requirements.txt'
      - '.github/workflows/build-and-push.yml'
  pull_request:
    branches: [ main ]
  workflow_dispatch:  # Allow manual trigger

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Image digest
        run: echo ${{ steps.docker_build.outputs.digest }}
```

### Step 3: Create Deploy Workflow

**File:** `.github/workflows/deploy.yml`

This workflow deploys to Beast when a release is created or main is updated.

```yaml
name: Deploy to Beast

on:
  push:
    branches: [ main ]
  workflow_run:
    workflows: ["Build and Push Docker Image"]
    types: [completed]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name != 'workflow_run' }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          port: 22
          script: |
            set -e

            echo "🚀 Starting deployment of ydun-scraper..."

            # Navigate to project
            cd ~/network-infrastructure/beast/docker

            # Pull latest code
            echo "📥 Pulling latest code..."
            cd ~/ydun-scraper
            git pull origin main

            # Pull latest image from registry
            echo "🐳 Pulling latest Docker image..."
            docker pull ghcr.io/${{ github.repository }}:latest

            # Update docker-compose
            echo "♻️ Stopping old container..."
            cd ~/network-infrastructure/beast/docker
            docker compose stop ydun-scraper || true

            # Start new container
            echo "🔄 Starting new container..."
            docker compose up -d ydun-scraper

            # Wait for container to be healthy
            echo "⏳ Waiting for container to be healthy..."
            sleep 5

            # Health check
            echo "🏥 Running health check..."
            if curl -f http://localhost:5000/health > /dev/null 2>&1; then
              echo "✅ Health check passed!"
            else
              echo "❌ Health check failed!"
              docker compose logs ydun-scraper
              exit 1
            fi

            echo "✨ Deployment complete!"

      - name: Verify Deployment
        run: |
          echo "Checking deployment status..."
          sleep 2
          curl -v http://localhost:5000/health || echo "Warning: Could not verify health"

      - name: Deployment Notification
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const status = context.job.status === 'success' ? '✅ Success' : '❌ Failed';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `${status} - Deployment to Beast: ${status}`
            })
```

### Step 4: Create Test Workflow (Optional)

**File:** `.github/workflows/test.yml`

Run tests and linting before deployment.

```yaml
name: Test & Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pylint flake8

      - name: Run linting
        run: |
          echo "🔍 Running pylint..."
          pylint src/ --disable=all --enable=E,F || true

          echo "🔍 Running flake8..."
          flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Test imports
        run: |
          echo "Testing Python imports..."
          python -c "from src.http_server import app; print('✅ http_server imports OK')"
          python -c "from src.batch_scraper import BatchScraper; print('✅ batch_scraper imports OK')"

      - name: Build Docker image (test)
        run: |
          echo "🐳 Testing Docker build..."
          docker build -t ydun-scraper:test .
          docker inspect ydun-scraper:test || exit 1
          echo "✅ Docker build successful"
```

### Step 5: Create Rollback Workflow (Optional)

**File:** `.github/workflows/rollback.yml`

Manually trigger rollback to previous version.

```yaml
name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to (e.g., main-sha123456)'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest

    steps:
      - name: Rollback via SSH
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            set -e

            echo "⚠️ Rolling back to version: ${{ github.event.inputs.version }}"

            cd ~/network-infrastructure/beast/docker

            # Stop current container
            docker compose stop ydun-scraper || true

            # Pull previous image
            docker pull ghcr.io/${{ github.repository }}:${{ github.event.inputs.version }}

            # Update docker-compose.yml temporarily
            # (This is simplified - in practice you'd need version management)

            # Start rolled-back container
            docker compose up -d ydun-scraper

            # Health check
            sleep 5
            curl -f http://localhost:5000/health || exit 1

            echo "✅ Rollback complete to version: ${{ github.event.inputs.version }}"
```

---

## Workflow Configuration

### File: `.github/workflows/build-and-push.yml` (Full Example)

**Path:** `/home/jimmyb/ydun-scraper/.github/workflows/build-and-push.yml`

```yaml
name: Build and Push Docker Image

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'src/**'
      - 'Dockerfile'
      - 'requirements.txt'
      - '.github/workflows/**'
  pull_request:
    branches:
      - main
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Image Summary
        run: |
          echo "## Docker Build Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Registry**: ${{ env.REGISTRY }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Image**: ${{ env.IMAGE_NAME }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Tags**: ${{ steps.meta.outputs.tags }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Pushed**: ${{ github.event_name != 'pull_request' }}" >> $GITHUB_STEP_SUMMARY
```

### File: `.github/workflows/deploy.yml` (Full Example)

**Path:** `/home/jimmyb/ydun-scraper/.github/workflows/deploy.yml`

```yaml
name: Deploy to Beast

on:
  push:
    branches:
      - main
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (no actual deployment)'
        required: false
        default: 'false'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to Beast
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          port: 22
          command_timeout: 30m
          script: |
            set -e

            echo "========================================="
            echo "🚀 Starting ydun-scraper Deployment"
            echo "========================================="
            echo "Timestamp: $(date)"
            echo "Git Commit: ${{ github.sha }}"
            echo "Branch: ${{ github.ref_name }}"

            # Navigation
            COMPOSE_DIR="$HOME/network-infrastructure/beast/docker"
            SCRAPER_DIR="$HOME/ydun-scraper"

            # Pull latest code
            echo ""
            echo "📥 Pulling latest code..."
            cd "$SCRAPER_DIR"
            git fetch origin
            git checkout ${{ github.ref_name }}
            git pull origin ${{ github.ref_name }}
            COMMIT=$(git rev-parse --short HEAD)
            echo "✅ Code updated to: $COMMIT"

            # Pull latest image
            echo ""
            echo "🐳 Pulling Docker image..."
            docker pull ghcr.io/${{ github.repository }}:latest || {
              echo "❌ Failed to pull image"
              exit 1
            }
            echo "✅ Image pulled successfully"

            # Backup current container
            echo ""
            echo "💾 Backing up current container..."
            cd "$COMPOSE_DIR"
            docker compose ps ydun-scraper 2>/dev/null && \
              docker commit ydun-scraper ydun-scraper:backup-$(date +%s) || true

            # Stop and update
            echo ""
            echo "🔄 Stopping current container..."
            docker compose stop ydun-scraper || true

            echo "🔄 Starting new container..."
            docker compose up -d ydun-scraper

            # Health checks
            echo ""
            echo "⏳ Waiting for container to start..."
            sleep 5

            echo "🏥 Running health check..."
            for i in {1..10}; do
              if curl -sf http://localhost:5000/health > /dev/null; then
                echo "✅ Health check passed (attempt $i)"
                break
              fi
              if [ $i -eq 10 ]; then
                echo "❌ Health check failed after 10 attempts"
                docker compose logs ydun-scraper | tail -20
                exit 1
              fi
              echo "Attempt $i/10..."
              sleep 2
            done

            # Verify
            echo ""
            echo "📊 Deployment verification:"
            docker compose ps ydun-scraper

            echo ""
            echo "========================================="
            echo "✨ Deployment Complete!"
            echo "========================================="

      - name: Deployment Status
        if: success()
        run: |
          echo "## ✅ Deployment Successful" >> $GITHUB_STEP_SUMMARY
          echo "- **Timestamp**: $(date)" >> $GITHUB_STEP_SUMMARY
          echo "- **Commit**: ${{ github.sha }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Environment**: production (Beast)" >> $GITHUB_STEP_SUMMARY
          echo "- **Status**: Running" >> $GITHUB_STEP_SUMMARY

      - name: Deployment Failed
        if: failure()
        run: |
          echo "## ❌ Deployment Failed" >> $GITHUB_STEP_SUMMARY
          echo "- **Timestamp**: $(date)" >> $GITHUB_STEP_SUMMARY
          echo "- **Commit**: ${{ github.sha }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Issue**: Check logs above for details" >> $GITHUB_STEP_SUMMARY
```

---

## Registry Options

### Option 1: GitHub Container Registry (Recommended)

**Pros:**
- No additional setup
- GitHub token already available
- Free for public images
- Integrated with GitHub UI
- Good storage limits

**Cons:**
- Slightly less mature than Docker Hub
- Limited to GitHub ecosystem

**Setup:**
```yaml
# In workflow
registry: ghcr.io
username: ${{ github.actor }}
password: ${{ secrets.GITHUB_TOKEN }}

# Image name format
ghcr.io/jimmyh-world/ydun-scraper:latest
```

**View Images:**
```
GitHub → ydun-scraper repo → Packages → Container registry
```

### Option 2: Docker Hub

**Pros:**
- Industry standard
- Large community
- Easy to pull from anywhere
- Good documentation

**Cons:**
- Requires separate account
- Rate limits for unauthenticated pulls
- Need to store credentials in GitHub secrets

**Setup:**
1. Create Docker Hub account
2. Create personal access token
3. Store in GitHub secrets:
   ```
   DOCKER_USERNAME=jimmyh
   DOCKER_PASSWORD=<access-token>
   ```

**Workflow config:**
```yaml
registry: docker.io
username: ${{ secrets.DOCKER_USERNAME }}
password: ${{ secrets.DOCKER_PASSWORD }}

# Image name format
jimmyh/ydun-scraper:latest
```

### Option 3: Self-Hosted Registry

**Pros:**
- Full control
- No external dependency
- Private by default

**Cons:**
- Requires server setup
- Additional maintenance
- SSL certificate management

**Not covered in this document** - requires separate Docker Registry setup.

---

## Deployment Integration

### Integration Point 1: Docker Compose Update

**File:** `~/network-infrastructure/beast/docker/docker-compose.yml`

**Current (Manual):**
```yaml
ydun-scraper:
  build:
    context: /home/jimmyb/ydun-scraper
    dockerfile: Dockerfile
  image: ydun-scraper:latest
  ports:
    - "5000:8080"
```

**After GitHub Actions (Automatic):**
```yaml
ydun-scraper:
  image: ghcr.io/jimmyh-world/ydun-scraper:latest
  ports:
    - "5000:8080"
  pull_policy: always  # Always pull latest image
  restart: unless-stopped
```

**Why the change:**
- Image comes from registry, not local build
- No local Dockerfile build needed
- `pull_policy: always` ensures latest version
- GitHub Actions controls the image

### Integration Point 2: Cloudflare Tunnel

No changes needed to Cloudflare configuration. Tunnel continues to:
```
External: https://scrape.kitt.agency/scrape
    ↓
Internal: localhost:5000/scrape
```

Deployment of new image doesn't affect tunnel routing.

### Integration Point 3: Health Checks

GitHub Actions deployment workflow includes health check:
```bash
curl -f http://localhost:5000/health
```

This validates:
- Container is running
- HTTP server is responding
- Application is healthy

---

## Monitoring & Validation

### Monitoring Dashboard

**GitHub Actions Dashboard:**
```
Repository → Actions → Recent Workflow Runs
```

Shows:
- Build status ✅/❌
- Deployment status ✅/❌
- Timing
- Logs
- Artifacts

### Deployment Logs

**View in GitHub:**
```
Actions → Deploy to Beast → Latest Run → Deploy via SSH
```

Shows:
```
📥 Pulling latest code...
✅ Code updated to: abc1234

🐳 Pulling Docker image...
✅ Image pulled successfully

🔄 Stopping current container...
✅ Health check passed

✨ Deployment Complete!
```

### Real-Time Monitoring

**Monitor during deployment:**
```bash
# SSH to Beast
ssh beast.local

# Watch logs
docker compose logs -f ydun-scraper

# Check stats
docker stats ydun-scraper

# Health check
curl http://localhost:5000/health
```

### Alerts & Notifications

**Option 1: GitHub Notifications**
- GitHub sends email on workflow failure
- Configured in: GitHub → Settings → Notifications

**Option 2: Slack Integration** (Optional)
```yaml
- name: Slack Notification
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Deployment ${{ job.status }}",
        "channel": "#deployments"
      }
```

---

## Troubleshooting

### Issue: "Failed to login to registry"

**Cause:** Invalid GitHub token or wrong credentials

**Solution:**
```bash
# Verify GitHub token has correct scopes
1. Go to GitHub → Settings → Developer settings
2. Check token has: repo, write:packages, read:packages
3. Regenerate if needed
4. Update DOCKER_PASSWORD secret in repo settings
```

### Issue: "SSH connection refused"

**Cause:** Wrong host, port, or SSH key

**Solution:**
```bash
# Test SSH manually
ssh -i ~/.ssh/id_rsa jimmyb@192.168.1.100 "echo OK"

# If fails:
1. Verify DEPLOY_HOST is correct
2. Verify SSH key is added to ~/.ssh/authorized_keys on Beast
3. Check SSH port (default 22)
```

### Issue: "Health check failed after deployment"

**Cause:** Container failed to start or application error

**Solution:**
```bash
# SSH to Beast and check logs
ssh beast.local
docker compose logs ydun-scraper -n 50

# Common issues:
# 1. Port already in use: lsof -i :5000
# 2. Invalid image: docker pull ghcr.io/jimmyh-world/ydun-scraper:latest
# 3. Missing dependencies: check requirements.txt
```

### Issue: "Workflow runs but doesn't deploy"

**Cause:** Workflow not triggered or condition not met

**Solution:**
```bash
# Check workflow configuration
1. Branch must be 'main' (not 'master')
2. Paths filter might exclude your changes
3. Permissions might be insufficient

# Debug:
- Add 'workflow_dispatch' trigger to run manually
- Check GitHub Actions logs
- Look for blue dots (skipped jobs)
```

---

## Rollback Procedures

### Manual Rollback (If Needed)

#### Option 1: Trigger Rollback Workflow

```
GitHub → Actions → Rollback Deployment → Run workflow
Input previous version number → Execute
```

#### Option 2: Manual SSH Rollback

```bash
ssh beast.local
cd ~/network-infrastructure/beast/docker

# View recent images
docker images | grep ydun-scraper

# Restore from backup
docker load < ydun-scraper-backup.tar

# Update docker-compose.yml
# Change image to: ydun-scraper:backup-1234567890

# Restart
docker compose up -d ydun-scraper

# Verify
curl http://localhost:5000/health
```

#### Option 3: Git Revert

```bash
ssh beast.local
cd ~/ydun-scraper

# Find problematic commit
git log --oneline -10

# Revert
git revert <commit-hash>
git push origin main

# GitHub Actions will automatically rebuild and redeploy
```

### Rollback Validation

After rollback, verify:

```bash
# Check version
curl http://localhost:5000/health

# Review logs
docker compose logs ydun-scraper | grep "Batch Complete"

# Test scraping
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
```

---

## Implementation Timeline

### Phase 1: Setup (1-2 hours)
- [ ] Create GitHub secrets (DEPLOY_HOST, DEPLOY_KEY, etc.)
- [ ] Create `.github/workflows/` directory
- [ ] Add `build-and-push.yml` workflow
- [ ] Add `deploy.yml` workflow
- [ ] Test SSH deployment manually

### Phase 2: Validation (1 hour)
- [ ] Trigger workflow manually (workflow_dispatch)
- [ ] Verify image builds and pushes
- [ ] Verify deployment to Beast
- [ ] Check health endpoint
- [ ] Verify monitoring works

### Phase 3: Production Ready (30 minutes)
- [ ] Document in DEPLOYMENT.md
- [ ] Create rollback procedure
- [ ] Test rollback process
- [ ] Brief team on new workflow
- [ ] Update incident procedures

### Phase 4: Optimization (Optional)
- [ ] Add Slack notifications
- [ ] Add more comprehensive tests
- [ ] Setup automated security scanning
- [ ] Add performance testing

---

## Quick Reference

### Files to Create

```
.github/
└── workflows/
    ├── build-and-push.yml    # Build Docker image
    ├── deploy.yml            # Deploy to Beast
    ├── test.yml              # Optional: Run tests
    └── rollback.yml          # Optional: Rollback trigger
```

### Environment Variables (Secrets)

```
DEPLOY_HOST          = 192.168.1.100
DEPLOY_USER          = jimmyb
DEPLOY_KEY           = <ssh private key>
DOCKER_USERNAME      = <github-username>
DOCKER_PASSWORD      = <github-token>
```

### Deployment Command

```bash
# No command needed - automatic on:
git push origin main

# Or manual trigger via GitHub UI:
# Actions → Deploy to Beast → Run workflow
```

### Monitoring

```
GitHub UI: Actions → Recent runs
Beast CLI: docker compose logs -f ydun-scraper
```

---

## Additional Resources

### GitHub Actions Documentation
- https://docs.github.com/en/actions
- Docker Build and Push: https://github.com/docker/build-push-action
- SSH Action: https://github.com/appleboy/ssh-action
- Container Registry: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry

### Docker Hub vs GHCR
- https://docs.docker.com/docker-hub/
- https://docs.github.com/en/packages/working-with-a-github-packages-registry

### Security Best Practices
- https://github.com/step-security/harden-runner
- https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

## Next Steps (When Ready to Implement)

1. **Review this document** with team
2. **Create GitHub secrets** (DEPLOY_HOST, DEPLOY_KEY, etc.)
3. **Create workflow files** (copy from examples above)
4. **Test manually** (use workflow_dispatch)
5. **Verify deployment** (curl health endpoint)
6. **Update DEPLOYMENT.md** with GitHub Actions info
7. **Brief team** on new automated workflow

---

## Notes

- **Current Status**: Not implemented (local deployment only)
- **Recommendation**: Implement after current setup is stable
- **Estimated Effort**: 2-3 hours for full setup
- **Risk**: Low - doesn't affect current local deployment
- **Benefit**: Automated, faster, more reliable deployments

---

**Document Created:** 2025-10-18
**Status:** Planning/Reference (Not Implemented)
**Current Deployment Method:** Local Docker Compose
**Suggested Implementation:** After current setup stabilizes

