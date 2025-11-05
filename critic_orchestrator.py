#!/usr/bin/env python3
"""
CriticOrchestrator - Coordinates specialized critic agents for unbiased code evaluation

Philosophy: "Creator Cannot Be Judge"
- Enforces FRESH CONTEXT: Critics receive ONLY code, no task history
- Enforces OPUS MANDATORY: All critics use claude-opus-4-20250514, no fallback
- Enforces DOMAIN SPECIALIZATION: Each critic focuses on one domain
- Enforces ACTIONABLE OUTPUT: All findings must be specific and fixable

Usage:
    orchestrator = CriticOrchestrator()

    # Run all critics
    results = orchestrator.review_code(code_snippet, file_path="app/users.py")

    # Run specific critic
    result = orchestrator.review_code(
        code_snippet,
        critics=["security-critic"],
        file_path="app/auth.py"
    )

    # Get aggregated report
    report = orchestrator.generate_report(results)
"""

import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_system import BaseAgent

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    # Fallback if observability not available
    EventEmitter = None
    EventType = None
    EventSeverity = None


@dataclass
class CriticResult:
    """Result from a single critic evaluation."""
    critic_type: str
    model_used: str
    analysis_timestamp: str
    overall_score: int
    grade: str  # EXCELLENT, GOOD, FAIR, POOR, CRITICAL
    summary: str
    findings: List[Dict[str, Any]]
    statistics: Dict[str, int]
    metrics: Dict[str, Any]
    execution_time_seconds: float
    cost_usd: float
    success: bool
    error: Optional[str] = None


@dataclass
class AggregatedReport:
    """Aggregated report from all critics."""
    timestamp: str
    file_path: Optional[str]
    code_snippet: str
    critics_run: List[str]
    overall_score: int  # 0-100, average across all critics
    worst_grade: str  # CRITICAL, POOR, FAIR, GOOD, EXCELLENT
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    findings_by_critic: Dict[str, List[Dict[str, Any]]]
    critic_scores: Dict[str, int]
    critic_grades: Dict[str, str]
    total_cost_usd: float
    total_execution_time_seconds: float
    success_count: int
    failure_count: int
    failed_critics: List[str] = field(default_factory=list)


class CriticOrchestrator:
    """
    Orchestrates multiple specialized critic agents for code evaluation.

    Key Principles:
    1. FRESH CONTEXT: Critics receive ONLY code, no creation history
    2. OPUS MANDATORY: All critics use claude-opus-4-20250514, no fallback
    3. DOMAIN SPECIALIZATION: Each critic focuses on one domain
    4. ACTIONABLE OUTPUT: Findings must be specific and fixable
    """

    # Critic definitions
    CRITICS = {
        "security-critic": {
            "name": "Security Critic",
            "description": "Deep security vulnerability analysis",
            "definition_file": Path.home() / ".claude" / "agents" / "critics" / "security-critic.md",
            "focus": "security vulnerabilities, OWASP compliance, attack vectors"
        },
        "performance-critic": {
            "name": "Performance Critic",
            "description": "Deep performance analysis and optimization",
            "definition_file": Path.home() / ".claude" / "agents" / "critics" / "performance-critic.md",
            "focus": "algorithmic complexity, database queries, memory usage, I/O"
        },
        "architecture-critic": {
            "name": "Architecture Critic",
            "description": "Deep architectural analysis and design patterns",
            "definition_file": Path.home() / ".claude" / "agents" / "critics" / "architecture-critic.md",
            "focus": "SOLID principles, coupling, cohesion, design patterns"
        },
        "code-quality-critic": {
            "name": "Code Quality Critic",
            "description": "Deep code quality and maintainability analysis",
            "definition_file": Path.home() / ".claude" / "agents" / "critics" / "code-quality-critic.md",
            "focus": "readability, maintainability, documentation, error handling"
        },
        "documentation-critic": {
            "name": "Documentation Critic",
            "description": "Deep documentation completeness analysis",
            "definition_file": Path.home() / ".claude" / "agents" / "critics" / "documentation-critic.md",
            "focus": "docstrings, examples, API docs, inline comments"
        }
    }

    # Opus model - MANDATORY, no fallback
    OPUS_MODEL = "claude-opus-4-20250514"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CriticOrchestrator.

        Args:
            api_key: Anthropic API key (uses env var ANTHROPIC_API_KEY if not provided)
        """
        self.api_key = api_key
        self._critic_agents: Dict[str, BaseAgent] = {}

        # Initialize observability
        if EventEmitter is not None:
            self.emitter = EventEmitter(enable_console=False)  # Quiet mode for critics
        else:
            self.emitter = None

        self._load_critics()

    def _load_critics(self):
        """Load all critic agents with Opus model enforcement."""
        for critic_id, critic_info in self.CRITICS.items():
            definition_file = critic_info["definition_file"]

            if not definition_file.exists():
                print(f"Warning: Critic definition not found: {definition_file}")
                continue

            # Load critic definition
            with open(definition_file, 'r') as f:
                critic_definition = f.read()

            # Create agent with OPUS MANDATORY - parameters passed directly
            agent = BaseAgent(
                role=critic_info["name"],
                model=self.OPUS_MODEL,
                api_key=self.api_key,
                system_prompt=critic_definition,
                temperature=0.3,  # Low temperature for consistent analysis
                max_tokens=4096,
                use_circuit_breaker=True  # Resilience enabled (no fallback needed separately)
            )
            self._critic_agents[critic_id] = agent

        print(f"Loaded {len(self._critic_agents)}/{len(self.CRITICS)} critics")

    def review_code(
        self,
        code_snippet: str,
        file_path: Optional[str] = None,
        critics: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> Dict[str, CriticResult]:
        """
        Review code with specified critics (or all critics).

        FRESH CONTEXT ENFORCEMENT: Critics receive ONLY the code snippet,
        with no history or context about creation.

        Args:
            code_snippet: Code to review
            file_path: Optional file path for context in findings
            critics: List of critic IDs to run (None = all critics)
            language: Programming language hint (auto-detected if None)

        Returns:
            Dictionary mapping critic_id to CriticResult
        """
        # Determine which critics to run
        critics_to_run = critics or list(self.CRITICS.keys())

        # Validate critic IDs
        invalid_critics = set(critics_to_run) - set(self.CRITICS.keys())
        if invalid_critics:
            raise ValueError(f"Invalid critic IDs: {invalid_critics}")

        # Build FRESH CONTEXT prompt (code only, no history)
        prompt = self._build_fresh_context_prompt(
            code_snippet,
            file_path,
            language
        )

        # Emit critic review started event
        if self.emitter:
            self.emitter.emit(
                event_type=EventType.CRITIC_STARTED,
                component="critic-orchestrator",
                message=f"Starting critic review with {len(critics_to_run)} critics",
                severity=EventSeverity.INFO,
                workflow="critic-system",
                data={"critics": critics_to_run, "file": file_path}
            )

        # Run critics
        results = {}
        for critic_id in critics_to_run:
            if critic_id not in self._critic_agents:
                print(f"Skipping {critic_id}: not loaded")
                continue

            # Emit critic invoked event
            if self.emitter:
                self.emitter.start_span(critic_id)
                self.emitter.emit(
                    event_type=EventType.CRITIC_STARTED,
                    component=critic_id,
                    message=f"Invoking {critic_id}",
                    severity=EventSeverity.INFO,
                    agent=critic_id,
                    model=self.OPUS_MODEL
                )

            result = self._run_critic(critic_id, prompt)
            results[critic_id] = result

            # Emit critic completed/failed event
            if self.emitter:
                if result.success:
                    self.emitter.emit(
                        event_type=EventType.CRITIC_COMPLETED,
                        component=critic_id,
                        message=f"{critic_id} completed with score {result.overall_score}",
                        severity=EventSeverity.INFO,
                        agent=critic_id,
                        duration_ms=result.execution_time_seconds * 1000,
                        cost_usd=result.cost_usd,
                        quality_score=float(result.overall_score)
                    )
                    # Emit quality measured
                    self.emitter.emit(
                        event_type=EventType.QUALITY_MEASURED,
                        component=critic_id,
                        message=f"Quality score: {result.overall_score} ({result.grade})",
                        severity=EventSeverity.INFO,
                        quality_score=float(result.overall_score),
                        data={"grade": result.grade, "findings_count": len(result.findings)}
                    )
                else:
                    self.emitter.emit(
                        event_type=EventType.CRITIC_FAILED,
                        component=critic_id,
                        message=f"{critic_id} failed: {result.error}",
                        severity=EventSeverity.ERROR,
                        error=result.error
                    )

                # Emit cost event
                if result.cost_usd and result.cost_usd > 0:
                    self.emitter.emit(
                        event_type=EventType.COST_INCURRED,
                        component=critic_id,
                        message=f"Cost incurred: ${result.cost_usd:.4f}",
                        severity=EventSeverity.INFO,
                        cost_usd=result.cost_usd,
                        data={"model": self.OPUS_MODEL}
                    )

                self.emitter.end_span()

        return results

    def _build_fresh_context_prompt(
        self,
        code_snippet: str,
        file_path: Optional[str],
        language: Optional[str]
    ) -> str:
        """
        Build prompt with FRESH CONTEXT - code only, no history.

        This is CRITICAL for the "Creator Cannot Be Judge" principle.
        The critic receives ONLY the code, with no knowledge of:
        - Who wrote it
        - Why it was written
        - What task it was created for
        - What the intended behavior is

        The critic must judge the code on its own merits.
        """
        prompt_parts = []

        # File context (minimal)
        if file_path:
            prompt_parts.append(f"File: {file_path}")

        # Language hint
        if language:
            prompt_parts.append(f"Language: {language}")
        elif file_path:
            # Auto-detect from extension
            ext = Path(file_path).suffix.lstrip('.')
            if ext:
                prompt_parts.append(f"Language: {ext}")

        # Code snippet (the ONLY substantive content)
        prompt_parts.append("\n# Code to Review\n")
        prompt_parts.append("```")
        prompt_parts.append(code_snippet)
        prompt_parts.append("```")

        # Instructions
        prompt_parts.append("\n# Instructions\n")
        prompt_parts.append(
            "Analyze the code above according to your specialized domain. "
            "Output your findings in the JSON schema format specified in your definition. "
            "Focus ONLY on your domain - do not comment on other domains. "
            "Every finding must include specific location, severity, impact, and concrete recommendation."
        )

        return "\n".join(prompt_parts)

    def _run_critic(self, critic_id: str, prompt: str) -> CriticResult:
        """
        Run a single critic with Opus model enforcement.

        Args:
            critic_id: Critic identifier
            prompt: Fresh context prompt (code only)

        Returns:
            CriticResult with findings or error
        """
        agent = self._critic_agents[critic_id]
        critic_info = self.CRITICS[critic_id]

        start_time = datetime.now()

        try:
            # Execute review with OPUS MANDATORY
            response = agent.execute(
                task=prompt,
                context={}  # FRESH CONTEXT: No context provided
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Parse JSON response
            result_json = self._extract_json(response)

            # Create CriticResult
            return CriticResult(
                critic_type=critic_id,
                model_used=result_json.get("model_used", self.OPUS_MODEL),
                analysis_timestamp=result_json.get("analysis_timestamp", datetime.now().isoformat()),
                overall_score=result_json.get("overall_score", 0),
                grade=self._extract_grade(result_json),
                summary=result_json.get("summary", "No summary provided"),
                findings=result_json.get("findings", []),
                statistics=result_json.get("statistics", {}),
                metrics=result_json.get("metrics", {}),
                execution_time_seconds=execution_time,
                cost_usd=agent.cost_tracker.total_cost,
                success=True,
                error=None
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            # Return error result
            return CriticResult(
                critic_type=critic_id,
                model_used=self.OPUS_MODEL,
                analysis_timestamp=datetime.now().isoformat(),
                overall_score=0,
                grade="ERROR",
                summary=f"Critic failed: {str(e)}",
                findings=[],
                statistics={},
                metrics={},
                execution_time_seconds=execution_time,
                cost_usd=agent.cost_tracker.total_cost,
                success=False,
                error=str(e)
            )

    def _extract_json(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from critic response.

        Critics should output pure JSON, but may include markdown code blocks.
        This extracts the JSON from various formats.
        """
        # Try parsing directly
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Try extracting from any code block
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
            # Skip language identifier if present
            if "\n" in json_str:
                json_str = "\n".join(json_str.split("\n")[1:])
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Fallback: return error structure
        return {
            "error": "Could not parse JSON from response",
            "raw_response": response[:500]  # First 500 chars
        }

    def _extract_grade(self, result_json: Dict[str, Any]) -> str:
        """Extract grade from result JSON (handles various grade field names)."""
        for key in ["grade", "quality_grade", "performance_grade",
                    "architecture_grade", "documentation_grade", "risk_level"]:
            if key in result_json:
                return result_json[key]
        return "UNKNOWN"

    def generate_report(
        self,
        results: Dict[str, CriticResult],
        code_snippet: str,
        file_path: Optional[str] = None
    ) -> AggregatedReport:
        """
        Generate aggregated report from all critic results.

        Args:
            results: Dictionary of critic results
            code_snippet: Code that was reviewed
            file_path: Optional file path

        Returns:
            AggregatedReport with aggregated findings
        """
        # Calculate aggregate statistics
        critics_run = list(results.keys())
        successful_results = [r for r in results.values() if r.success]
        failed_results = [r for r in results.values() if not r.success]

        # Overall score (average of successful critics)
        if successful_results:
            overall_score = sum(r.overall_score for r in successful_results) // len(successful_results)
        else:
            overall_score = 0

        # Worst grade
        grade_priority = {
            "CRITICAL": 0,
            "POOR": 1,
            "FAIR": 2,
            "GOOD": 3,
            "EXCELLENT": 4,
            "ERROR": -1,
            "UNKNOWN": -1
        }
        worst_grade = min(
            (r.grade for r in results.values()),
            key=lambda g: grade_priority.get(g, -1)
        )

        # Count findings by severity
        total_findings = 0
        critical_findings = 0
        high_findings = 0
        medium_findings = 0
        low_findings = 0
        findings_by_critic = {}

        for critic_id, result in results.items():
            findings_by_critic[critic_id] = result.findings
            stats = result.statistics
            total_findings += stats.get("total_findings", 0)
            critical_findings += stats.get("critical", 0)
            high_findings += stats.get("high", 0)
            medium_findings += stats.get("medium", 0)
            low_findings += stats.get("low", 0)

        # Extract scores and grades
        critic_scores = {c: r.overall_score for c, r in results.items()}
        critic_grades = {c: r.grade for c, r in results.items()}

        # Calculate costs and times
        total_cost = sum(r.cost_usd for r in results.values())
        total_time = sum(r.execution_time_seconds for r in results.values())

        return AggregatedReport(
            timestamp=datetime.now().isoformat(),
            file_path=file_path,
            code_snippet=code_snippet[:500] + "..." if len(code_snippet) > 500 else code_snippet,
            critics_run=critics_run,
            overall_score=overall_score,
            worst_grade=worst_grade,
            total_findings=total_findings,
            critical_findings=critical_findings,
            high_findings=high_findings,
            medium_findings=medium_findings,
            low_findings=low_findings,
            findings_by_critic=findings_by_critic,
            critic_scores=critic_scores,
            critic_grades=critic_grades,
            total_cost_usd=total_cost,
            total_execution_time_seconds=total_time,
            success_count=len(successful_results),
            failure_count=len(failed_results),
            failed_critics=[r.critic_type for r in failed_results]
        )

    def print_report(self, report: AggregatedReport):
        """Print human-readable report to console."""
        print("\n" + "=" * 80)
        print("CRITIC SYSTEM REPORT")
        print("=" * 80)

        if report.file_path:
            print(f"\nFile: {report.file_path}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Critics Run: {', '.join(report.critics_run)}")

        print(f"\n--- OVERALL ASSESSMENT ---")
        print(f"Overall Score: {report.overall_score}/100")
        print(f"Worst Grade: {report.worst_grade}")
        print(f"Total Findings: {report.total_findings}")
        print(f"  - Critical: {report.critical_findings}")
        print(f"  - High: {report.high_findings}")
        print(f"  - Medium: {report.medium_findings}")
        print(f"  - Low: {report.low_findings}")

        print(f"\n--- CRITIC SCORES ---")
        for critic_id, score in report.critic_scores.items():
            grade = report.critic_grades[critic_id]
            critic_name = self.CRITICS[critic_id]["name"]
            print(f"{critic_name}: {score}/100 ({grade})")

        print(f"\n--- EXECUTION METRICS ---")
        print(f"Total Cost: ${report.total_cost_usd:.4f}")
        print(f"Total Time: {report.total_execution_time_seconds:.2f}s")
        print(f"Success Count: {report.success_count}/{len(report.critics_run)}")

        if report.failed_critics:
            print(f"\nFailed Critics: {', '.join(report.failed_critics)}")

        print("\n" + "=" * 80)


def main():
    """Demo usage of CriticOrchestrator."""
    # Example code to review
    code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
    '''

    print("Initializing CriticOrchestrator...")
    orchestrator = CriticOrchestrator()

    print("\nReviewing code with all critics...")
    results = orchestrator.review_code(
        code_snippet=code,
        file_path="example.py",
        language="python"
    )

    print("\nGenerating aggregated report...")
    report = orchestrator.generate_report(
        results=results,
        code_snippet=code,
        file_path="example.py"
    )

    orchestrator.print_report(report)

    # Print detailed findings from one critic
    if "security-critic" in results:
        security_result = results["security-critic"]
        if security_result.success and security_result.findings:
            print("\n--- SECURITY FINDINGS (Sample) ---")
            for finding in security_result.findings[:2]:  # First 2 findings
                print(f"\n[{finding.get('severity', 'UNKNOWN')}] {finding.get('title', 'No title')}")
                print(f"Location: {finding.get('location', {})}")
                print(f"Description: {finding.get('description', 'No description')[:200]}...")


if __name__ == "__main__":
    main()
