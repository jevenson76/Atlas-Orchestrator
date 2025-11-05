# Enterprise Analyst MCP Server - Documentation

**Version:** 1.0.0
**Date:** November 5, 2025
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Pipeline Workflow](#pipeline-workflow)
6. [Output Styles](#output-styles)
7. [MCP Integration](#mcp-integration)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)

---

## Overview

The **Enterprise Analyst MCP Server** is a production-ready implementation that leverages the complete **Zero-Touch Engineering (ZTE) Platform** to generate validated, structured enterprise analyst reports from external data sources.

### Key Features

- ✅ **Complete ZTE Pipeline Integration**: Phase B (infrastructure) + Priority 2 (validation) + C5 (output styles)
- ✅ **Deterministic Output Control**: Structured JSON reports with 100% schema compliance
- ✅ **Multi-Model Orchestration**: Haiku 3.5 for retrieval, Sonnet 4.5 for generation, Opus 4 for validation
- ✅ **Closed-Loop Validation**: Automatic refinement until validation passes
- ✅ **MCP Protocol Integration**: Standardized interface for external tool access
- ✅ **Enterprise-Grade Output**: Executive summaries, detailed analysis, evidence citations, actionable recommendations

### Use Cases

- **Security Compliance Analysis**: Analyze security policies, audit logs, and compliance documentation
- **Enterprise Risk Assessment**: Evaluate risk factors across organizational data sources
- **Document Intelligence**: Extract insights and generate structured reports from unstructured data
- **Regulatory Compliance**: Generate compliance reports with evidence citations and recommendations
- **Strategic Analysis**: Analyze business data and generate executive-ready reports

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enterprise Analyst MCP Server                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EnterpriseAnalyst Orchestrator                  │
│  Coordinates 5-step ZTE pipeline for report generation           │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐      ┌──────────────┐    ┌──────────────┐
    │  Scout   │      │    Master    │    │  Validation  │
    │  Agent   │      │ Orchestrator │    │ Orchestrator │
    │ (Haiku)  │      │  (Sonnet)    │    │   (Opus)     │
    └──────────┘      └──────────────┘    └──────────────┘
         │                    │                    │
         │                    │                    ▼
         │                    │            ┌──────────────┐
         │                    │            │  Refinement  │
         │                    │            │     Loop     │
         │                    │            │  (Sonnet)    │
         │                    │            └──────────────┘
         ▼                    ▼
    ┌──────────┐      ┌──────────────┐
    │   RAG    │      │    Output    │
    │  System  │      │    Styles    │
    │          │      │   Manager    │
    └──────────┘      └──────────────┘
```

### Model Stack Mandate

| Phase | Model | Purpose | Temperature | Output Style |
|-------|-------|---------|-------------|--------------|
| **Retrieval** | Haiku 3.5 | Fast context retrieval via RAG | 0.3 | None (raw context) |
| **Generation** | Sonnet 4.5 | Report generation with structure | 0.5 | `analyst` (strict JSON) |
| **Validation** | Opus 4 | Critical validation and judgment | 0.0 | `critic_judge` (strict JSON) |
| **Refinement** | Sonnet 4.5 | Structured feedback extraction | 0.2 | `refinement_feedback` (YAML) |

### ZTE Platform Components

**Phase B: Multi-Provider Infrastructure**
- `ResilientBaseAgent`: Multi-provider agent with fallback, circuit breakers, cost tracking
- `APIConfig`: Multi-provider API configuration (Anthropic, Google, OpenAI)
- `Constants.Models`: Standard model identifiers with enforcement

**Priority 2: Closed-Loop Validation**
- `ValidationOrchestrator`: Coordinates validation across code/docs/tests
- `RefinementLoop`: Closed-loop self-correction system with iterative feedback
- `ValidationReport`: Structured validation results with findings and scores

**C5: Output Styles System**
- `OutputStylesManager`: Central utility for loading and applying output styles
- `analyst.md`: Structured JSON schema for enterprise reports
- `critic_judge.md`: Strict JSON validation schema
- `refinement_feedback.md`: Structured YAML feedback schema

---

## Installation

### Prerequisites

```bash
# Python 3.11+
python3 --version

# Install dependencies
pip install anthropic python-dotenv pydantic chromadb sentence-transformers
```

### Setup

```bash
# Clone or navigate to ZTE library
cd /home/jevenson/.claude/lib

# Verify file structure
ls -la output_styles/analyst.md
ls -la enterprise_analyst.py
ls -la mcp_servers/analyst_server.py
ls -la test_enterprise_analyst.py

# Create output directory
mkdir -p reports

# (Optional) Initialize RAG system
# Configure your vector database and document ingestion
```

### Environment Configuration

```bash
# ~/.env or project .env
# Note: Claude Code uses browser authentication by default
# Only needed for direct Python SDK usage

# Optional: For alternative providers
GOOGLE_API_KEY=your-google-key
OPENAI_API_KEY=your-openai-key
```

---

## Usage

### Quick Start: Command Line

```bash
# Direct usage (convenience function)
python3 enterprise_analyst.py \
  "/path/to/data/source" \
  "Analyze security compliance and provide recommendations"

# Output:
# ================================================================================
# ANALYST REPORT GENERATION COMPLETE
# ================================================================================
# Report ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# Status: success
# Validation Score: 92.5/100
# Duration: 45.23s
# Archive: ./reports/analyst_report_a1b2c3d4_20251105_123456.json
```

### Programmatic Usage

```python
import asyncio
from pathlib import Path
from enterprise_analyst import generate_analyst_report

async def main():
    result = await generate_analyst_report(
        source_path="/path/to/data/source",
        query="Analyze security posture and provide recommendations",
        analyst_name="Security Team Analyst",
        project_root=Path("."),
        output_dir=Path("./reports")
    )

    print(f"Report ID: {result['report_id']}")
    print(f"Status: {result['status']}")
    print(f"Validation Score: {result['validation_report']['average_score']:.1f}")

    # Access report sections
    exec_summary = result['report']['executive_summary']
    print(f"Risk Level: {exec_summary['risk_level']}")
    print(f"Key Findings: {len(exec_summary['key_findings'])}")

asyncio.run(main())
```

### Advanced Usage: EnterpriseAnalyst Class

```python
from enterprise_analyst import EnterpriseAnalyst
from pathlib import Path

# Initialize with custom configuration
analyst = EnterpriseAnalyst(
    project_root=Path("."),
    enable_rag=True,
    max_refinement_iterations=5,
    min_validation_score=90.0,
    output_dir=Path("./custom_reports")
)

# Generate report
result = await analyst.generate_report(
    source_path="/path/to/data",
    query="Detailed security compliance analysis",
    analyst_name="Chief Security Officer",
    additional_context={
        "compliance_framework": "SOC 2 Type II",
        "audit_period": "Q4 2025"
    }
)

# Access detailed results
print(f"Refinement Iterations: {result['metadata']['refinement_iterations']}")
print(f"Archive Path: {result['archive_path']}")
```

---

## Pipeline Workflow

### 5-Step Execution Flow

#### **STEP 1: Context Retrieval**
**Agent:** Scout Agent (Haiku 3.5)
**Purpose:** Retrieve relevant context from data source
**Method:** RAG system (if available) or direct file reading
**Output:** Raw context chunks

```python
# Example retrieval result
{
    "context": "Retrieved text chunks...",
    "source_count": 10,
    "retrieval_method": "rag",
    "metadata": {
        "top_k": 10,
        "sources": [...]
    }
}
```

#### **STEP 2: Report Generation**
**Agent:** Master Orchestrator (Sonnet 4.5)
**Output Style:** `analyst` (strict JSON enforcement)
**Purpose:** Generate structured report from context
**Model Enforcement:** claude-sonnet-4-5-20250929

```python
# Example generation result
{
    "report": {
        "report_metadata": {...},
        "executive_summary": {...},
        "detailed_analysis": {...},
        "recommendations": [...]
    },
    "model": "claude-sonnet-4-5-20250929",
    "output_style": "analyst"
}
```

#### **STEP 3: Validation**
**Agent:** ValidationOrchestrator (Opus 4)
**Output Style:** `critic_judge` (strict JSON enforcement)
**Purpose:** Validate report structure and quality
**Model Enforcement:** claude-opus-4-20250514

```python
# Example validation result
{
    "overall_status": "FAIL",
    "average_score": 78.5,
    "critical_count": 2,
    "high_count": 5,
    "findings": [
        {
            "severity": "CRITICAL",
            "location": "report_metadata.timestamp",
            "issue": "Missing required field",
            "recommendation": "Add ISO8601 timestamp"
        }
    ]
}
```

#### **STEP 4: Refinement (if validation fails)**
**Agent:** RefinementLoop with Refinement Agent (Sonnet 4.5)
**Output Style:** `refinement_feedback` (structured YAML)
**Purpose:** Extract structured feedback and regenerate report
**Max Iterations:** 3 (configurable)

```python
# Example refinement result
{
    "generation_result": {...},  # Refined report
    "validation_report": {...},  # New validation
    "iterations": 2,
    "history": [...]
}
```

#### **STEP 5: Finalization**
**Purpose:** Archive validated report
**Format:** JSON file with report + validation + metadata
**Location:** `{output_dir}/analyst_report_{report_id}_{timestamp}.json`

```json
{
    "report_id": "a1b2c3d4...",
    "report": {...},
    "validation": {...},
    "metadata": {
        "archived_at": "2025-11-05T12:34:56Z",
        "validation_passed": true,
        "validation_score": 92.5
    }
}
```

---

## Output Styles

### Analyst Output Style

**Location:** `/home/jevenson/.claude/lib/output_styles/analyst.md`

**Schema Overview:**

```json
{
    "report_metadata": {
        "report_id": "unique-identifier",
        "title": "Report title",
        "generated_at": "ISO8601 timestamp",
        "analyst": "Analyst name",
        "query": "Original query",
        "source_path": "Data source path",
        "confidence_score": 0.0-100.0
    },
    "executive_summary": {
        "overview": "2-3 sentence summary",
        "key_findings": ["array of findings"],
        "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
        "compliance_status": "COMPLIANT|NON_COMPLIANT|PARTIAL|UNKNOWN",
        "recommendations_summary": "Summary"
    },
    "detailed_analysis": {
        "categories": [
            {
                "category_name": "Security",
                "summary": "Category summary",
                "findings": [
                    {
                        "finding_id": "F001",
                        "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
                        "title": "Finding title",
                        "description": "Detailed description",
                        "evidence": "Supporting evidence",
                        "impact": "Impact assessment",
                        "affected_areas": ["areas"],
                        "citations": [
                            {
                                "source": "Document name",
                                "page": 42,
                                "section": "Section 3.2",
                                "quote": "Verbatim quote",
                                "url": "https://..."
                            }
                        ]
                    }
                ],
                "metrics": {
                    "total_issues": 10,
                    "critical_count": 2,
                    "high_count": 5,
                    "compliance_rate": 75.0
                }
            }
        ]
    },
    "recommendations": [
        {
            "recommendation_id": "R001",
            "priority": "IMMEDIATE|HIGH|MEDIUM|LOW",
            "title": "Recommendation title",
            "description": "Detailed description",
            "rationale": "Why this is important",
            "implementation": {
                "effort": "LOW|MEDIUM|HIGH|VERY_HIGH",
                "timeline": "1-2 weeks",
                "resources_required": ["resources"],
                "dependencies": ["dependencies"]
            },
            "expected_impact": "Expected outcome",
            "related_findings": ["F001", "F002"]
        }
    ],
    "evidence_summary": {
        "sources_consulted": 15,
        "documents_reviewed": ["list"],
        "date_range": {"earliest": "2025-01-01", "latest": "2025-11-05"},
        "data_quality": "HIGH|MEDIUM|LOW",
        "gaps_identified": ["gaps"]
    },
    "appendix": {
        "methodology": "Analysis methodology",
        "assumptions": ["assumptions"],
        "limitations": ["limitations"],
        "glossary": {"term": "definition"}
    }
}
```

**Key Features:**
- ✅ Strict JSON schema enforcement
- ✅ Mandatory evidence citations for all findings
- ✅ Structured recommendations with implementation details
- ✅ Risk and compliance assessments
- ✅ Enterprise-grade formatting suitable for executives

---

## MCP Integration

### MCP Server Architecture

The Analyst MCP Server exposes the EnterpriseAnalyst orchestrator via the Model Context Protocol, providing standardized access for external tools and AI assistants.

### Starting the MCP Server

```bash
# Start server with default configuration
python3 mcp_servers/analyst_server.py

# Start with custom configuration
python3 mcp_servers/analyst_server.py \
  --project-root /path/to/project \
  --output-dir /path/to/reports \
  --max-iterations 5 \
  --min-score 90.0 \
  --log-level INFO
```

### MCP Prompts

#### `/analyst/generate-report`

Generate a validated enterprise analyst report.

**Arguments:**
- `source_path` (required): Path to data source (file, directory, or URL)
- `query` (required): Analysis query or objective
- `analyst_name` (optional): Name of analyst for report metadata

**Example Usage:**

```
/analyst/generate-report "/data/security/audit_logs" "Analyze security compliance for Q4 2025"
```

**Response Format:**

```markdown
✅ **Enterprise Analyst Report Generated**

**Report ID:** `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
**Status:** success
**Validation Score:** 92.5/100
**Duration:** 45.23s

## Pipeline Execution
- **Retrieval Model:** claude-3-5-haiku-20241022
- **Generation Model:** claude-sonnet-4-5-20250929
- **Validation Model:** claude-opus-4-20250514
- **Output Style:** analyst
- **Refinement Iterations:** 2

## Executive Summary
**Overview:** [2-3 sentence summary]
**Risk Level:** MEDIUM
**Compliance Status:** PARTIAL

## Archive
Report archived to: `./reports/analyst_report_a1b2c3d4_20251105_123456.json`
```

### MCP Tools

#### `generate_analyst_report`

Programmatic access to report generation.

**Input Schema:**

```json
{
    "source_path": "string (required)",
    "query": "string (required)",
    "analyst_name": "string (optional, default: Claude Enterprise Analyst)",
    "include_validation": "boolean (optional, default: false)"
}
```

**Example Tool Call:**

```json
{
    "tool": "generate_analyst_report",
    "arguments": {
        "source_path": "/data/security/audit_logs",
        "query": "Analyze security compliance",
        "include_validation": true
    }
}
```

**Response:**

```json
{
    "report_id": "a1b2c3d4...",
    "status": "success",
    "report": {...},
    "metadata": {...},
    "validation": {...},
    "archive_path": "./reports/..."
}
```

---

## Testing

### Running Tests

```bash
# Dry-run mode (architecture verification only, no API calls)
python3 test_enterprise_analyst.py

# Live mode (executes actual API calls)
python3 test_enterprise_analyst.py --live

# With debug logging
python3 test_enterprise_analyst.py --live --log-level DEBUG
```

### Test Suite Coverage

**Test 1: Output Style Verification**
- Verifies `analyst.md` output style is loaded correctly
- Validates schema structure and required sections
- Confirms model and enforcement settings

**Test 2: Component Initialization**
- Initializes all pipeline agents (Scout, Master, Validation, Refinement)
- Verifies model assignments match mandate
- Confirms output style enforcement is active

**Test 3: EnterpriseAnalyst Orchestrator**
- Initializes EnterpriseAnalyst with custom configuration
- Verifies internal agent coordination
- Confirms RAG system integration

**Test 4: Pipeline Architecture (Dry-Run)**
- Verifies complete 5-step workflow without API calls
- Confirms model stack mandate compliance
- Validates output style enforcement across all steps

**Test 5: Live Pipeline Execution**
- Executes complete pipeline with real API calls
- Generates actual report from test data
- Validates report structure and archive creation
- **Note:** Only runs with `--live` flag

**Test 6: MCP Server Interface**
- Verifies MCP server initialization
- Confirms prompt and tool availability
- Validates server configuration

### Expected Test Results

```
================================================================================
TEST SUMMARY
================================================================================

Total Tests: 6
Passed: 6 ✅
Failed: 0 ❌

================================================================================
Status: ✅ ALL TESTS PASSED
================================================================================

Results saved to: ./test_results_enterprise_analyst.json
```

---

## Configuration

### EnterpriseAnalyst Configuration Options

```python
analyst = EnterpriseAnalyst(
    project_root=Path("."),              # Validation context directory
    output_dir=Path("./reports"),        # Report archive directory
    enable_rag=True,                     # Use RAG for retrieval (requires RAG system)
    max_refinement_iterations=3,         # Max refinement attempts
    min_validation_score=85.0            # Minimum validation score to pass
)
```

### MCP Server Configuration Options

```bash
python3 mcp_servers/analyst_server.py \
  --project-root /path/to/project \      # Validation context directory
  --output-dir /path/to/reports \        # Report archive directory
  --no-rag \                             # Disable RAG system
  --max-iterations 5 \                   # Max refinement iterations
  --min-score 90.0 \                     # Min validation score
  --log-level INFO                       # Logging level
```

### Output Style Configuration

Edit `/home/jevenson/.claude/lib/output_styles/analyst.md` to customize:

```yaml
---
name: analyst
version: 1.0.0
model: claude-sonnet-4-5-20250929      # Force specific model
enforcement: strict                     # strict | advisory
schema_type: json                       # json | yaml
temperature: 0.5                        # 0.0 - 1.0
max_tokens: 4000                        # Token limit
retry_on_parse_error: true              # Auto-retry on parse errors
retry_attempts: 3                       # Number of retry attempts
validation_mode: schema_strict          # schema_strict | schema_lenient
---
```

---

## Troubleshooting

### Common Issues

#### Issue: Authentication Error (401)

**Symptom:**
```
Error code: 401 - {'type': 'authentication_error', 'message': 'invalid x-api-key'}
```

**Solution:**
- Claude Code uses browser authentication by default (Claude Max subscription)
- For Python SDK direct usage, ensure valid API keys in environment
- Check `/home/jevenson/.env` for invalid/expired keys
- See `/home/jevenson/.claude/lib/ZTE_INTEGRATION_FINAL_REPORT.md` for details

#### Issue: RAG System Not Available

**Symptom:**
```
WARNING: RAG system not available - will use basic file reading
```

**Solution:**
- This is expected if RAG system not initialized
- Pipeline falls back to direct file reading
- To enable RAG: Initialize vector database and configure `rag_system.py`

#### Issue: Validation Always Fails

**Symptom:**
```
Report validation failed (score: 65.0), triggering refinement loop
Refinement exhausted max iterations (3) without passing validation
```

**Solution:**
- Check validation score threshold (default: 85.0)
- Review validation findings in output
- Lower `min_validation_score` if appropriate
- Increase `max_refinement_iterations` for more attempts

#### Issue: Missing Output Style

**Symptom:**
```
FileNotFoundError: Output style not found: analyst
```

**Solution:**
- Verify file exists: `ls -la output_styles/analyst.md`
- Check YAML frontmatter is properly formatted
- Ensure `name: analyst` in frontmatter matches requested style

---

## API Reference

### EnterpriseAnalyst Class

#### `__init__(project_root, enable_rag, max_refinement_iterations, min_validation_score, output_dir)`

Initialize the orchestrator.

**Parameters:**
- `project_root` (Path, optional): Root directory for validation context
- `enable_rag` (bool, default=True): Whether to use RAG system
- `max_refinement_iterations` (int, default=3): Maximum refinement attempts
- `min_validation_score` (float, default=85.0): Minimum validation score to pass
- `output_dir` (Path, optional): Directory for archiving reports

#### `async generate_report(source_path, query, analyst_name, additional_context)`

Generate a validated enterprise analyst report.

**Parameters:**
- `source_path` (str): Path to data source (file, directory, or URL)
- `query` (str): Analysis query or objective
- `analyst_name` (str, default="Claude Enterprise Analyst"): Analyst name for metadata
- `additional_context` (dict, optional): Additional context for report generation

**Returns:**
- `dict` with keys:
  - `report_id` (str): Unique report identifier
  - `status` (str): "success" or "failed_validation"
  - `report` (dict): Validated analyst report (JSON)
  - `validation_report` (dict): Final validation results
  - `metadata` (dict): Execution metadata (timing, iterations, models)
  - `archive_path` (str or None): Path to archived report

**Raises:**
- `Exception`: If pipeline execution fails

### Convenience Function

#### `async generate_analyst_report(source_path, query, analyst_name, project_root, output_dir)`

Convenience function for quick report generation.

**Parameters:** Same as `EnterpriseAnalyst.generate_report()`

**Returns:** Same as `EnterpriseAnalyst.generate_report()`

---

## Performance Metrics

### Expected Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Parse Error Rate** | <1% | With output style enforcement |
| **Validation Pass Rate (1st attempt)** | 70-80% | Without deliberate failure injection |
| **Validation Pass Rate (after refinement)** | >95% | With max 3 iterations |
| **Average Duration** | 30-60s | Depends on source size and complexity |
| **Cost per Report** | ~$0.05-0.15 | Depends on source size, refinement iterations |

### Cost Breakdown (Example Report)

| Phase | Model | Tokens | Cost |
|-------|-------|--------|------|
| Retrieval | Haiku 3.5 | 2,000 | $0.0005 |
| Generation | Sonnet 4.5 | 3,500 | $0.0105 |
| Validation | Opus 4 | 4,000 | $0.06 |
| Refinement (if needed) | Sonnet 4.5 | 3,500 | $0.0105 |
| **Total** | | **13,000** | **~$0.08** |

---

## Roadmap

### Future Enhancements

- [ ] **Multi-Source Aggregation**: Combine data from multiple sources in single report
- [ ] **Incremental Reports**: Update existing reports with new data
- [ ] **Custom Output Styles**: User-defined report templates
- [ ] **Interactive Refinement**: User feedback during refinement loop
- [ ] **Report Comparison**: Compare reports across time periods
- [ ] **Automated Distribution**: Email/Slack integration for report delivery
- [ ] **Dashboard Integration**: Real-time monitoring of report generation
- [ ] **A/B Testing**: Compare output style effectiveness

---

## Support and Resources

### Documentation

- **ZTE Platform Overview**: `/home/jevenson/.claude/lib/README.md`
- **Phase 2 Integration Report**: `/home/jevenson/.claude/lib/ZTE_INTEGRATION_FINAL_REPORT.md`
- **Output Styles Guide**: See output_styles/ directory
- **Validation System**: See validators/ directory

### File Locations

```
/home/jevenson/.claude/lib/
├── output_styles/
│   ├── analyst.md                    # Enterprise report schema
│   ├── critic_judge.md               # Validation schema
│   └── refinement_feedback.md        # Refinement schema
├── mcp_servers/
│   ├── analyst_server.py             # MCP server implementation
│   └── validation_server.py          # Validation MCP server
├── enterprise_analyst.py             # Main orchestrator
├── test_enterprise_analyst.py        # Test suite
└── ENTERPRISE_ANALYST_DOCUMENTATION.md  # This file
```

### Version History

- **v1.0.0** (2025-11-05): Initial release
  - Complete 5-step ZTE pipeline
  - MCP server integration
  - Comprehensive test suite
  - Production-ready documentation

---

**Last Updated:** November 5, 2025
**Documentation Version:** 1.0.0
**Status:** ✅ Production Ready

For questions or issues, refer to the ZTE Platform documentation or test suite for examples.
