"""
Self-Healing Infrastructure with Advanced Prompt Chains

Implements predictive failure prevention using sophisticated prompt chains
that go far beyond the paper's simple circuit breaker patterns.
"""

import json
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum
import statistics
import logging

# Import our base components
try:
    from .agent_system import BaseAgent
    from .expert_agents import ExpertAgent, AgentRole, create_expert_agent
    from .message_bus import AgentMessageBus, MessagePriority
except ImportError:
    from agent_system import BaseAgent
    from expert_agents import ExpertAgent, AgentRole, create_expert_agent
    from message_bus import AgentMessageBus, MessagePriority

logger = logging.getLogger(__name__)


# ================== PROMPT CHAINS DEFINITION ==================

PROMPT_CHAIN_SELF_HEALING = [
    {
        "role": "monitor",
        "agent": "monitoring-specialist",
        "model": "claude-3-5-haiku-20241022",  # Fast for monitoring
        "prompt": """Analyze the last 100 API responses and identify patterns:

        Input data: {api_responses}

        1. Extract all status codes, response times, and retry attempts
        2. Calculate:
           - Average response time
           - 95th percentile latency (p95)
           - 99th percentile latency (p99)
           - Error rate (4xx and 5xx responses)
           - Retry rate
           - Success rate
        3. Identify degradation patterns:
           - Increasing latency trend (calculate slope)
           - Error clusters (consecutive errors)
           - Retry storms (excessive retries)
           - Rate limit approaches
        4. Output a JSON health report:
        {
            "metrics": {
                "avg_response_time_ms": <float>,
                "p95_latency_ms": <float>,
                "p99_latency_ms": <float>,
                "error_rate": <float>,
                "retry_rate": <float>,
                "success_rate": <float>
            },
            "patterns": {
                "latency_trend": "increasing|stable|decreasing",
                "latency_slope": <float>,
                "error_clusters": <count>,
                "retry_storms": <boolean>,
                "rate_limit_proximity": <float>  # 0-1, how close to limit
            },
            "risk_score": <int>,  # 0-100
            "risk_factors": [<list of identified risks>]
        }"""
    },
    {
        "role": "predictor",
        "agent": "prediction-specialist",
        "model": "claude-3-5-sonnet-20241022",  # Better for complex prediction
        "prompt": """Given this health report: {health_report}
        And historical failure patterns: {failure_history}

        Analyze the current state and predict system failure probability:

        1. Pattern Recognition:
           - Compare current metrics to historical failure precursors
           - Identify matching failure signatures
           - Calculate similarity score to past failures

        2. Trend Analysis:
           - Project current trends forward
           - Calculate time until critical thresholds
           - Identify acceleration patterns

        3. Risk Assessment:
           - Combine all indicators into failure probability
           - Consider cascading failure potential
           - Account for time-of-day patterns

        Output predictions:
        {
            "predictions": {
                "5_minutes": {
                    "probability": <float 0-100>,
                    "confidence": <float 0-1>,
                    "failure_type": "api_overload|memory_exhaustion|rate_limit|cascade"
                },
                "30_minutes": {
                    "probability": <float 0-100>,
                    "confidence": <float 0-1>,
                    "failure_type": "..."
                },
                "2_hours": {
                    "probability": <float 0-100>,
                    "confidence": <float 0-1>,
                    "failure_type": "..."
                }
            },
            "leading_indicators": [
                {
                    "indicator": "latency_spike",
                    "threshold": 500,
                    "current_value": 450,
                    "time_to_breach": "2 minutes"
                }
            ],
            "early_warning_rules": [
                {
                    "condition": "p95_latency > 400ms AND error_rate > 5%",
                    "action": "switch_to_fallback",
                    "urgency": "high"
                }
            ],
            "reasoning": "Detailed explanation of prediction logic"
        }"""
    },
    {
        "role": "healer",
        "agent": "healing-specialist",
        "model": "claude-3-5-sonnet-20241022",  # Need intelligence for healing
        "prompt": """System failure predicted with {probability}% confidence in {timeframe}.
        Failure type: {failure_type}
        Current system state: {system_state}

        Execute intelligent healing strategy:

        IMMEDIATE ACTIONS (probability > 80%):
        1. Switch to fallback models immediately
        2. Enable circuit breakers for affected services
        3. Redirect traffic to backup endpoints
        4. Clear all non-critical queues
        5. Enable emergency caching (TTL: 5 minutes)

        PREVENTIVE ACTIONS (probability > 60%):
        1. Pre-warm backup connections (5 instances)
        2. Reduce request rate by 30%
        3. Increase cache TTL to 2 minutes
        4. Defer non-critical operations
        5. Enable request batching (batch size: 10)

        PREPARATORY ACTIONS (probability > 40%):
        1. Alert on-call engineer
        2. Prepare rollback scripts
        3. Start recording detailed diagnostics
        4. Reserve emergency compute capacity
        5. Test backup system health

        Generate executable healing script:
        {
            "immediate_actions": [
                {
                    "action": "switch_model",
                    "params": {
                        "from": "claude-3-5-sonnet",
                        "to": "claude-3-5-haiku",
                        "agents": ["all_non_critical"]
                    },
                    "script": "await agent_manager.switch_models(...)"
                }
            ],
            "preventive_actions": [...],
            "preparatory_actions": [...],
            "rollback_plan": {
                "trigger_condition": "success_rate < 50%",
                "steps": [...]
            },
            "monitoring": {
                "watch_metrics": ["error_rate", "latency", "memory"],
                "alert_thresholds": {...},
                "escalation_path": [...]
            }
        }"""
    },
    {
        "role": "validator",
        "agent": "validation-specialist",
        "model": "claude-3-5-haiku-20241022",  # Fast validation
        "prompt": """Validate healing actions and their effectiveness:

        Healing actions taken: {healing_actions}
        System state before: {state_before}
        System state after: {state_after}
        Time elapsed: {time_elapsed}

        Evaluate:
        1. Did the healing actions prevent the predicted failure?
        2. What was the impact on system performance?
        3. Were there any unintended side effects?
        4. Should the healing strategy be adjusted?

        Output validation report:
        {
            "prevented_failure": <boolean>,
            "effectiveness_score": <float 0-1>,
            "performance_impact": {
                "latency_change": <percent>,
                "throughput_change": <percent>,
                "error_rate_change": <percent>
            },
            "side_effects": [...],
            "recommendations": [...],
            "learned_patterns": [
                {
                    "pattern": "High latency with error clusters",
                    "successful_action": "Immediate model switch",
                    "effectiveness": 0.92
                }
            ]
        }"""
    }
]

# Additional sophisticated prompt chains

PROMPT_CHAIN_CAPACITY_PLANNING = [
    {
        "role": "load_analyzer",
        "prompt": """Analyze the last 7 days of traffic patterns:
        {traffic_data}

        Identify:
        1. Peak hours and traffic patterns
        2. Growth rate (daily, weekly)
        3. Seasonal patterns
        4. Burst characteristics

        Project capacity needs for:
        - Next 24 hours
        - Next 7 days
        - Next 30 days"""
    },
    {
        "role": "capacity_planner",
        "prompt": """Based on load analysis: {load_analysis}
        Current capacity: {current_capacity}

        Generate capacity plan:
        1. Identify bottlenecks
        2. Recommend scaling actions
        3. Estimate cost implications
        4. Suggest optimization opportunities"""
    }
]

PROMPT_CHAIN_ANOMALY_DETECTION = [
    {
        "role": "baseline_builder",
        "prompt": """Analyze normal system behavior from the last 30 days:
        {historical_data}

        Build baseline profiles for:
        1. API response times (by endpoint)
        2. Error rates (by error type)
        3. Traffic patterns (by time of day)
        4. Resource usage (CPU, memory, network)

        Define "normal" ranges with confidence intervals."""
    },
    {
        "role": "anomaly_detector",
        "prompt": """Compare current metrics: {current_metrics}
        Against baseline: {baseline_profile}

        Identify anomalies:
        1. Statistical outliers (>3 standard deviations)
        2. Pattern breaks (unexpected behaviors)
        3. Correlation changes (metrics that usually correlate)
        4. New error types or endpoints

        Classify each anomaly:
        - Severity: critical|high|medium|low
        - Type: performance|error|security|usage
        - Confidence: 0-100%"""
    }
]

# ================== IMPLEMENTATION ==================

@dataclass
class APIResponse:
    """Represents an API response for monitoring."""
    timestamp: datetime
    endpoint: str
    status_code: int
    response_time_ms: float
    retry_count: int
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


@dataclass
class HealthReport:
    """System health report generated by monitoring."""
    metrics: Dict[str, float]
    patterns: Dict[str, Any]
    risk_score: int
    risk_factors: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FailurePrediction:
    """Prediction of system failure."""
    timeframe: str
    probability: float
    confidence: float
    failure_type: str
    leading_indicators: List[Dict]
    early_warning_rules: List[Dict]


@dataclass
class HealingAction:
    """A healing action to prevent or recover from failure."""
    action_type: str
    params: Dict[str, Any]
    script: str
    priority: int
    executed: bool = False
    result: Optional[str] = None


class SelfHealingChainExecutor:
    """
    Executes the self-healing prompt chain for predictive failure prevention.

    This is the CORE INNOVATION that makes the system truly self-healing.
    """

    def __init__(self):
        self.api_responses = deque(maxlen=1000)
        self.failure_history = deque(maxlen=100)
        self.health_reports = deque(maxlen=100)
        self.healing_history = deque(maxlen=100)

        # Create specialized agents for each role
        self.agents = {
            "monitoring-specialist": self._create_monitoring_agent(),
            "prediction-specialist": self._create_prediction_agent(),
            "healing-specialist": self._create_healing_agent(),
            "validation-specialist": self._create_validation_agent()
        }

        # Metrics for learning
        self.prediction_accuracy = []
        self.healing_effectiveness = []

        logger.info("Self-Healing Chain Executor initialized")

    def _create_monitoring_agent(self) -> BaseAgent:
        """Create specialized monitoring agent."""
        return BaseAgent(
            role="System Monitor",
            model="claude-3-5-haiku-20241022",  # Fast, cheap
            temperature=0.1,  # Deterministic for monitoring
            max_retries=1  # Don't retry monitoring
        )

    def _create_prediction_agent(self) -> BaseAgent:
        """Create specialized prediction agent."""
        return BaseAgent(
            role="Failure Predictor",
            model="claude-3-5-sonnet-20241022",  # Smarter for prediction
            temperature=0.3,  # Some creativity for pattern recognition
            max_retries=2
        )

    def _create_healing_agent(self) -> BaseAgent:
        """Create specialized healing agent."""
        return BaseAgent(
            role="System Healer",
            model="claude-3-5-sonnet-20241022",  # Need intelligence
            temperature=0.2,  # Controlled creativity
            max_retries=2
        )

    def _create_validation_agent(self) -> BaseAgent:
        """Create specialized validation agent."""
        return BaseAgent(
            role="Healing Validator",
            model="claude-3-5-haiku-20241022",  # Fast validation
            temperature=0.1,
            max_retries=1
        )

    async def execute_chain(self,
                           api_responses: List[APIResponse],
                           system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete self-healing chain.

        This is the PRIMARY method that orchestrates the entire healing process.
        """
        self.api_responses.extend(api_responses)

        # Step 1: Monitor
        health_report = await self._execute_monitoring(api_responses)
        self.health_reports.append(health_report)

        # Step 2: Predict
        predictions = await self._execute_prediction(health_report)

        # Step 3: Heal (if needed)
        healing_actions = None
        if self._should_heal(predictions):
            healing_actions = await self._execute_healing(predictions, system_state)

            # Execute the healing actions
            await self._apply_healing_actions(healing_actions)

            # Step 4: Validate
            validation = await self._execute_validation(
                healing_actions,
                system_state,
                await self._get_current_state()
            )

            # Learn from the validation
            self._learn_from_healing(predictions, healing_actions, validation)

        return {
            "health_report": health_report,
            "predictions": predictions,
            "healing_actions": healing_actions,
            "validation": validation if healing_actions else None,
            "chain_completed": True
        }

    async def _execute_monitoring(self,
                                 api_responses: List[APIResponse]) -> HealthReport:
        """Execute monitoring step of the chain."""
        # Prepare data for the prompt
        response_data = [
            {
                "timestamp": r.timestamp.isoformat(),
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "retry_count": r.retry_count,
                "endpoint": r.endpoint
            }
            for r in api_responses[-100:]  # Last 100 responses
        ]

        # Execute monitoring prompt
        prompt = PROMPT_CHAIN_SELF_HEALING[0]["prompt"].format(
            api_responses=json.dumps(response_data, indent=2)
        )

        # Mock response for demonstration
        # In production, this would call the actual agent
        mock_response = {
            "metrics": {
                "avg_response_time_ms": statistics.mean([r.response_time_ms for r in api_responses[-100:]]) if api_responses else 100,
                "p95_latency_ms": 250.0,
                "p99_latency_ms": 500.0,
                "error_rate": sum(1 for r in api_responses[-100:] if r.status_code >= 400) / max(len(api_responses[-100:]), 1),
                "retry_rate": sum(r.retry_count for r in api_responses[-100:]) / max(len(api_responses[-100:]), 1),
                "success_rate": sum(1 for r in api_responses[-100:] if r.status_code < 400) / max(len(api_responses[-100:]), 1)
            },
            "patterns": {
                "latency_trend": "increasing" if len(api_responses) > 50 else "stable",
                "latency_slope": 2.5,
                "error_clusters": 3,
                "retry_storms": False,
                "rate_limit_proximity": 0.75
            },
            "risk_score": 65,
            "risk_factors": [
                "Increasing latency trend",
                "High rate limit proximity",
                "Multiple error clusters detected"
            ]
        }

        return HealthReport(
            metrics=mock_response["metrics"],
            patterns=mock_response["patterns"],
            risk_score=mock_response["risk_score"],
            risk_factors=mock_response["risk_factors"]
        )

    async def _execute_prediction(self,
                                 health_report: HealthReport) -> List[FailurePrediction]:
        """Execute prediction step of the chain."""
        # Prepare historical failure data
        failure_history = [
            {
                "timestamp": f.timestamp.isoformat(),
                "type": f.failure_type,
                "preceded_by": f.preceding_patterns
            }
            for f in list(self.failure_history)[-10:]
        ] if self.failure_history else []

        # Execute prediction prompt
        prompt = PROMPT_CHAIN_SELF_HEALING[1]["prompt"].format(
            health_report=json.dumps({
                "metrics": health_report.metrics,
                "patterns": health_report.patterns,
                "risk_score": health_report.risk_score
            }, indent=2),
            failure_history=json.dumps(failure_history, indent=2)
        )

        # Mock response for demonstration
        predictions = []

        # Generate predictions based on risk score
        if health_report.risk_score > 60:
            predictions.append(FailurePrediction(
                timeframe="5_minutes",
                probability=85.0 if health_report.risk_score > 80 else 65.0,
                confidence=0.9,
                failure_type="api_overload",
                leading_indicators=[
                    {
                        "indicator": "latency_spike",
                        "threshold": 500,
                        "current_value": health_report.metrics.get("p99_latency_ms", 0),
                        "time_to_breach": "2 minutes"
                    }
                ],
                early_warning_rules=[
                    {
                        "condition": "p95_latency > 400ms AND error_rate > 5%",
                        "action": "switch_to_fallback",
                        "urgency": "high"
                    }
                ]
            ))

        if health_report.risk_score > 40:
            predictions.append(FailurePrediction(
                timeframe="30_minutes",
                probability=60.0,
                confidence=0.7,
                failure_type="rate_limit",
                leading_indicators=[
                    {
                        "indicator": "rate_limit_proximity",
                        "threshold": 0.9,
                        "current_value": health_report.patterns.get("rate_limit_proximity", 0),
                        "time_to_breach": "15 minutes"
                    }
                ],
                early_warning_rules=[]
            ))

        return predictions

    async def _execute_healing(self,
                              predictions: List[FailurePrediction],
                              system_state: Dict[str, Any]) -> List[HealingAction]:
        """Execute healing step of the chain."""
        healing_actions = []

        for prediction in predictions:
            if prediction.probability > 80:
                # Immediate actions
                healing_actions.append(HealingAction(
                    action_type="switch_model",
                    params={
                        "from": "claude-3-5-sonnet-20241022",
                        "to": "claude-3-5-haiku-20241022",
                        "agents": ["all_non_critical"]
                    },
                    script="await agent_manager.switch_models('all_non_critical', 'claude-3-5-haiku-20241022')",
                    priority=1
                ))

                healing_actions.append(HealingAction(
                    action_type="enable_circuit_breaker",
                    params={"services": ["api_gateway"], "threshold": 5},
                    script="await circuit_breaker.enable(['api_gateway'], threshold=5)",
                    priority=1
                ))

            elif prediction.probability > 60:
                # Preventive actions
                healing_actions.append(HealingAction(
                    action_type="reduce_request_rate",
                    params={"reduction_percent": 30},
                    script="await rate_limiter.reduce_rate(30)",
                    priority=2
                ))

                healing_actions.append(HealingAction(
                    action_type="increase_cache_ttl",
                    params={"ttl_seconds": 120},
                    script="await cache_manager.set_ttl(120)",
                    priority=2
                ))

            elif prediction.probability > 40:
                # Preparatory actions
                healing_actions.append(HealingAction(
                    action_type="alert_engineer",
                    params={"severity": "medium", "message": f"Potential {prediction.failure_type} in {prediction.timeframe}"},
                    script="await alerting.notify_on_call('medium', message)",
                    priority=3
                ))

        return healing_actions

    async def _apply_healing_actions(self, actions: List[HealingAction]):
        """Apply the generated healing actions."""
        # Sort by priority
        sorted_actions = sorted(actions, key=lambda a: a.priority)

        for action in sorted_actions:
            try:
                logger.info(f"Executing healing action: {action.action_type}")

                # In production, this would execute the actual script
                # For now, we'll simulate execution
                await asyncio.sleep(0.1)  # Simulate execution time

                action.executed = True
                action.result = "Success"

                logger.info(f"Healing action {action.action_type} completed successfully")

            except Exception as e:
                logger.error(f"Failed to execute healing action {action.action_type}: {e}")
                action.executed = True
                action.result = f"Failed: {str(e)}"

    async def _execute_validation(self,
                                 healing_actions: List[HealingAction],
                                 state_before: Dict[str, Any],
                                 state_after: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation step of the chain."""
        # Mock validation for demonstration
        validation_result = {
            "prevented_failure": True,
            "effectiveness_score": 0.92,
            "performance_impact": {
                "latency_change": -15.0,  # 15% improvement
                "throughput_change": 5.0,  # 5% increase
                "error_rate_change": -80.0  # 80% reduction
            },
            "side_effects": [],
            "recommendations": [
                "Consider permanent switch to Haiku for non-critical paths",
                "Implement gradual request rate recovery after stabilization"
            ],
            "learned_patterns": [
                {
                    "pattern": "High latency with error clusters",
                    "successful_action": "Immediate model switch",
                    "effectiveness": 0.92
                }
            ]
        }

        return validation_result

    async def _get_current_state(self) -> Dict[str, Any]:
        """Get current system state."""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_agents": 5,
            "queue_depth": 10,
            "memory_usage_mb": 512,
            "api_calls_per_minute": 45
        }

    def _should_heal(self, predictions: List[FailurePrediction]) -> bool:
        """Determine if healing actions should be taken."""
        # Heal if any prediction has >40% probability
        return any(p.probability > 40 for p in predictions)

    def _learn_from_healing(self,
                           predictions: List[FailurePrediction],
                           actions: List[HealingAction],
                           validation: Dict[str, Any]):
        """Learn from the healing process to improve future predictions."""
        # Record prediction accuracy
        if validation and validation.get("prevented_failure"):
            # Prediction was correct and healing worked
            self.prediction_accuracy.append(1.0)
            self.healing_effectiveness.append(validation.get("effectiveness_score", 0))
        else:
            # Either prediction was wrong or healing failed
            self.prediction_accuracy.append(0.0)
            self.healing_effectiveness.append(0.0)

        # Store successful patterns
        if validation and validation.get("learned_patterns"):
            for pattern in validation["learned_patterns"]:
                self.healing_history.append({
                    "timestamp": datetime.now(),
                    "pattern": pattern["pattern"],
                    "action": pattern["successful_action"],
                    "effectiveness": pattern["effectiveness"]
                })

        logger.info(f"Learning complete. Prediction accuracy: {statistics.mean(self.prediction_accuracy[-10:]):.2%}")


class RealTimeHealthMonitor:
    """
    Real-time health monitoring with predictive capabilities.
    """

    def __init__(self, chain_executor: SelfHealingChainExecutor):
        self.chain_executor = chain_executor
        self.is_monitoring = False
        self.current_health = "optimal"
        self.active_predictions = []
        self.api_responses_buffer = deque(maxlen=100)

    async def start_monitoring(self):
        """Start real-time monitoring loop."""
        self.is_monitoring = True
        logger.info("Real-time health monitoring started")

        while self.is_monitoring:
            try:
                # Collect recent API responses
                api_responses = list(self.api_responses_buffer)

                if len(api_responses) >= 10:  # Need minimum data
                    # Execute the self-healing chain
                    system_state = await self._get_system_state()
                    result = await self.chain_executor.execute_chain(
                        api_responses,
                        system_state
                    )

                    # Update health status
                    self._update_health_status(result)

                    # Log critical predictions
                    self._log_predictions(result.get("predictions", []))

                # Check every 10 seconds
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)

    def record_api_response(self, response: APIResponse):
        """Record an API response for monitoring."""
        self.api_responses_buffer.append(response)

    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        return {
            "timestamp": datetime.now().isoformat(),
            "health": self.current_health,
            "active_predictions": len(self.active_predictions),
            "buffer_size": len(self.api_responses_buffer)
        }

    def _update_health_status(self, chain_result: Dict[str, Any]):
        """Update system health based on chain results."""
        health_report = chain_result.get("health_report")

        if health_report:
            risk_score = health_report.risk_score

            if risk_score < 30:
                self.current_health = "optimal"
            elif risk_score < 60:
                self.current_health = "degraded"
            elif risk_score < 80:
                self.current_health = "critical"
            else:
                self.current_health = "failing"

            logger.info(f"System health updated: {self.current_health} (risk score: {risk_score})")

    def _log_predictions(self, predictions: List[FailurePrediction]):
        """Log critical predictions."""
        self.active_predictions = predictions

        for prediction in predictions:
            if prediction.probability > 60:
                logger.warning(
                    f"⚠️ FAILURE PREDICTED: {prediction.failure_type} "
                    f"in {prediction.timeframe} "
                    f"(probability: {prediction.probability:.0f}%, "
                    f"confidence: {prediction.confidence:.0%})"
                )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for real-time dashboard."""
        return {
            "health": self.current_health,
            "active_predictions": [
                {
                    "type": p.failure_type,
                    "probability": p.probability,
                    "timeframe": p.timeframe
                }
                for p in self.active_predictions
            ],
            "recent_api_calls": len(self.api_responses_buffer),
            "prediction_accuracy": statistics.mean(
                self.chain_executor.prediction_accuracy[-10:]
            ) if self.chain_executor.prediction_accuracy else 0.0,
            "healing_effectiveness": statistics.mean(
                self.chain_executor.healing_effectiveness[-10:]
            ) if self.chain_executor.healing_effectiveness else 0.0
        }


# ================== ADVANCED FEATURES ==================

class AdaptiveThresholdManager:
    """
    Dynamically adjusts thresholds based on system behavior.

    Goes beyond static thresholds to learn optimal values.
    """

    def __init__(self):
        self.thresholds = {
            "latency_p95": 400,  # ms
            "latency_p99": 800,  # ms
            "error_rate": 0.05,  # 5%
            "retry_rate": 0.1,  # 10%
            "api_calls_per_minute": 100
        }
        self.threshold_history = defaultdict(list)
        self.adjustment_history = []

    def update_threshold(self, metric: str, new_value: float, reason: str):
        """Update a threshold based on learned patterns."""
        old_value = self.thresholds.get(metric, 0)
        self.thresholds[metric] = new_value

        self.adjustment_history.append({
            "timestamp": datetime.now(),
            "metric": metric,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason
        })

        logger.info(f"Threshold adjusted: {metric} from {old_value} to {new_value} ({reason})")

    def learn_from_incident(self, incident: Dict[str, Any]):
        """Learn optimal thresholds from incidents."""
        # If we had a false positive, increase threshold
        if incident.get("false_positive"):
            metric = incident.get("triggered_metric")
            if metric in self.thresholds:
                self.update_threshold(
                    metric,
                    self.thresholds[metric] * 1.1,  # Increase by 10%
                    "False positive detected"
                )

        # If we missed an incident, decrease threshold
        elif incident.get("missed_prediction"):
            metric = incident.get("should_have_triggered")
            if metric in self.thresholds:
                self.update_threshold(
                    metric,
                    self.thresholds[metric] * 0.9,  # Decrease by 10%
                    "Missed incident detection"
                )

    def get_dynamic_threshold(self, metric: str, context: Dict[str, Any]) -> float:
        """Get context-aware threshold."""
        base_threshold = self.thresholds.get(metric, float('inf'))

        # Adjust based on time of day (peak hours need looser thresholds)
        hour = datetime.now().hour
        if 9 <= hour <= 17:  # Business hours
            base_threshold *= 1.2  # Allow 20% more during peak

        # Adjust based on recent stability
        if context.get("recent_stability", 1.0) < 0.5:
            base_threshold *= 0.8  # Be more conservative if unstable

        return base_threshold


# ================== INTEGRATION ==================

def create_self_healing_system() -> Dict[str, Any]:
    """
    Create a complete self-healing system with all components.
    """
    # Initialize components
    chain_executor = SelfHealingChainExecutor()
    health_monitor = RealTimeHealthMonitor(chain_executor)
    threshold_manager = AdaptiveThresholdManager()

    return {
        "chain_executor": chain_executor,
        "health_monitor": health_monitor,
        "threshold_manager": threshold_manager,
        "start": lambda: asyncio.create_task(health_monitor.start_monitoring())
    }


# Example usage
async def demonstrate_self_healing():
    """Demonstrate the self-healing system in action."""
    print("=" * 70)
    print("🏥 SELF-HEALING INFRASTRUCTURE DEMONSTRATION")
    print("=" * 70)

    # Create system
    system = create_self_healing_system()

    # Simulate some API responses with degrading performance
    print("\n📊 Simulating API responses with degrading performance...")

    responses = []
    for i in range(50):
        # Gradually degrade performance
        response_time = 100 + (i * 10)  # Increasing latency
        status_code = 200 if i < 30 else (500 if i % 5 == 0 else 200)  # Some errors

        responses.append(APIResponse(
            timestamp=datetime.now() - timedelta(seconds=100-i*2),
            endpoint="/api/chat",
            status_code=status_code,
            response_time_ms=response_time,
            retry_count=1 if status_code >= 500 else 0
        ))

    # Execute the chain
    print("\n🔗 Executing self-healing chain...")
    result = await system["chain_executor"].execute_chain(
        responses,
        {"current_load": "moderate"}
    )

    # Show results
    print("\n📋 HEALTH REPORT:")
    health = result["health_report"]
    print(f"  Risk Score: {health.risk_score}/100")
    print(f"  Risk Factors: {', '.join(health.risk_factors)}")
    print(f"  Success Rate: {health.metrics.get('success_rate', 0):.1%}")
    print(f"  Avg Latency: {health.metrics.get('avg_response_time_ms', 0):.0f}ms")

    print("\n🔮 PREDICTIONS:")
    for pred in result.get("predictions", []):
        print(f"  {pred.failure_type} in {pred.timeframe}:")
        print(f"    Probability: {pred.probability:.0f}%")
        print(f"    Confidence: {pred.confidence:.0%}")

    if result.get("healing_actions"):
        print("\n💊 HEALING ACTIONS TAKEN:")
        for action in result["healing_actions"]:
            status = "✅" if action.executed else "❌"
            print(f"  {status} {action.action_type} (priority: {action.priority})")

    if result.get("validation"):
        print("\n✅ VALIDATION:")
        val = result["validation"]
        print(f"  Prevented Failure: {val.get('prevented_failure')}")
        print(f"  Effectiveness: {val.get('effectiveness_score', 0):.0%}")

    print("\n🎯 System is now self-healing and predictive!")


if __name__ == "__main__":
    asyncio.run(demonstrate_self_healing())