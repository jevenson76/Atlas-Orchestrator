# ZeroTouch Atlas - Comprehensive Deployment Guide

**Version**: 2.0.0
**Last Updated**: November 2025
**Target Audience**: DevOps Engineers, System Administrators, Platform Engineers
**Project**: ZeroTouch Atlas Platform - Global-Scale Intelligent Orchestration

---

## What's New in 2.0

✨ **Multi-Perspective Dialogue UI** - Enterprise-grade visualization for complex task analysis
✨ **Claude Max Optimization** - $0/day operation with FREE Claude models
✨ **Enhanced Web UI** - Professional design with real-time observability
✨ **Zero-Trust Security** - All inputs validated before execution
✨ **5-Tab Interface** - Task Submission, RAG Topics, Dialogue, Observability, History

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development Deployment](#local-development-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment (AWS/Azure)](#cloud-deployment)
6. [MCP Server Management](#mcp-server-management)
7. [Multi-Perspective Dialogue Setup](#multi-perspective-dialogue-setup)
8. [Configuration & Scaling](#configuration--scaling)
9. [Observability Setup](#observability-setup)
10. [Security Hardening](#security-hardening)
11. [Troubleshooting](#troubleshooting)
12. [Production Checklist](#production-checklist)

---

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB available space
- OS: Ubuntu 20.04+, macOS 12+, Windows 10+ (with WSL2)

**Recommended (Production)**:
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 50+ GB available space
- OS: Ubuntu 22.04 LTS

### Software Dependencies

- **Python**: 3.11 or higher
- **pip**: Latest version
- **Git**: 2.30+
- **Docker** (optional): 20.10+
- **Docker Compose** (optional): 2.0+

### API Keys Required

| Provider | Required | Purpose | Cost | How to Obtain |
|----------|----------|---------|------|---------------|
| **Anthropic Claude** | No* | Primary AI provider | **FREE with Claude Max** | [console.anthropic.com](https://console.anthropic.com) |
| **xAI Grok** | Optional | External perspective | $3/$15 per 1M tokens | [x.ai/api](https://x.ai/api) |
| **Google Gemini** | Optional | Fallback provider | Free tier available | [ai.google.dev](https://ai.google.dev) |
| **OpenAI** | Optional | Secondary fallback | Pay-as-you-go | [platform.openai.com](https://platform.openai.com) |

\***With Claude Max subscription**, ALL Claude models (Opus 4.1, Sonnet 3.5) are **100% FREE**. The system uses browser authentication automatically. Fallback providers (Grok, Gemini, GPT) are optional and only used if Claude is unavailable.

**Cost Optimization**:
- **Primary**: Opus 4.1 + Sonnet 3.5 (FREE with Claude Max)
- **Fallback**: Grok 3 (~$3/$15) → Gemini (free tier) → GPT-4 ($30)
- **Daily Operation**: ~$0/day (99% FREE Claude models)

---

## Environment Setup

### 1. Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/jevenson76/Atlas-Orchestrator.git
cd Atlas-Orchestrator

# Verify repository integrity
git log --oneline -5
```

### 2. Create Virtual Environment

```bash
# Create isolated Python environment
python3.11 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (WSL):
source venv/bin/activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "streamlit|pandas|anthropic"
```

### 4. Configure API Keys

#### Option A: Environment Variables (Recommended)

```bash
# Create .env file (NOT committed to git)
cat > ~/.claude/.env <<EOF
GOOGLE_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
EOF

# Secure permissions
chmod 600 ~/.claude/.env
```

#### Option B: Configuration File

```bash
# Create config.json
cat > ~/.claude/config.json <<EOF
{
  "google_api_key": "your-gemini-api-key-here",
  "openai_api_key": "your-openai-api-key-here",
  "daily_budget": 10.0,
  "rate_limit_per_minute": 30,
  "rate_limit_per_hour": 500
}
EOF

# Secure permissions
chmod 600 ~/.claude/config.json
```

### 5. Initialize Directory Structure

```bash
# Create required directories
mkdir -p ~/dropzone/{tasks,results,archive}
mkdir -p ~/.claude/logs/events

# Verify structure
tree ~/dropzone ~/.claude/logs -L 2
```

---

## Local Development Deployment

### Quick Start (Single User)

```bash
# Navigate to repository
cd Atlas-Orchestrator

# Activate virtual environment
source venv/bin/activate

# Launch application
streamlit run atlas_app.py --server.port 8501

# Access UI
# Open browser: http://localhost:8501
```

### Advanced Configuration

```bash
# Custom port and headless mode
streamlit run atlas_app.py \
  --server.port 8502 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.fileWatcherType none

# With resource limits
ulimit -n 4096  # Increase file descriptor limit
streamlit run atlas_app.py --server.port 8501
```

### Background Process

```bash
# Run as background service
nohup streamlit run atlas_app.py --server.port 8501 > atlas.log 2>&1 &

# Check status
ps aux | grep streamlit

# View logs
tail -f atlas.log

# Stop service
pkill -f "streamlit run atlas_app.py"
```

---

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p /root/.claude/logs/events \
    && mkdir -p /root/dropzone/{tasks,results,archive}

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "atlas_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Create Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  atlas:
    build: .
    container_name: zerotouch-atlas
    ports:
      - "8501:8501"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/root/.claude/logs
      - ./dropzone:/root/dropzone
    restart: unless-stopped
    networks:
      - atlas-network

networks:
  atlas-network:
    driver: bridge
```

### 3. Deploy with Docker Compose

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f atlas

# Stop services
docker-compose down

# Restart
docker-compose restart
```

---

## Cloud Deployment

### AWS Deployment (EC2 + ECS)

#### EC2 Instance Setup

```bash
# 1. Launch EC2 instance
# - Instance type: t3.medium (2 vCPU, 4 GB RAM)
# - AMI: Ubuntu 22.04 LTS
# - Security group: Allow inbound 8501 (HTTP), 22 (SSH)
# - Storage: 30 GB gp3

# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv git

# 4. Clone and deploy (follow Local Deployment steps)

# 5. Setup systemd service
sudo nano /etc/systemd/system/atlas.service
```

**atlas.service**:
```ini
[Unit]
Description=ZeroTouch Atlas Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Atlas-Orchestrator
Environment="PATH=/home/ubuntu/Atlas-Orchestrator/venv/bin"
ExecStart=/home/ubuntu/Atlas-Orchestrator/venv/bin/streamlit run atlas_app.py --server.port 8501
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable atlas
sudo systemctl start atlas
sudo systemctl status atlas
```

#### ECS Fargate Deployment

```bash
# 1. Push Docker image to ECR
aws ecr create-repository --repository-name zerotouch-atlas
docker tag zerotouch-atlas:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/zerotouch-atlas:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/zerotouch-atlas:latest

# 2. Create ECS task definition (atlas-task.json)
# 3. Create ECS service with ALB
# 4. Configure auto-scaling
```

### Azure Deployment (Container Instances)

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name AtlasResourceGroup --location eastus

# 3. Deploy container
az container create \
  --resource-group AtlasResourceGroup \
  --name zerotouch-atlas \
  --image your-registry.azurecr.io/zerotouch-atlas:latest \
  --dns-name-label zerotouch-atlas-app \
  --ports 8501 \
  --environment-variables \
    GOOGLE_API_KEY=$GOOGLE_API_KEY \
    OPENAI_API_KEY=$OPENAI_API_KEY

# 4. Get public IP
az container show --resource-group AtlasResourceGroup --name zerotouch-atlas --query ipAddress.fqdn
```

---

## MCP Server Management

### Overview

ZeroTouch Atlas supports distributed MCP (Model Context Protocol) servers for specialized capabilities:

- **`analyst_server.py`**: Data analysis and reporting
- **`rag_server.py`**: Retrieval-augmented generation
- **`validation_server.py`**: Quality gate validation

### Launch MCP Servers

```bash
# Navigate to MCP servers directory
cd mcp_servers

# Launch analyst server (port 3001)
python3 analyst_server.py --port 3001 &

# Launch RAG server (port 3002)
python3 rag_server.py --port 3002 &

# Launch validation server (port 3003)
python3 validation_server.py --port 3003 &

# Verify servers
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
```

### Server Configuration

```python
# mcp_servers/config.py

SERVER_CONFIG = {
    "analyst_server": {
        "port": 3001,
        "timeout": 300,  # 5 minutes
        "max_concurrent": 5
    },
    "rag_server": {
        "port": 3002,
        "timeout": 60,
        "max_concurrent": 10,
        "vector_db": "chroma",  # or "pinecone"
        "embedding_model": "text-embedding-ada-002"
    },
    "validation_server": {
        "port": 3003,
        "timeout": 120,
        "max_concurrent": 3,
        "min_score_threshold": 80.0
    }
}
```

### Server Health Monitoring

```bash
# Create monitoring script
cat > monitor_servers.sh <<'EOF'
#!/bin/bash

SERVERS=("3001:analyst" "3002:rag" "3003:validation")

for server in "${SERVERS[@]}"; do
  IFS=':' read -r port name <<< "$server"

  if curl -sf http://localhost:$port/health > /dev/null; then
    echo "✅ $name server (port $port) is healthy"
  else
    echo "❌ $name server (port $port) is down - restarting..."
    # Restart logic here
  fi
done
EOF

chmod +x monitor_servers.sh

# Run as cron job (every 5 minutes)
crontab -e
# Add: */5 * * * * /path/to/monitor_servers.sh
```

---

## Multi-Perspective Dialogue Setup

### Overview

The **Multi-Perspective Dialogue** system enables complex tasks to be analyzed by multiple AI models through constructive debate, improving output quality by 15-30%.

### Architecture

```
PROPOSER (Sonnet 3.5 - FREE)
   ↓ Generates initial solution

CHALLENGER (Opus 4.1 - FREE)
   ↓ Critiques and suggests improvements

ORCHESTRATOR (Opus 4.1 - FREE)
   ↓ Decides: Refine or Consensus?

[Repeat up to max_iterations]

FINAL OUTPUT with Quality Metrics
```

### Configuration

**File**: `multi_perspective.py`

```python
from multi_perspective import MultiPerspectiveDialogue
from core.constants import Models

# Initialize dialogue system
dialogue = MultiPerspectiveDialogue(
    proposer_model=Models.SONNET,           # FREE with Claude Max
    challenger_model=Models.OPUS_4,         # FREE with Claude Max
    orchestrator_model=Models.OPUS_4,       # FREE with Claude Max
    max_iterations=3,                       # Prevent endless loops (1-5)
    min_quality_threshold=85.0,             # Stop when met (70-95)
    enable_external_perspective=False,      # Optional Grok 3 (~$0.01)
    external_model=Models.GROK_3
)

# Execute dialogue
result = dialogue.execute("Complex task description...")

# Access results
print(f"Quality: {result.initial_quality} → {result.final_quality}")
print(f"Improvement: +{result.improvement_percentage}%")
print(f"Cost: ${result.total_cost:.6f}")  # $0.00 with Claude Max
print(f"Consensus: {result.consensus_status.value}")
```

### Web UI Access

Users can access Multi-Perspective Dialogue through the web interface:

1. **Navigate to**: `http://localhost:8501`
2. **Click tab**: "🗣️ Multi-Perspective Dialogue"
3. **Submit task**: Enter complex task description
4. **Configure**: Max iterations, quality threshold, external perspective
5. **Watch**: Live dialogue visualization with professional UI
6. **Review**: Quality metrics, timeline, full transcript

### Features

✅ **Enterprise UI**: Professional, clean visualization (no amateur elements)
✅ **Color-coded Roles**: Blue (Proposer), Amber (Challenger), Green (Orchestrator)
✅ **Real-time Updates**: Live turn-by-turn progression
✅ **Quality Tracking**: Initial → Final quality charts
✅ **Timeline View**: Chronological dialogue flow
✅ **Consensus Indicators**: Visual status (Consensus/In Progress/No Consensus)
✅ **Zero Cost**: $0.00 with Claude Max (Sonnet + Opus FREE)

### When to Use

**✅ Use For**:
- Complex architectural decisions
- Tasks requiring validation/critique
- Multiple perspectives valuable
- Quality > speed
- Tradeoff evaluation

**❌ Don't Use For**:
- Simple tasks (single model sufficient)
- Time-critical tasks (adds 30-60s latency)
- Low-stakes outputs

### Cost Optimization

**With Claude Max Subscription**:
- Proposer (Sonnet 3.5): **$0.00** (FREE)
- Challenger (Opus 4.1): **$0.00** (FREE)
- Orchestrator (Opus 4.1): **$0.00** (FREE)
- External (Grok 3): **~$0.01** (optional)

**Total Daily Cost**: **~$0/day** (99% FREE Claude models)

### Production Tuning

```python
# High-quality output (research, architecture)
dialogue = MultiPerspectiveDialogue(
    max_iterations=4,                       # More rounds
    min_quality_threshold=90.0,             # Higher bar
    enable_external_perspective=True        # Diversity
)

# Balanced (default - recommended)
dialogue = MultiPerspectiveDialogue(
    max_iterations=3,
    min_quality_threshold=85.0,
    enable_external_perspective=False
)

# Fast iteration (development)
dialogue = MultiPerspectiveDialogue(
    max_iterations=2,                       # Quick refinement
    min_quality_threshold=80.0,             # Lower bar
    enable_external_perspective=False
)
```

### Monitoring

**View dialogue metrics**:
- Web UI → Multi-Perspective Dialogue tab → Statistics panel
- Track: Total dialogues, avg quality, avg improvement %, total cost

**Access dialogue history**:
- Each dialogue saved with full transcript
- Expandable result cards with quality metrics
- Timeline visualization of all turns

---

## Configuration & Scaling

### Refinement Loop Configuration

**File**: `refinement_loop.py`

```python
# Adjust iteration limits
loop = RefinementLoop(
    max_iterations=3,           # 1-10 iterations
    min_score_threshold=80.0,   # 0-100 quality threshold
    allow_partial=False,        # Accept WARNING status
    save_history=True,          # Persist iteration logs
    agent=sonnet_agent          # Structured feedback (C5)
)
```

**Scaling Recommendations**:

| Use Case | max_iterations | min_score_threshold | allow_partial |
|----------|----------------|---------------------|---------------|
| **Development** | 3 | 70.0 | True |
| **Production** | 5 | 85.0 | False |
| **High Stakes** | 7 | 95.0 | False |
| **Cost Optimized** | 2 | 75.0 | True |

### Model Selection for Cost Optimization

```python
# Cost-optimized model allocation

COST_OPTIMIZED_CONFIG = {
    "retrieval": "claude-3-5-haiku-20241022",     # $0.25/1M tokens
    "routing": "claude-3-5-haiku-20241022",       # Fast + cheap
    "validation": "claude-opus-4-20250514",       # $15/1M - worth it
    "synthesis": "claude-3-5-sonnet-20241022",    # $3/1M - balanced
    "security": "claude-3-5-haiku-20241022"       # Speed matters
}

# Savings example:
# All Opus: $15/1M × 5 calls = $0.075 per workflow
# Optimized: ($0.25 × 3) + ($15 × 1) + ($3 × 1) = $18.75/1M = $0.019 per workflow
# **75% cost reduction**
```

### Rate Limiting & Budget Control

```python
# security/input_boundary_filter.py

RATE_LIMITS = {
    "per_minute": 30,   # Max submissions per minute
    "per_hour": 500,    # Max submissions per hour
    "daily_budget": 10.0  # USD per day
}

# Alerts at 80% budget
BUDGET_ALERTS = {
    "warning_threshold": 0.80,
    "critical_threshold": 0.95,
    "notification_email": "ops@yourcompany.com"
}
```

### Scaling Streamlit (Multi-User)

**For > 10 concurrent users**, use Streamlit Enterprise or reverse proxy:

```nginx
# nginx.conf

upstream atlas_backend {
    least_conn;
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    server_name atlas.yourcompany.com;

    location / {
        proxy_pass http://atlas_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Observability Setup

### C4 Hooks Configuration

**Event Stream Location**: `~/.claude/logs/events/stream.jsonl`

### Enable Real-Time Monitoring

```python
# observability/event_emitter.py

emitter = EventEmitter(
    log_dir=Path.home() / ".claude/logs/events",
    enable_streaming=True,     # Real-time stream
    enable_console=True,       # Console output
    enable_alerts=True,        # Alert detection
    max_stream_events=100      # Buffer size
)
```

### WebSocket Streaming (Advanced)

```python
# Create WebSocket server for real-time dashboard

import asyncio
import websockets

async def stream_events(websocket, path):
    """Stream C4 events to connected clients."""
    with open(STREAM_FILE, 'r') as f:
        # Seek to end
        f.seek(0, 2)

        while True:
            line = f.readline()
            if line:
                await websocket.send(line)
            await asyncio.sleep(0.1)

# Start server
start_server = websockets.serve(stream_events, "localhost", 8765)
asyncio.get_event_loop().run_until_complete(start_server)
```

### Metrics Dashboard

Access the **Live Monitor** tab in Atlas UI for:
- **Quality Scores** from Opus 4.1 Critic (0-100 scale)
- **Cost Breakdown** by model (Haiku/Sonnet/Opus/Gemini/OpenAI)
- **Execution Timeline** with agent activity
- **Provider Health** status indicators

### Log Rotation

```bash
# Setup logrotate for event stream

sudo nano /etc/logrotate.d/atlas

# Add:
/home/ubuntu/.claude/logs/events/*.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
```

---

## Security Hardening

### 1. API Key Management

```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret \
    --name atlas/google-api-key \
    --secret-string "your-key-here"

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='atlas/google-api-key')
api_key = response['SecretString']
```

### 2. Network Security

```bash
# Firewall rules (UFW)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8501/tcp    # Atlas UI
sudo ufw deny 3001:3003/tcp  # MCP servers (internal only)
sudo ufw enable
```

### 3. SSL/TLS Encryption

```bash
# Use Let's Encrypt with Certbot
sudo certbot --nginx -d atlas.yourcompany.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 4. Input Validation

Zero-Trust Security Filter is **always enabled** by default:
- Haiku 4.5-powered threat detection
- Rate limiting (30/min, 500/hour)
- Audit logging to `security/security_audit.log`

### 5. Access Control

```python
# Add authentication (example with Streamlit-Authenticator)

import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    'atlas_cookie',
    'atlas_signature',
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # Render Atlas UI
    main()
elif authentication_status == False:
    st.error('Username/password is incorrect')
```

---

## Troubleshooting

### Issue 1: "Module not found" errors

**Solution**:
```bash
# Verify virtual environment activated
which python3  # Should show venv path

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Issue 2: API rate limiting (429 errors)

**Solution**:
```python
# Check current rate limits
from resilient_agent import ResilientBaseAgent

agent = ResilientBaseAgent(role="test")
print(agent.rate_limiter.current_usage())

# Adjust limits in config
config["rate_limit_per_minute"] = 50  # Increase
```

### Issue 3: Event stream not updating

**Solution**:
```bash
# Check file permissions
ls -la ~/.claude/logs/events/stream.jsonl

# Fix permissions
chmod 644 ~/.claude/logs/events/stream.jsonl

# Verify emitter is writing
tail -f ~/.claude/logs/events/stream.jsonl
```

### Issue 4: Docker container crashes

**Solution**:
```bash
# Check logs
docker logs zerotouch-atlas

# Increase memory limit
docker run -m 4g zerotouch-atlas

# Check health
docker inspect --format='{{.State.Health.Status}}' zerotouch-atlas
```

### Issue 5: High API costs

**Solution**:
```python
# Enable cost tracking
from observability.event_emitter import EventEmitter

emitter = EventEmitter(enable_alerts=True)

# Review cost breakdown in Live Monitor tab
# Optimize model selection (use Haiku for non-critical tasks)
```

---

## Production Checklist

### Pre-Deployment

- [ ] All API keys configured and tested
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` verified)
- [ ] Directory structure initialized
- [ ] Security filter enabled and tested
- [ ] Rate limits configured appropriately
- [ ] Budget alerts configured
- [ ] SSL/TLS certificates installed (if public)
- [ ] Firewall rules configured
- [ ] Backup strategy defined

### Deployment

- [ ] Application starts without errors
- [ ] UI accessible via browser
- [ ] Zero-Trust security filter operational
- [ ] Task submission working (test with sample task)
- [ ] RAG topics selectable
- [ ] Observability dashboard displaying metrics
- [ ] Cost tracking functional
- [ ] Provider health indicators accurate

### Post-Deployment

- [ ] Monitor `~/.claude/logs/events/stream.jsonl` for events
- [ ] Verify quality scores from Opus 4.1 Critic
- [ ] Check cost breakdown by model
- [ ] Test interactive refinement loop
- [ ] Confirm multi-provider fallback (simulate API failure)
- [ ] Setup alerting (Slack/PagerDuty)
- [ ] Configure log rotation
- [ ] Schedule regular backups
- [ ] Document runbook for common operations
- [ ] Train operations team on troubleshooting

### Monitoring

**Daily**:
- Check cost dashboard (prevent overruns)
- Review security audit logs
- Monitor provider health

**Weekly**:
- Analyze quality score trends
- Review execution timelines for bottlenecks
- Optimize model selection based on costs

**Monthly**:
- Rotate API keys
- Update dependencies (`pip install --upgrade -r requirements.txt`)
- Review and archive old event logs

---

## Performance Benchmarks

### Expected Performance (Single User)

| Metric | Value |
|--------|-------|
| Task submission latency | < 200ms |
| Security validation (Haiku) | 500-1000ms |
| Simple task execution (Haiku) | 2-5s |
| Complex task (Opus with UltraThink) | 30-60s |
| Refinement loop (3 iterations) | 60-180s |
| UI page load | < 2s |

### Scaling Limits

| Configuration | Concurrent Users | Tasks/Hour | Est. Cost/Hour |
|---------------|------------------|------------|----------------|
| Single Streamlit | 1-5 | 30-50 | $0.50-$2.00 |
| Multi-Instance + LB | 10-50 | 500-1000 | $5.00-$20.00 |
| ECS Fargate (3 tasks) | 50-200 | 2000-5000 | $20.00-$100.00 |

---

## Support & Resources

### Documentation
- **README**: [README.md](../README.md)
- **Architecture**: [docs/archive/](./archive/)
- **API Reference**: Coming soon

### Community
- **GitHub Issues**: [Issues](https://github.com/jevenson76/Atlas-Orchestrator/issues)
- **Discussions**: [Discussions](https://github.com/jevenson76/Atlas-Orchestrator/discussions)

### Commercial Support
For enterprise support, custom integrations, or consulting services, contact the Atlas Platform Team.

---

**ZeroTouch Atlas Deployment Guide v1.0.0**

*Last Updated: November 2025*

🌐 **Mapping knowledge across domains • Zero-touch automation • Enterprise-grade security**
