#!/usr/bin/env python3
"""
Example: How the Multi-Agent System Grows Smarter Over Time

This demonstrates the learning mechanisms that make the system
improve with each use.
"""

import sys
import uuid
from datetime import datetime, timedelta
import random

sys.path.insert(0, '/home/jevenson/.claude/lib')

from learning_system import (
    AdaptiveLearner, TaskExecution, FeedbackType,
    ReinforcementLearner
)
from dynamic_spawner import DynamicAgentSpawner


def simulate_task_execution(task_description: str, team: list) -> TaskExecution:
    """Simulate a task execution for demonstration."""
    # In real usage, this would be actual execution results
    success = random.random() > 0.3  # 70% success rate

    return TaskExecution(
        task_id=str(uuid.uuid4()),
        task_description=task_description,
        task_domain=['web_development', 'api_development'],
        task_complexity='moderate',
        agents_used=team,
        execution_mode='adaptive',
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(minutes=random.randint(10, 60)),
        duration_minutes=random.randint(10, 60),
        cost=random.uniform(0.5, 5.0),
        success=success,
        feedback=FeedbackType.SUCCESS if success else FeedbackType.FAILURE,
        user_rating=random.randint(3, 5) if success else random.randint(1, 3),
        error_count=0 if success else random.randint(1, 3),
        retry_count=0 if success else random.randint(0, 2),
        lessons_learned=[
            "API design should come before implementation",
            "Parallel execution saved 40% time"
        ] if success else [
            "Need better error handling",
            "Missing test coverage"
        ]
    )


def main():
    print("=" * 70)
    print("HOW THE SYSTEM GROWS SMARTER - DEMONSTRATION")
    print("=" * 70)

    # Initialize learning system
    learner = AdaptiveLearner()
    rl_learner = ReinforcementLearner(learner)
    spawner = DynamicAgentSpawner()

    print("\n📚 PHASE 1: Initial Learning")
    print("-" * 40)

    # Simulate some initial task executions
    initial_tasks = [
        "Build a React dashboard with REST API",
        "Create authentication system with JWT",
        "Implement real-time chat with WebSockets",
        "Design database schema for e-commerce",
        "Setup CI/CD pipeline with GitHub Actions"
    ]

    print("Simulating 5 initial tasks to build knowledge base...")
    for task in initial_tasks:
        # Spawner analyzes task (initially without much knowledge)
        analysis = spawner.analyze_task(task)
        team = [a.value for a in analysis.suggested_agents[:3]]

        # Simulate execution
        execution = simulate_task_execution(task, team)

        # LEARNING HAPPENS HERE
        learner.learn_from_execution(execution)

        print(f"  ✓ Task: {task[:40]}")
        print(f"    Result: {'✅ Success' if execution.success else '❌ Failed'}")
        print(f"    Team: {', '.join(team[:2])}...")
        print(f"    Learned: {execution.lessons_learned[0][:50]}")

    print("\n📊 PHASE 2: Knowledge Accumulation")
    print("-" * 40)

    # Show what the system has learned
    insights = learner.export_insights()
    print(f"Total executions analyzed: {insights['total_executions']}")
    print(f"Overall success rate: {insights['success_rate']:.1%}")
    print(f"Average cost: ${insights['avg_cost']:.2f}")
    print(f"Average duration: {insights['avg_duration']:.1f} minutes")

    if insights['top_agents']:
        print("\nTop performing agents:")
        for agent, score in insights['top_agents'][:3]:
            print(f"  • {agent}: {score:.2f} performance score")

    print("\n🧠 PHASE 3: Intelligent Recommendations")
    print("-" * 40)

    # Now ask for recommendations on a NEW similar task
    new_task = "Build a Vue.js admin panel with GraphQL API"
    print(f"New task: {new_task}")

    # The system now uses its accumulated knowledge
    recommendations = learner.get_recommendations(new_task)

    print(f"\nSystem recommendations (confidence: {recommendations['confidence']:.1%}):")
    if recommendations['suggested_team']:
        print(f"  Suggested team: {', '.join(recommendations['suggested_team'][:3])}")
    print(f"  Execution mode: {recommendations['execution_mode']}")
    print(f"  Estimated duration: {recommendations['estimated_duration']:.0f} minutes")
    print(f"  Estimated cost: ${recommendations['estimated_cost']:.2f}")

    if recommendations['similar_successes']:
        print("\nBased on similar successful tasks:")
        for similar in recommendations['similar_successes'][:2]:
            print(f"  • {similar['task'][:50]}...")

    if recommendations['warnings']:
        print("\n⚠️ Warnings based on past failures:")
        for warning in recommendations['warnings']:
            print(f"  • {warning}")

    print("\n🔄 PHASE 4: Continuous Improvement")
    print("-" * 40)

    # Simulate more executions to show improvement
    print("Running 10 more tasks with learned optimizations...")

    before_success_rate = insights['success_rate']

    for i in range(10):
        task = f"Task {i+1}: Web application with API"

        # Use reinforcement learning to select team
        team = rl_learner.select_team_with_exploration(
            task,
            ['frontend-specialist', 'backend-specialist', 'api-designer',
             'test-specialist', 'security-auditor', 'devops-specialist']
        )

        execution = simulate_task_execution(task, team)

        # Calculate reward and update Q-values
        reward = rl_learner.calculate_reward(execution)
        state = f"{execution.task_complexity}:{len(team)}"
        action = ','.join(sorted(team))
        rl_learner.update_q_value(state, action, reward)

        # Learn from execution
        learner.learn_from_execution(execution)

    # Check improvement
    new_insights = learner.export_insights()
    after_success_rate = new_insights['success_rate']

    print(f"\nSuccess rate improvement:")
    print(f"  Before: {before_success_rate:.1%}")
    print(f"  After:  {after_success_rate:.1%}")
    if after_success_rate > before_success_rate:
        print(f"  📈 Improved by {(after_success_rate - before_success_rate):.1%}!")

    print("\n🎯 PHASE 5: Specialized Knowledge")
    print("-" * 40)

    # Show agent specializations discovered
    specializations = learner.pattern_recognizer.identify_agent_specializations()
    if specializations:
        print("Discovered agent specializations:")
        for agent, domains in list(specializations.items())[:3]:
            if domains:
                print(f"  • {agent}: {', '.join(list(domains)[:2])}")

    # Show discovered patterns
    patterns = learner.pattern_recognizer.analyze_execution_patterns(min_occurrences=1)
    if patterns:
        print(f"\nDiscovered {len(patterns)} successful team patterns")
        best_pattern = max(patterns, key=lambda p: p.success_rate)
        print(f"  Best pattern: {', '.join(best_pattern.agents[:3])}...")
        print(f"  Success rate: {best_pattern.success_rate:.1%}")

    print("\n" + "=" * 70)
    print("🚀 SUMMARY: How The System Grows Smarter")
    print("=" * 70)

    print("""
The system becomes smarter through:

1. **EXPERIENCE ACCUMULATION**
   - Every task execution is recorded and analyzed
   - Success patterns are identified and reinforced
   - Failure patterns are detected and avoided

2. **PATTERN RECOGNITION**
   - Successful team compositions are discovered
   - Agent specializations emerge from data
   - Optimal execution modes are learned

3. **ADAPTIVE RECOMMENDATIONS**
   - Similar past tasks inform new decisions
   - Confidence grows with more examples
   - Warnings prevent repeated failures

4. **REINFORCEMENT LEARNING**
   - Exploration tries new agent combinations
   - Exploitation uses proven successful teams
   - Q-values track long-term performance

5. **CONTINUOUS OPTIMIZATION**
   - Cost and duration estimates improve
   - Agent rankings reflect real performance
   - Team compositions evolve based on results

The more you use it, the smarter it gets! 🧠
""")

    print("Learned knowledge is persisted in:")
    print("  /home/jevenson/.claude/agents/learning.db")
    print("\nThis knowledge is automatically used by the Dynamic Spawner")
    print("for ALL future tasks across ALL projects!")


if __name__ == '__main__':
    main()