# 🌐 ZeroTouch Atlas

**Global-Scale Intelligent Multi-Agent Orchestration Platform**

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*Mapping knowledge across domains • Zero-touch automation • Enterprise-grade security*

[Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

**ZeroTouch Atlas** is a production-ready, enterprise-grade orchestration platform that coordinates multiple AI agents across providers (Anthropic, xAI, Google, OpenAI) with zero-trust security, intelligent routing, and real-time observability.

Named after the Titan who held the celestial spheres, **Atlas** represents global knowledge mapping—connecting and orchestrating intelligence across all domains with the same effortless precision.

### Why Atlas?

Traditional multi-agent systems require extensive configuration, lack security boundaries, and provide limited visibility into execution. **Atlas** solves these challenges:

- **🛡️ Zero-Trust Security**: Every input validated by Claude Haiku 4.5 before execution
- **🌐 Global Intelligence**: RAG topic routing optimizes queries across knowledge domains
- **📊 Real-Time Observability**: C4 hooks provide complete execution visibility with model attribution
- **🔄 Closed-Loop Validation**: Automatic UltraThink enforcement for Opus models in validation roles
- **⚡ Multi-Provider Resilience**: Seamless fallback across Anthropic, xAI (Grok), Gemini, and OpenAI
- **📥 Zero-Touch Workflow**: Drag-and-drop task submission with automatic orchestration

---

## ✨ Key Features

### 1. **Zero-Trust Input Boundary** 🛡️

Every task submission passes through a Haiku 4.5-powered security filter that detects:
- Prompt injection attacks
- SQL/XSS injection attempts
- Credential exposure
- Path traversal exploits
- Malicious code execution

**Rate limiting** (30/min, 500/hour) prevents abuse while maintaining performance.

### 2. **Agentic Drop Zone (ADZ)** 📥

Modern drag-and-drop interface with:
- Polished CSS animations and micro-interactions
- Automatic file validation and parsing
- Security-first task routing
- Support for JSON, YAML, TXT, MD formats

### 3. **RAG Topic Management** 🎯

Optimize retrieval with topic-based routing:
- 8 pre-defined knowledge domains
- Metadata-constrained search (80% scope reduction)
- Topic-optimized routing strategies
- 60-70% latency improvement

**Topics**: Medical & Healthcare, Automotive, Financial & Legal, Technology, Education, Business, Science, General Knowledge

### 4. **Multi-Agent Observability** 📊

Real-time C4 hooks provide:
- Event streaming from all agents
- Model and provider attribution
- Execution timeline visualization
- Error tracking and debugging

### 5. **UltraThink Enforcement** 🧠

Automatic injection of extended reasoning for:
- Opus 3 and Opus 4.1 models
- Validation/critic/judge/reviewer roles
- Self-reflection in RAG pipeline
- Quality assessment workflows

**Zero configuration required** - enforcement is automatic based on model and role detection.

### 6. **Multi-Provider Architecture** 🌐

Resilient fallback chain:
```
Claude (Anthropic) → Grok (xAI) → Gemini (Google) → GPT (OpenAI)
```

Supported providers:
- **Anthropic**: Claude 3 Haiku, Sonnet, Opus, Opus 4.1
- **xAI**: Grok Beta, Grok 2, Grok 2 Vision
- **Google**: Gemini Pro
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo

Features:
- Circuit breakers prevent cascade failures
- Automatic provider selection
- Cost tracking across providers
- Daily budget enforcement

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- API keys (optional - works with Claude Max subscription):
  - `XAI_API_KEY` (Grok)
  - `GOOGLE_API_KEY` (Gemini)
  - `OPENAI_API_KEY` (GPT)

### Installation

```bash
# Clone the repository
git clone https://github.com/jevenson76/Atlas-Orchestrator.git
cd Atlas-Orchestrator

# Install dependencies
pip install -r requirements.txt

# Configure API keys (optional)
echo "XAI_API_KEY=your-key" >> ~/.claude/config.json
echo "GOOGLE_API_KEY=your-key" >> ~/.claude/config.json
echo "OPENAI_API_KEY=your-key" >> ~/.claude/config.json
```

### Launch Atlas

```bash
streamlit run atlas_app.py --server.port 8501
```

Navigate to **http://localhost:8501**

### Your First Task

1. **Select RAG Topics** (optional): Click topic pills in the RAG Topics tab
2. **Submit via Drop Zone**: Drag a task file or click to browse
3. **Or use Manual Builder**: Fill in task description, model, temperature
4. **Monitor Execution**: Watch real-time events in Observability tab
5. **View History**: Check submitted tasks and results

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZeroTouch Atlas Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐          ┌──────────────────┐             │
│  │   Atlas Web UI  │          │  Security Filter │             │
│  │   (Streamlit)   │─────────▶│  (Haiku 4.5)    │             │
│  │                 │          │                  │             │
│  │ • Drag & Drop   │          │ • Zero-Trust     │             │
│  │ • RAG Topics    │          │ • Rate Limiting  │             │
│  │ • Observability │          │ • Threat Detection│            │
│  └─────────────────┘          └────────┬─────────┘             │
│                                         │                        │
│                                         ▼                        │
│                        ┌─────────────────────────┐              │
│                        │  Master Orchestrator    │              │
│                        │                         │              │
│                        │ • Task Routing          │              │
│                        │ • Workflow Selection    │              │
│                        │ • Agent Coordination    │              │
│                        └───────────┬─────────────┘              │
│                                    │                             │
│          ┌─────────────────────────┼──────────────────────┐     │
│          │                         │                      │     │
│          ▼                         ▼                      ▼     │
│  ┌──────────────┐         ┌──────────────┐      ┌──────────────┐
│  │ Claude Max   │         │ Gemini API   │      │ OpenAI API   │
│  │ (Opus/Sonnet)│         │ (Fallback 1) │      │ (Fallback 2) │
│  └──────────────┘         └──────────────┘      └──────────────┘
│          │                         │                      │     │
│          └─────────────────────────┴──────────────────────┘     │
│                                    │                             │
│                                    ▼                             │
│                    ┌────────────────────────────┐               │
│                    │  Agentic RAG Pipeline      │               │
│                    │                            │               │
│                    │ 1. Routing (Haiku)         │               │
│                    │ 2. Retrieval (Multi-Source)│               │
│                    │ 3. Validation (Opus 4.1)   │               │
│                    │ 4. Synthesis (Sonnet)      │               │
│                    └────────────────────────────┘               │
│                                    │                             │
│                                    ▼                             │
│                    ┌────────────────────────────┐               │
│                    │  Validation Orchestrator   │               │
│                    │  (UltraThink Enforcement)  │               │
│                    └────────────────────────────┘               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Stack

| Layer | Component | Technology | Purpose |
|-------|-----------|------------|---------|
| **UI** | Atlas Web App | Streamlit | User interface, drag-and-drop, RAG topics |
| **Security** | Input Boundary Filter | Claude Haiku 4.5 | Zero-trust validation, threat detection |
| **Orchestration** | Master Orchestrator | Python | Task routing, workflow selection |
| **Execution** | Resilient Agent | Multi-provider | API calls with fallback and retries |
| **Intelligence** | RAG Pipeline | 4-step workflow | Routing → Retrieval → Validation → Synthesis |
| **Quality** | Validation Orchestrator | Opus 4.1 (UltraThink) | Closed-loop validation |
| **Observability** | C4 Hooks | Event streaming | Real-time monitoring, tracing |

### Workflow Modes

Atlas supports 4 execution modes:

1. **Automatic** 🤖: Atlas selects optimal workflow based on task complexity
2. **Specialized Roles** 👥: 4-phase workflow (Architect → Developer → Tester → Reviewer)
3. **Parallel Execution** ⚡: Concurrent multi-component processing
4. **Progressive Enhancement** 📈: Iterative refinement (Simple → Advanced)

---

## 📚 Core Components

### ResilientBaseAgent

Foundation for all agents with:
- Multi-provider fallback (Anthropic → Gemini → OpenAI)
- Circuit breakers (threshold: 5 failures, timeout: 30s)
- Automatic retries with exponential backoff
- Cost tracking with daily budgets
- Security validation (input sanitization, scope checking)

**UltraThink Auto-Injection**: Automatically prepends `ultrathink` keyword for Opus models in validation roles.

### Security Module

**Input Boundary Filter** (`security/input_boundary_filter.py`):
- Pattern-based pre-screening (credentials, injections)
- AI-powered threat analysis (Haiku 4.5)
- Rate limiting per source
- Security audit logging
- Sanitized output generation

### Agentic RAG Pipeline

**4-Step Workflow**:
1. **Routing** (Haiku): Classify query intent and select retrieval strategy
2. **Retrieval**: Multi-source search with topic filtering
3. **Validation** (Opus 4.1 + UltraThink): Self-reflection and quality check
4. **Synthesis** (Sonnet): Generate final response

**Topic Optimization**: Constrains search to selected domains, reducing scope by 80%.

### Validation Orchestrator

**Closed-Loop Validation**:
- Opus 4.1 with automatic UltraThink enforcement
- Multi-round refinement loops
- Quality scoring and threshold enforcement
- Detailed critique generation

### Observability System

**C4 Hooks** (Contextual, Continuous, Comprehensive Coverage):
- Event emitters in all agents
- Distributed tracing
- Real-time event streaming to `~/.claude/logs/events/stream.jsonl`
- Model and provider attribution

---

## 🔧 Configuration

### Environment Variables

```bash
# Optional - Atlas works with Claude Max subscription
GOOGLE_API_KEY=your-gemini-key      # Gemini fallback
OPENAI_API_KEY=your-openai-key      # OpenAI fallback

# Configuration file location
~/.claude/config.json
```

### Configuration File Format

```json
{
  "google_api_key": "your-key",
  "openai_api_key": "your-key",
  "daily_budget": 10.0,
  "rate_limit_per_minute": 30,
  "rate_limit_per_hour": 500
}
```

### Directory Structure

```
~/.claude/
├── lib/                      # Atlas platform code
│   ├── atlas_app.py         # Main application
│   ├── resilient_agent.py   # Base agent with fallback
│   ├── security/            # Security module
│   ├── observability/       # C4 hooks
│   ├── core/                # Constants and utilities
│   └── mcp_servers/         # MCP server implementations
├── logs/                     # Execution logs
│   └── events/              # Observability event stream
└── config.json              # Configuration

~/dropzone/                   # Task submission
├── tasks/                    # Incoming tasks
├── results/                  # Completed results
└── archive/                  # Historical tasks
```

---

## 🛡️ Security

### Zero-Trust Architecture

**Every input is untrusted until validated** by the Input Boundary Filter:

1. **Pattern Screening**: Fast regex-based detection of known threats
2. **AI Analysis**: Claude Haiku 4.5 performs deep threat analysis
3. **Rate Limiting**: Prevents DoS via excessive submissions
4. **Audit Logging**: All security events logged to `security/security_audit.log`

### Threat Detection

The security filter detects:
- **Prompt Injection**: Attempts to manipulate LLM behavior
- **SQL Injection**: Malicious SQL patterns
- **XSS**: Script injection attempts
- **Path Traversal**: Unauthorized file access attempts
- **Credential Exposure**: Accidental API key inclusion
- **Code Injection**: Arbitrary code execution attempts

### Security Best Practices

1. ✅ **Enable Security Filter**: Always keep `Zero-Trust Security Filter` enabled in UI
2. ✅ **Review Audit Logs**: Monitor `security/security_audit.log` regularly
3. ✅ **Rate Limiting**: Adjust limits based on usage patterns
4. ✅ **API Key Security**: Store keys in `~/.claude/config.json` (not in code)
5. ✅ **Update Dependencies**: Keep security-critical packages current

---

## 🧪 Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/jevenson76/Atlas-Orchestrator.git
cd Atlas-Orchestrator
pip install -r requirements.txt

# Install development dependencies
pip install pytest black ruff mypy

# Run tests
pytest tests/ -v --cov

# Format code
black .
ruff check .
```

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_security.py -v

# With coverage
pytest --cov=. --cov-report=html
```

### Code Style

- **Formatter**: Black (line length: 88)
- **Linter**: Ruff
- **Type Checking**: mypy (when enabled)
- **Docstrings**: Google style

---

## 📖 Documentation

### Main Documentation

- **[Atlas App Documentation](docs/archive/ZTE_APP_DOCUMENTATION.md)**: Comprehensive UI guide
- **[Security Guide](security/README.md)**: Security architecture and best practices
- **[RAG Pipeline](docs/RAG_PIPELINE.md)**: Agentic RAG implementation details
- **[Observability](docs/archive/OBSERVABILITY_README.md)**: C4 hooks and monitoring
- **[Phase D Completion](docs/archive/PHASE_D_COMPLETION_REPORT.md)**: Final deployment report

### API Reference

Coming soon: Full API documentation for programmatic access.

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Contribution Process

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** with clear, descriptive commits
4. **Add tests** for new functionality
5. **Run linters**: `black . && ruff check .`
6. **Submit a Pull Request** with detailed description

### Code Review Criteria

- ✅ Tests pass and coverage maintained
- ✅ Code follows style guidelines (Black + Ruff)
- ✅ Security considerations documented
- ✅ Performance impact assessed
- ✅ Documentation updated

### Areas for Contribution

- 🐛 **Bug Fixes**: Report and fix issues
- ✨ **New Features**: Additional orchestration modes, integrations
- 📚 **Documentation**: Improve guides, add examples
- 🧪 **Testing**: Increase coverage, add integration tests
- 🎨 **UI/UX**: Enhance interface, add visualizations

---

## 🗺️ Roadmap

### Phase E (Planned)

- [ ] **Real-Time Dashboard**: WebSocket integration with C4 observability
- [ ] **Advanced RAG**: Hybrid search, automatic topic detection
- [ ] **Multi-User Support**: Authentication, session management, task queues
- [ ] **Cost Analytics**: Real-time tracking, budget alerts, per-task analysis
- [ ] **Custom Workflows**: Visual workflow builder
- [ ] **API Gateway**: RESTful API for programmatic access

### Phase F (Future)

- [ ] **Enterprise Features**: SSO, RBAC, audit trails
- [ ] **Scaling**: Kubernetes deployment, horizontal scaling
- [ ] **Advanced Security**: Anomaly detection, behavior analysis
- [ ] **Intelligence Layer**: Meta-learning, workflow optimization

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

### Built With

- **[Anthropic Claude](https://www.anthropic.com/)**: Opus, Sonnet, and Haiku models
- **[xAI Grok](https://x.ai/)**: Grok models for additional reasoning capabilities
- **[Streamlit](https://streamlit.io/)**: Web application framework
- **[Google Gemini](https://deepmind.google/technologies/gemini/)**: Multi-provider fallback
- **[OpenAI](https://openai.com/)**: GPT models for additional coverage

### Inspiration

- **Model Context Protocol (MCP)**: Anthropic's specification for agent capabilities
- **Zero-Trust Architecture**: Google BeyondCorp security principles
- **Agentic Workflows**: LangChain and AutoGPT patterns

---

## 📞 Support

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/jevenson76/Atlas-Orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jevenson76/Atlas-Orchestrator/discussions)
- **Documentation**: See [docs/](docs/) directory

### Reporting Security Issues

Please report security vulnerabilities to the maintainers privately. Do not create public issues for security problems.

---

<div align="center">

**ZeroTouch Atlas** v1.0.0

*Mapping knowledge across domains • Zero-touch automation • Enterprise-grade security*

Made with 🌐 by the Atlas Platform Team

[⬆ Back to Top](#-zerotouch-atlas)

</div>
