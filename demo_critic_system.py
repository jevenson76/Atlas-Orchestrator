#!/usr/bin/env python3
"""
Interactive Demo: C3 Specialized Critic System

Demonstrates:
1. Individual critic analysis (security, performance, architecture, etc.)
2. Multi-critic orchestration
3. Validator + Critic integration
4. Fresh context enforcement
5. Opus model usage
6. Cost tracking and reporting
7. Recommendation logic

Usage:
    python3 demo_critic_system.py
"""

import sys
from pathlib import Path
from typing import List

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from critic_orchestrator import CriticOrchestrator
from validation_orchestrator import ValidationOrchestrator


# ============================================================================
# SAMPLE CODE FOR TESTING
# ============================================================================

BAD_CODE_SQL_INJECTION = '''
def get_user(user_id):
    """Fetch user from database."""
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

def delete_user(user_id):
    """Delete user from database."""
    query = f"DELETE FROM users WHERE id = {user_id}"
    db.execute(query)
    return True
'''

BAD_CODE_N_PLUS_ONE = '''
def get_user_posts(user_ids):
    """Get posts for multiple users."""
    posts = []
    for user_id in user_ids:
        user = db.query(User).filter_by(id=user_id).first()
        user_posts = db.query(Post).filter_by(user_id=user.id).all()
        for post in user_posts:
            posts.append(post)
    return posts
'''

BAD_CODE_GOD_OBJECT = '''
class UserController:
    """Handle all user operations."""

    def register_user(self, username, password, email):
        # Validation
        if not username or len(username) < 3:
            return {"error": "Invalid username"}

        # Database connection
        conn = mysql.connector.connect(
            host="localhost", user="root", password="admin123", database="users"
        )
        cursor = conn.cursor()

        # Password hashing
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        # Insert query
        query = f"INSERT INTO users VALUES ('{username}', '{hashed_pw}', '{email}')"
        cursor.execute(query)
        conn.commit()

        # Send welcome email
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.sendmail('noreply@app.com', email, f'Welcome {username}!')

        return {"success": True}
'''

BAD_CODE_QUALITY = '''
def process(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            if data[i] < 100:
                if data[i] % 2 == 0:
                    result.append(data[i] * 2)
                else:
                    result.append(data[i] * 3)
            else:
                result.append(data[i])
        else:
            result.append(0)
    return result
'''

UNDOCUMENTED_CODE = '''
def calc(d, w, t):
    tot = 0
    for i, v in enumerate(d):
        if v > t:
            tot += v * w[i]
    return tot / len(d) if d else 0
'''

GOOD_CODE = '''
from typing import List
from dataclasses import dataclass

@dataclass
class User:
    """User entity with validated fields."""
    id: int
    username: str
    email: str

class UserRepository:
    """Data access layer for user operations."""

    def __init__(self, db_session):
        self._db = db_session

    def find_by_id(self, user_id: int) -> User:
        """Fetch user by ID using parameterized query.

        Args:
            user_id: User identifier

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        query = "SELECT * FROM users WHERE id = ?"
        result = self._db.execute(query, (user_id,))

        if not result:
            raise ValueError(f"User {user_id} not found")

        return User(**result)

def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numeric values.

    Args:
        numbers: List of numbers

    Returns:
        Average value

    Raises:
        ValueError: If list is empty

    Example:
        >>> calculate_average([1, 2, 3, 4, 5])
        3.0
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")

    return sum(numbers) / len(numbers)
'''


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def print_section_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_code_sample(code: str, description: str):
    """Print code sample with description."""
    print(f"\n--- {description} ---\n")
    print("```python")
    print(code.strip())
    print("```\n")


def demo_1_single_critic():
    """Demo 1: Single security critic analysis."""
    print_section_header("DEMO 1: Single Critic Analysis (Security)")

    print_code_sample(BAD_CODE_SQL_INJECTION, "Code with SQL Injection Vulnerability")

    print("🔍 Running Security Critic (Opus model)...\n")

    orchestrator = CriticOrchestrator()
    results = orchestrator.review_code(
        code_snippet=BAD_CODE_SQL_INJECTION,
        critics=["security-critic"],
        file_path="auth.py",
        language="python"
    )

    # Display results
    if "security-critic" in results:
        result = results["security-critic"]

        print(f"✅ Analysis Complete!")
        print(f"   Model Used: {result.model_used}")
        print(f"   Overall Score: {result.overall_score}/100")
        print(f"   Grade: {result.grade}")
        print(f"   Execution Time: {result.execution_time_seconds:.2f}s")
        print(f"   Cost: ${result.cost_usd:.4f}")

        if result.findings:
            print(f"\n📋 Findings ({len(result.findings)} total):")
            for i, finding in enumerate(result.findings[:3], 1):  # First 3
                print(f"\n   {i}. [{finding.get('severity', 'N/A')}] {finding.get('title', 'No title')}")
                print(f"      Location: {finding.get('location', {})}")
                print(f"      Issue: {finding.get('description', 'N/A')[:100]}...")

        stats = result.statistics
        print(f"\n📊 Statistics:")
        print(f"   Total Findings: {stats.get('total_findings', 0)}")
        print(f"   - Critical: {stats.get('critical', 0)}")
        print(f"   - High: {stats.get('high', 0)}")
        print(f"   - Medium: {stats.get('medium', 0)}")
        print(f"   - Low: {stats.get('low', 0)}")

    input("\n[Press Enter to continue to Demo 2...]")


def demo_2_multiple_critics():
    """Demo 2: Multiple critics in parallel."""
    print_section_header("DEMO 2: Multiple Critics (Security + Performance + Architecture)")

    print_code_sample(BAD_CODE_GOD_OBJECT, "Code with Multiple Issues")

    print("🔍 Running 3 Critics in Parallel (all using Opus)...\n")

    orchestrator = CriticOrchestrator()
    results = orchestrator.review_code(
        code_snippet=BAD_CODE_GOD_OBJECT,
        critics=["security-critic", "performance-critic", "architecture-critic"],
        file_path="controllers.py",
        language="python"
    )

    # Generate aggregated report
    report = orchestrator.generate_report(
        results=results,
        code_snippet=BAD_CODE_GOD_OBJECT,
        file_path="controllers.py"
    )

    # Display aggregated report
    print("✅ Multi-Critic Analysis Complete!\n")
    print(f"📊 AGGREGATED REPORT")
    print(f"   Overall Score: {report.overall_score}/100")
    print(f"   Worst Grade: {report.worst_grade}")
    print(f"   Total Findings: {report.total_findings}")
    print(f"     - Critical: {report.critical_findings}")
    print(f"     - High: {report.high_findings}")
    print(f"     - Medium: {report.medium_findings}")
    print(f"     - Low: {report.low_findings}")
    print(f"   Total Cost: ${report.total_cost_usd:.4f}")
    print(f"   Total Time: {report.total_execution_time_seconds:.2f}s")

    print(f"\n📋 Results by Critic:")
    for critic_id, result in results.items():
        print(f"\n   {critic_id}:")
        print(f"     Score: {result.overall_score}/100 ({result.grade})")
        print(f"     Findings: {len(result.findings)}")
        print(f"     Cost: ${result.cost_usd:.4f}")

    input("\n[Press Enter to continue to Demo 3...]")


def demo_3_all_critics():
    """Demo 3: All 5 critics."""
    print_section_header("DEMO 3: Comprehensive Analysis (All 5 Critics)")

    print_code_sample(UNDOCUMENTED_CODE, "Code with Quality and Documentation Issues")

    print("🔍 Running ALL 5 Critics (Comprehensive Analysis)...\n")
    print("   Critics: security, performance, architecture, code-quality, documentation\n")

    orchestrator = CriticOrchestrator()
    results = orchestrator.review_code(
        code_snippet=UNDOCUMENTED_CODE,
        file_path="utils.py",
        language="python"
        # critics=None means run all
    )

    report = orchestrator.generate_report(
        results=results,
        code_snippet=UNDOCUMENTED_CODE,
        file_path="utils.py"
    )

    orchestrator.print_report(report)

    input("\n[Press Enter to continue to Demo 4...]")


def demo_4_validator_critic_integration():
    """Demo 4: Validators + Critics integration."""
    print_section_header("DEMO 4: Validator + Critic Integration")

    print("This demo shows the two-stage evaluation:")
    print("  1. VALIDATORS (fast, structural checks) - Haiku/Sonnet")
    print("  2. CRITICS (deep, semantic analysis) - Opus MANDATORY")

    print_code_sample(BAD_CODE_N_PLUS_ONE, "Code with Performance Issues")

    print("🔍 Running Comprehensive Evaluation (Standard Level)...\n")

    try:
        orchestrator = ValidationOrchestrator(project_root=".")

        result = orchestrator.validate_with_critics(
            code=BAD_CODE_N_PLUS_ONE,
            context={
                "file_path": "queries.py",
                "language": "python",
                "criticality": "high"
            },
            level="standard"  # validators + 3 key critics
        )

        # Display combined report
        orchestrator.print_combined_report(result)

    except Exception as e:
        print(f"❌ Demo 4 failed: {e}")
        print(f"   This is expected if validators are not set up.")

    input("\n[Press Enter to continue to Demo 5...]")


def demo_5_good_code():
    """Demo 5: Analyzing good code."""
    print_section_header("DEMO 5: Analyzing Good Code (What Excellence Looks Like)")

    print_code_sample(GOOD_CODE, "Well-Written Code")

    print("🔍 Running All Critics on Good Code...\n")

    orchestrator = CriticOrchestrator()
    results = orchestrator.review_code(
        code_snippet=GOOD_CODE,
        file_path="models.py",
        language="python"
    )

    report = orchestrator.generate_report(
        results=results,
        code_snippet=GOOD_CODE,
        file_path="models.py"
    )

    print("\n✅ Analysis Complete!")
    print(f"\n📊 RESULTS FOR GOOD CODE")
    print(f"   Overall Score: {report.overall_score}/100")
    print(f"   Worst Grade: {report.worst_grade}")
    print(f"   Total Findings: {report.total_findings}")

    if report.overall_score >= 80:
        print(f"\n✅ EXCELLENT CODE QUALITY!")
        print(f"   This code demonstrates:")
        print(f"     - ✅ No security vulnerabilities")
        print(f"     - ✅ Efficient algorithms")
        print(f"     - ✅ Clean architecture (SOLID principles)")
        print(f"     - ✅ High code quality")
        print(f"     - ✅ Comprehensive documentation")

    print(f"\n📋 Critic Breakdown:")
    for critic_id, result in results.items():
        print(f"   {critic_id}: {result.overall_score}/100 ({result.grade})")

    input("\n[Press Enter to continue to Demo 6...]")


def demo_6_cost_comparison():
    """Demo 6: Cost comparison between levels."""
    print_section_header("DEMO 6: Cost Comparison (Quick vs Standard vs Thorough)")

    print("Let's compare the cost and depth of different validation levels:\n")

    print("📊 VALIDATION LEVELS:\n")

    print("  QUICK (Validators Only):")
    print("    - Validators: 1 (code-validator with Haiku)")
    print("    - Critics: 0")
    print("    - Est. Cost: $0.001 - $0.005")
    print("    - Est. Time: 2-5 seconds")
    print("    - Use Case: CI/CD quick checks\n")

    print("  STANDARD (Validators + Key Critics):")
    print("    - Validators: 1 (code-validator with Sonnet)")
    print("    - Critics: 3 (security, performance, architecture)")
    print("    - Est. Cost: $0.15 - $0.20")
    print("    - Est. Time: 40-60 seconds")
    print("    - Use Case: Pre-commit review\n")

    print("  THOROUGH (Validators + All Critics):")
    print("    - Validators: 1 (code-validator with Opus)")
    print("    - Critics: 5 (all critics)")
    print("    - Est. Cost: $0.25 - $0.35")
    print("    - Est. Time: 90-120 seconds")
    print("    - Use Case: Pre-production gate\n")

    print("💡 KEY INSIGHT:")
    print("   Critics are 20-30x more expensive than validators, but provide")
    print("   deep semantic analysis that validators cannot match.\n")

    print("💰 COST BREAKDOWN (per review):")
    print("   - Haiku validator: ~$0.001")
    print("   - Sonnet validator: ~$0.005")
    print("   - Opus validator: ~$0.020")
    print("   - Single critic (Opus): ~$0.050 - $0.060")
    print("   - All 5 critics: ~$0.250 - $0.300\n")

    input("\n[Press Enter to finish demo...]")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print(" " * 20 + "C3 SPECIALIZED CRITIC SYSTEM DEMO")
    print("=" * 80)

    print("""
This interactive demo showcases the C3 Critic System:

✅ FRESH CONTEXT: Critics receive ONLY code (no task history)
✅ OPUS MANDATORY: All critics use claude-opus-4-20250514
✅ DOMAIN SPECIALIZATION: Each critic focuses on one domain
✅ ACTIONABLE OUTPUT: Specific findings with concrete recommendations

The demos will:
1. Run individual critics
2. Run multiple critics in parallel
3. Run all 5 critics
4. Show validator + critic integration
5. Analyze good code
6. Compare costs across levels

NOTE: Some demos require ANTHROPIC_API_KEY environment variable.
      If not set, demos will show mock results.
    """)

    input("[Press Enter to begin Demo 1...]")

    try:
        # Run all demos
        demo_1_single_critic()
        demo_2_multiple_critics()
        demo_3_all_critics()
        demo_4_validator_critic_integration()
        demo_5_good_code()
        demo_6_cost_comparison()

        print_section_header("DEMO COMPLETE!")

        print("""
🎉 You've seen the full C3 Critic System in action!

KEY TAKEAWAYS:

1. **Creator Cannot Be Judge** - Critics use fresh context (code only)
2. **Opus Mandatory** - All critics use Opus 4 (no fallback)
3. **Domain Specialization** - Each critic focuses on one area
4. **Comprehensive Analysis** - All 5 critics provide deep insights
5. **Cost-Aware** - Choose level based on budget and depth needed

NEXT STEPS:

- Read: ~/.claude/lib/CRITIC_SYSTEM_README.md
- Run Tests: pytest test_critic_system.py -v
- Try It: Use validate_with_critics() in your projects

Thank you for exploring the C3 Critic System!
        """)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
