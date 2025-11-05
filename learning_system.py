"""
Learning System for Multi-Agent Intelligence Growth

This module enables the agent system to learn from experience,
optimize team composition, and improve task execution over time.
"""

import json
import sqlite3
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from enum import Enum
import numpy as np
from statistics import mean, median, stdev
import logging

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback for learning."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    USER_POSITIVE = "user_positive"
    USER_NEGATIVE = "user_negative"
    USER_CORRECTION = "user_correction"


class LearningMode(Enum):
    """Learning modes for the system."""
    PASSIVE = "passive"      # Learn from observation only
    ACTIVE = "active"        # Actively experiment with teams
    ADAPTIVE = "adaptive"    # Adjust based on performance
    REINFORCEMENT = "reinforcement"  # Use reward signals


@dataclass
class TaskExecution:
    """Record of a task execution for learning."""
    task_id: str
    task_description: str
    task_domain: List[str]
    task_complexity: str
    agents_used: List[str]
    execution_mode: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    cost: float
    success: bool
    feedback: FeedbackType
    user_rating: Optional[int] = None  # 1-5 stars
    error_count: int = 0
    retry_count: int = 0
    outputs: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)


@dataclass
class AgentPerformance:
    """Track individual agent performance over time."""
    agent_name: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_duration: float = 0.0
    avg_cost: float = 0.0
    error_rate: float = 0.0
    retry_rate: float = 0.0
    user_rating: float = 0.0
    specializations: Set[str] = field(default_factory=set)
    weak_areas: Set[str] = field(default_factory=set)
    collaboration_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class TeamPattern:
    """Successful team composition pattern."""
    pattern_id: str
    task_type: str
    agents: List[str]
    success_rate: float
    avg_duration: float
    avg_cost: float
    usage_count: int
    last_used: datetime
    confidence: float
    conditions: Dict[str, Any] = field(default_factory=dict)


class LearningDatabase:
    """
    Persistent storage for learning data.
    """

    def __init__(self, db_path: str = "/home/jevenson/.claude/agents/learning.db"):
        """Initialize learning database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()

    def _create_tables(self):
        """Create database tables for learning data."""
        cursor = self.conn.cursor()

        # Task executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_executions (
                task_id TEXT PRIMARY KEY,
                task_description TEXT,
                task_domain TEXT,
                task_complexity TEXT,
                agents_used TEXT,
                execution_mode TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes REAL,
                cost REAL,
                success BOOLEAN,
                feedback TEXT,
                user_rating INTEGER,
                error_count INTEGER,
                retry_count INTEGER,
                outputs TEXT,
                metrics TEXT,
                lessons_learned TEXT
            )
        """)

        # Agent performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                agent_name TEXT PRIMARY KEY,
                total_tasks INTEGER,
                successful_tasks INTEGER,
                failed_tasks INTEGER,
                avg_duration REAL,
                avg_cost REAL,
                error_rate REAL,
                retry_rate REAL,
                user_rating REAL,
                specializations TEXT,
                weak_areas TEXT,
                collaboration_scores TEXT,
                last_updated TIMESTAMP
            )
        """)

        # Team patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_patterns (
                pattern_id TEXT PRIMARY KEY,
                task_type TEXT,
                agents TEXT,
                success_rate REAL,
                avg_duration REAL,
                avg_cost REAL,
                usage_count INTEGER,
                last_used TIMESTAMP,
                confidence REAL,
                conditions TEXT
            )
        """)

        # Knowledge base table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                knowledge_id TEXT PRIMARY KEY,
                category TEXT,
                key TEXT,
                value TEXT,
                confidence REAL,
                usage_count INTEGER,
                last_updated TIMESTAMP
            )
        """)

        self.conn.commit()

    def save_execution(self, execution: TaskExecution):
        """Save task execution record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO task_executions VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            execution.task_id,
            execution.task_description,
            json.dumps(execution.task_domain),
            execution.task_complexity,
            json.dumps(execution.agents_used),
            execution.execution_mode,
            execution.start_time.isoformat(),
            execution.end_time.isoformat(),
            execution.duration_minutes,
            execution.cost,
            execution.success,
            execution.feedback.value,
            execution.user_rating,
            execution.error_count,
            execution.retry_count,
            json.dumps(execution.outputs),
            json.dumps(execution.metrics),
            json.dumps(execution.lessons_learned)
        ))
        self.conn.commit()

    def get_similar_executions(self, task_description: str,
                               limit: int = 10) -> List[TaskExecution]:
        """Find similar past task executions."""
        # Simple keyword matching (could use embeddings for better similarity)
        keywords = set(task_description.lower().split())

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM task_executions
            ORDER BY start_time DESC
            LIMIT 100
        """)

        executions = []
        for row in cursor.fetchall():
            exec_desc = row[1].lower()
            exec_keywords = set(exec_desc.split())

            # Calculate similarity
            overlap = len(keywords & exec_keywords)
            if overlap > len(keywords) * 0.3:  # 30% overlap threshold
                executions.append(self._row_to_execution(row))

        return executions[:limit]

    def _row_to_execution(self, row) -> TaskExecution:
        """Convert database row to TaskExecution."""
        return TaskExecution(
            task_id=row[0],
            task_description=row[1],
            task_domain=json.loads(row[2]),
            task_complexity=row[3],
            agents_used=json.loads(row[4]),
            execution_mode=row[5],
            start_time=datetime.fromisoformat(row[6]),
            end_time=datetime.fromisoformat(row[7]),
            duration_minutes=row[8],
            cost=row[9],
            success=row[10],
            feedback=FeedbackType(row[11]),
            user_rating=row[12],
            error_count=row[13],
            retry_count=row[14],
            outputs=json.loads(row[15]),
            metrics=json.loads(row[16]),
            lessons_learned=json.loads(row[17])
        )

    def update_agent_performance(self, agent_name: str, execution: TaskExecution):
        """Update agent performance metrics."""
        cursor = self.conn.cursor()

        # Get current performance
        cursor.execute("""
            SELECT * FROM agent_performance WHERE agent_name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        if row:
            # Update existing performance
            total = row[1] + 1
            successful = row[2] + (1 if execution.success else 0)
            failed = row[3] + (0 if execution.success else 1)
            avg_duration = (row[4] * row[1] + execution.duration_minutes) / total
            avg_cost = (row[5] * row[1] + execution.cost) / total
            error_rate = failed / total
            retry_rate = (row[7] * row[1] + execution.retry_count) / total

            cursor.execute("""
                UPDATE agent_performance
                SET total_tasks = ?, successful_tasks = ?, failed_tasks = ?,
                    avg_duration = ?, avg_cost = ?, error_rate = ?, retry_rate = ?,
                    last_updated = ?
                WHERE agent_name = ?
            """, (total, successful, failed, avg_duration, avg_cost,
                  error_rate, retry_rate, datetime.now().isoformat(), agent_name))
        else:
            # Create new performance record
            cursor.execute("""
                INSERT INTO agent_performance VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (agent_name, 1, 1 if execution.success else 0,
                  0 if execution.success else 1, execution.duration_minutes,
                  execution.cost, 0 if execution.success else 1,
                  execution.retry_count, 0.0, json.dumps([]), json.dumps([]),
                  json.dumps({}), datetime.now().isoformat()))

        self.conn.commit()

    def get_best_team_for_task(self, task_type: str) -> Optional[TeamPattern]:
        """Get the best performing team for a task type."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM team_patterns
            WHERE task_type = ?
            ORDER BY success_rate DESC, avg_cost ASC
            LIMIT 1
        """, (task_type,))

        row = cursor.fetchone()
        if row:
            return TeamPattern(
                pattern_id=row[0],
                task_type=row[1],
                agents=json.loads(row[2]),
                success_rate=row[3],
                avg_duration=row[4],
                avg_cost=row[5],
                usage_count=row[6],
                last_used=datetime.fromisoformat(row[7]),
                confidence=row[8],
                conditions=json.loads(row[9])
            )
        return None

    def save_knowledge(self, category: str, key: str, value: Any,
                      confidence: float = 1.0):
        """Save learned knowledge."""
        cursor = self.conn.cursor()
        knowledge_id = f"{category}:{key}"

        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_base VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (knowledge_id, category, key, json.dumps(value),
              confidence, 1, datetime.now().isoformat()))

        self.conn.commit()

    def get_knowledge(self, category: str, key: str) -> Optional[Any]:
        """Retrieve learned knowledge."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value, confidence FROM knowledge_base
            WHERE category = ? AND key = ?
        """, (category, key))

        row = cursor.fetchone()
        if row and row[1] > 0.5:  # Only return if confidence > 50%
            return json.loads(row[0])
        return None


class PatternRecognizer:
    """
    Recognizes patterns in task executions and agent performance.
    """

    def __init__(self, db: LearningDatabase):
        self.db = db
        self.patterns = []

    def analyze_execution_patterns(self, min_occurrences: int = 3) -> List[TeamPattern]:
        """Analyze executions to find successful team patterns."""
        cursor = self.db.conn.cursor()

        # Group executions by agent teams
        cursor.execute("""
            SELECT agents_used, task_complexity, COUNT(*) as count,
                   AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
                   AVG(duration_minutes) as avg_duration,
                   AVG(cost) as avg_cost
            FROM task_executions
            GROUP BY agents_used, task_complexity
            HAVING count >= ?
        """, (min_occurrences,))

        patterns = []
        for row in cursor.fetchall():
            if row[3] > 0.7:  # Success rate > 70%
                pattern = TeamPattern(
                    pattern_id=f"pattern_{len(patterns)}",
                    task_type=row[1],
                    agents=json.loads(row[0]),
                    success_rate=row[3],
                    avg_duration=row[4],
                    avg_cost=row[5],
                    usage_count=row[2],
                    last_used=datetime.now(),
                    confidence=min(row[2] / 10, 1.0)  # Confidence based on usage
                )
                patterns.append(pattern)

                # Save pattern to database
                self._save_pattern(pattern)

        return patterns

    def _save_pattern(self, pattern: TeamPattern):
        """Save discovered pattern to database."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO team_patterns VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (pattern.pattern_id, pattern.task_type, json.dumps(pattern.agents),
              pattern.success_rate, pattern.avg_duration, pattern.avg_cost,
              pattern.usage_count, pattern.last_used.isoformat(),
              pattern.confidence, json.dumps(pattern.conditions)))
        self.db.conn.commit()

    def identify_agent_specializations(self) -> Dict[str, Set[str]]:
        """Identify what each agent is particularly good at."""
        cursor = self.db.conn.cursor()

        # Analyze successful tasks per agent
        cursor.execute("""
            SELECT t.agents_used, t.task_domain
            FROM task_executions t
            WHERE t.success = 1
        """)

        agent_domains = defaultdict(Counter)
        for row in cursor.fetchall():
            agents = json.loads(row[0])
            domains = json.loads(row[1])

            for agent in agents:
                for domain in domains:
                    agent_domains[agent][domain] += 1

        # Identify specializations (domains with high success)
        specializations = {}
        for agent, domains in agent_domains.items():
            total = sum(domains.values())
            specializations[agent] = {
                domain for domain, count in domains.items()
                if count / total > 0.3  # 30% of successful tasks
            }

        return specializations

    def detect_failure_patterns(self) -> List[Dict[str, Any]]:
        """Detect common failure patterns to avoid."""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT task_description, agents_used, error_count, lessons_learned
            FROM task_executions
            WHERE success = 0
            ORDER BY start_time DESC
            LIMIT 50
        """)

        failure_patterns = []
        for row in cursor.fetchall():
            # Analyze failure reasons
            pattern = {
                'description_keywords': set(row[0].lower().split()[:5]),
                'problematic_agents': json.loads(row[1]),
                'error_indicators': row[2],
                'lessons': json.loads(row[3])
            }
            failure_patterns.append(pattern)

        return failure_patterns


class AdaptiveLearner:
    """
    Core learning engine that improves the system over time.
    """

    def __init__(self, db_path: str = "/home/jevenson/.claude/agents/learning.db"):
        self.db = LearningDatabase(db_path)
        self.pattern_recognizer = PatternRecognizer(self.db)
        self.learning_mode = LearningMode.ADAPTIVE

        # Performance thresholds for learning triggers
        self.performance_thresholds = {
            'success_rate_min': 0.7,
            'cost_increase_alert': 1.5,  # 50% increase
            'duration_increase_alert': 2.0,  # 2x slower
            'retry_threshold': 3
        }

        logger.info("Adaptive Learner initialized")

    def learn_from_execution(self, execution: TaskExecution):
        """
        Learn from a completed task execution.

        This is the PRIMARY learning mechanism that makes the system smarter.
        """
        # 1. Save execution for historical analysis
        self.db.save_execution(execution)

        # 2. Update agent performance metrics
        for agent in execution.agents_used:
            self.db.update_agent_performance(agent, execution)

        # 3. Analyze for patterns
        if execution.success:
            self._learn_success_patterns(execution)
        else:
            self._learn_failure_patterns(execution)

        # 4. Adjust team recommendations
        self._update_team_recommendations(execution)

        # 5. Extract and save knowledge
        self._extract_knowledge(execution)

        # 6. Trigger adaptive improvements
        self._trigger_adaptations(execution)

        logger.info(f"Learned from execution {execution.task_id}: "
                   f"Success={execution.success}, Cost=${execution.cost:.2f}")

    def _learn_success_patterns(self, execution: TaskExecution):
        """Learn from successful executions."""
        # Record successful team composition
        team_key = f"{execution.task_complexity}:{','.join(sorted(execution.agents_used))}"
        self.db.save_knowledge(
            category="successful_teams",
            key=team_key,
            value={
                'agents': execution.agents_used,
                'duration': execution.duration_minutes,
                'cost': execution.cost
            },
            confidence=0.9 if execution.user_rating and execution.user_rating >= 4 else 0.7
        )

        # Learn optimal execution modes
        mode_key = f"{execution.task_complexity}:{len(execution.agents_used)}"
        self.db.save_knowledge(
            category="execution_modes",
            key=mode_key,
            value=execution.execution_mode,
            confidence=0.8
        )

    def _learn_failure_patterns(self, execution: TaskExecution):
        """Learn from failed executions."""
        # Record problematic combinations
        failure_key = f"avoid:{execution.task_complexity}:{','.join(sorted(execution.agents_used))}"
        self.db.save_knowledge(
            category="failure_patterns",
            key=failure_key,
            value={
                'reason': execution.feedback.value,
                'errors': execution.error_count,
                'lessons': execution.lessons_learned
            },
            confidence=0.9
        )

        # Identify missing capabilities
        if "capability" in str(execution.lessons_learned).lower():
            self.db.save_knowledge(
                category="capability_gaps",
                key=execution.task_description[:50],
                value=execution.lessons_learned,
                confidence=0.7
            )

    def _update_team_recommendations(self, execution: TaskExecution):
        """Update team composition recommendations."""
        # Calculate team effectiveness score
        effectiveness = self._calculate_effectiveness(execution)

        # Update pattern database
        if effectiveness > 0.7:
            pattern = TeamPattern(
                pattern_id=f"learned_{execution.task_id}",
                task_type=execution.task_complexity,
                agents=execution.agents_used,
                success_rate=1.0 if execution.success else 0.0,
                avg_duration=execution.duration_minutes,
                avg_cost=execution.cost,
                usage_count=1,
                last_used=execution.end_time,
                confidence=effectiveness
            )
            self.pattern_recognizer._save_pattern(pattern)

    def _extract_knowledge(self, execution: TaskExecution):
        """Extract reusable knowledge from execution."""
        # Extract task-to-agent mappings
        for domain in execution.task_domain:
            for agent in execution.agents_used:
                mapping_key = f"{domain}:{agent}"
                current = self.db.get_knowledge("agent_mappings", mapping_key) or {'count': 0, 'success': 0}
                current['count'] += 1
                if execution.success:
                    current['success'] += 1
                self.db.save_knowledge(
                    category="agent_mappings",
                    key=mapping_key,
                    value=current,
                    confidence=current['success'] / current['count'] if current['count'] > 0 else 0
                )

    def _trigger_adaptations(self, execution: TaskExecution):
        """Trigger system adaptations based on learning."""
        # Check if performance is degrading
        recent_executions = self.db.get_similar_executions(execution.task_description, limit=5)

        if len(recent_executions) >= 3:
            recent_success_rate = sum(1 for e in recent_executions if e.success) / len(recent_executions)

            if recent_success_rate < self.performance_thresholds['success_rate_min']:
                logger.warning(f"Performance degradation detected: {recent_success_rate:.1%} success rate")
                self._recommend_team_adjustment(execution.task_description)

    def _calculate_effectiveness(self, execution: TaskExecution) -> float:
        """Calculate overall effectiveness score."""
        score = 0.0

        # Success is most important (40%)
        if execution.success:
            score += 0.4

        # User rating (30%)
        if execution.user_rating:
            score += (execution.user_rating / 5.0) * 0.3

        # Cost efficiency (15%)
        # Assume $1 is good, $10 is bad
        cost_score = max(0, 1 - (execution.cost / 10))
        score += cost_score * 0.15

        # Speed (15%)
        # Assume 10 min is good, 120 min is bad
        speed_score = max(0, 1 - (execution.duration_minutes / 120))
        score += speed_score * 0.15

        return min(score, 1.0)

    def _recommend_team_adjustment(self, task_description: str):
        """Recommend adjustments to team composition."""
        # This would integrate with the spawner to suggest different agents
        logger.info(f"Recommending team adjustment for: {task_description}")

    def get_recommendations(self, task_description: str) -> Dict[str, Any]:
        """
        Get learned recommendations for a new task.

        This is how the system USES its accumulated knowledge.
        """
        recommendations = {
            'confidence': 0.0,
            'suggested_team': [],
            'avoid_agents': [],
            'execution_mode': 'adaptive',
            'estimated_duration': 30.0,
            'estimated_cost': 1.0,
            'similar_successes': [],
            'warnings': []
        }

        # Find similar successful executions
        similar = self.db.get_similar_executions(task_description, limit=5)
        successful = [e for e in similar if e.success]

        if successful:
            # Use the most successful team composition
            best = max(successful, key=lambda e: self._calculate_effectiveness(e))
            recommendations['suggested_team'] = best.agents_used
            recommendations['execution_mode'] = best.execution_mode
            recommendations['estimated_duration'] = best.duration_minutes
            recommendations['estimated_cost'] = best.cost
            recommendations['confidence'] = 0.8
            recommendations['similar_successes'] = [
                {'task': e.task_description[:100], 'success': e.success}
                for e in successful[:3]
            ]

        # Check for known failures to avoid
        failed = [e for e in similar if not e.success]
        if failed:
            problematic_agents = set()
            for e in failed:
                problematic_agents.update(e.agents_used)
            recommendations['avoid_agents'] = list(problematic_agents)
            recommendations['warnings'].append(f"Similar tasks have failed {len(failed)} times")

        # Apply learned patterns
        patterns = self.pattern_recognizer.analyze_execution_patterns()
        for pattern in patterns:
            if pattern.confidence > 0.7:
                recommendations['suggested_team'] = pattern.agents
                recommendations['confidence'] = pattern.confidence
                break

        return recommendations

    def get_agent_rankings(self) -> List[Tuple[str, float]]:
        """Get agents ranked by overall performance."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT agent_name,
                   (successful_tasks * 1.0 / total_tasks) * 0.4 +
                   (1 - error_rate) * 0.3 +
                   (CASE WHEN user_rating > 0 THEN user_rating / 5.0 ELSE 0.5 END) * 0.3
                   as score
            FROM agent_performance
            WHERE total_tasks > 0
            ORDER BY score DESC
        """)

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def export_insights(self) -> Dict[str, Any]:
        """Export learned insights for analysis."""
        insights = {
            'total_executions': 0,
            'success_rate': 0.0,
            'avg_cost': 0.0,
            'avg_duration': 0.0,
            'top_agents': self.get_agent_rankings()[:5],
            'discovered_patterns': len(self.pattern_recognizer.analyze_execution_patterns()),
            'specializations': self.pattern_recognizer.identify_agent_specializations(),
            'failure_patterns': self.pattern_recognizer.detect_failure_patterns()[:5]
        }

        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), AVG(CASE WHEN success THEN 1 ELSE 0 END),
                   AVG(cost), AVG(duration_minutes)
            FROM task_executions
        """)

        row = cursor.fetchone()
        if row:
            insights['total_executions'] = row[0]
            insights['success_rate'] = row[1] or 0.0
            insights['avg_cost'] = row[2] or 0.0
            insights['avg_duration'] = row[3] or 0.0

        return insights


class ReinforcementLearner:
    """
    Advanced reinforcement learning for continuous improvement.
    """

    def __init__(self, learner: AdaptiveLearner):
        self.learner = learner
        self.exploration_rate = 0.1  # 10% exploration
        self.learning_rate = 0.01
        self.discount_factor = 0.95

        # Q-table for agent-task combinations
        self.q_table = defaultdict(lambda: defaultdict(float))

    def select_team_with_exploration(self, task_description: str,
                                    available_agents: List[str]) -> List[str]:
        """Select team using epsilon-greedy strategy."""
        import random

        if random.random() < self.exploration_rate:
            # Explore: try a new combination
            team_size = random.randint(2, min(5, len(available_agents)))
            return random.sample(available_agents, team_size)
        else:
            # Exploit: use best known combination
            recommendations = self.learner.get_recommendations(task_description)
            if recommendations['confidence'] > 0.5:
                return recommendations['suggested_team']
            else:
                # Fallback to random if no good recommendation
                return random.sample(available_agents, 3)

    def update_q_value(self, state: str, action: str, reward: float):
        """Update Q-value for state-action pair."""
        old_value = self.q_table[state][action]
        self.q_table[state][action] = old_value + self.learning_rate * (reward - old_value)

    def calculate_reward(self, execution: TaskExecution) -> float:
        """Calculate reward signal from execution."""
        reward = 0.0

        # Success/failure is primary signal
        reward += 10.0 if execution.success else -5.0

        # User rating bonus
        if execution.user_rating:
            reward += (execution.user_rating - 3) * 2  # -4 to +4

        # Efficiency bonus (inverse of cost)
        reward += max(0, 5 - execution.cost)

        # Speed bonus (inverse of duration)
        reward += max(0, 60 - execution.duration_minutes) / 10

        # Penalty for errors and retries
        reward -= execution.error_count * 2
        reward -= execution.retry_count

        return reward


# Integration with the Dynamic Spawner
def integrate_learning_with_spawner():
    """
    Integrate learning system with the dynamic spawner.

    This makes the spawner use learned knowledge.
    """
    from dynamic_spawner import DynamicAgentSpawner, TaskAnalyzer

    # Monkey-patch the analyzer to use learning
    original_analyze = TaskAnalyzer.analyze

    def enhanced_analyze(self, task_description: str, context=None):
        # Get original analysis
        analysis = original_analyze(self, task_description, context)

        # Enhance with learned recommendations
        learner = AdaptiveLearner()
        recommendations = learner.get_recommendations(task_description)

        if recommendations['confidence'] > 0.6:
            # Override with learned team
            analysis.suggested_agents = recommendations['suggested_team']
            analysis.execution_mode = recommendations['execution_mode']
            analysis.estimated_cost = recommendations['estimated_cost']
            analysis.estimated_time = recommendations['estimated_duration']
            analysis.confidence = recommendations['confidence']

        return analysis

    TaskAnalyzer.analyze = enhanced_analyze

    logger.info("Learning system integrated with spawner")


# Auto-integrate on import
integrate_learning_with_spawner()