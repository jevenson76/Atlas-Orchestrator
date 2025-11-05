"""
Agent Message Bus for Inter-Agent Communication

Provides pub/sub, RPC, and queue-based communication patterns
for multi-agent systems.
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class MessageType(Enum):
    """Types of messages in the system."""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    RESULT = "result"
    ERROR = "error"


@dataclass
class Message:
    """
    Message object for inter-agent communication.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.REQUEST
    from_agent: str = ""
    to_agent: Optional[str] = None
    topic: Optional[str] = None
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.ttl is None:
            return False
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    def to_json(self) -> str:
        """Serialize message to JSON."""
        data = {
            'id': self.id,
            'type': self.type.value,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'topic': self.topic,
            'payload': self.payload,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to,
            'ttl': self.ttl,
            'metadata': self.metadata
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(
            id=data['id'],
            type=MessageType(data['type']),
            from_agent=data['from_agent'],
            to_agent=data.get('to_agent'),
            topic=data.get('topic'),
            payload=data.get('payload'),
            priority=MessagePriority(data.get('priority', 3)),
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to'),
            ttl=data.get('ttl'),
            metadata=data.get('metadata', {})
        )


class MessageQueue:
    """
    Priority queue for agent messages.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues = {
            MessagePriority.CRITICAL: deque(),
            MessagePriority.HIGH: deque(),
            MessagePriority.NORMAL: deque(),
            MessagePriority.LOW: deque()
        }
        self.lock = Lock()
        self.total_messages = 0

    def put(self, message: Message) -> bool:
        """Add message to queue."""
        with self.lock:
            if self.total_messages >= self.max_size:
                logger.warning(f"Queue full, dropping message {message.id}")
                return False

            # Check if message is expired
            if message.is_expired():
                logger.debug(f"Message {message.id} expired, not queuing")
                return False

            self.queues[message.priority].append(message)
            self.total_messages += 1
            return True

    def get(self) -> Optional[Message]:
        """Get next message by priority."""
        with self.lock:
            # Check queues in priority order
            for priority in MessagePriority:
                if self.queues[priority]:
                    message = self.queues[priority].popleft()
                    self.total_messages -= 1

                    # Skip expired messages
                    if message.is_expired():
                        logger.debug(f"Skipping expired message {message.id}")
                        return self.get()  # Recursive call to get next

                    return message
            return None

    def peek(self) -> Optional[Message]:
        """Peek at next message without removing."""
        with self.lock:
            for priority in MessagePriority:
                if self.queues[priority]:
                    return self.queues[priority][0]
            return None

    def size(self) -> int:
        """Get total queue size."""
        return self.total_messages

    def clear(self):
        """Clear all messages."""
        with self.lock:
            for queue in self.queues.values():
                queue.clear()
            self.total_messages = 0


class AgentMessageBus:
    """
    Central message bus for agent communication.

    Supports:
    - Direct messaging (agent to agent)
    - Publish/Subscribe (topics)
    - Request/Response (RPC-style)
    - Broadcasting
    """

    def __init__(self,
                 max_queue_size: int = 1000,
                 enable_persistence: bool = False):
        """
        Initialize message bus.

        Args:
            max_queue_size: Maximum messages per queue
            enable_persistence: Persist messages to disk
        """
        self.max_queue_size = max_queue_size
        self.enable_persistence = enable_persistence

        # Agent queues (one per agent)
        self.agent_queues: Dict[str, MessageQueue] = {}

        # Topic subscriptions
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Pending RPC responses
        self.pending_responses: Dict[str, asyncio.Future] = {}

        # Message handlers
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Metrics
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_dropped': 0,
            'rpc_calls': 0,
            'broadcasts': 0
        }

        # Lock for thread safety
        self.lock = Lock()

        # Message history for debugging
        self.message_history: deque = deque(maxlen=100)

        logger.info("Message bus initialized")

    def register_agent(self, agent_name: str) -> bool:
        """Register an agent with the message bus."""
        with self.lock:
            if agent_name not in self.agent_queues:
                self.agent_queues[agent_name] = MessageQueue(self.max_queue_size)
                logger.info(f"Agent '{agent_name}' registered")
                return True
            return False

    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        with self.lock:
            if agent_name in self.agent_queues:
                del self.agent_queues[agent_name]
                # Remove from all subscriptions
                for topic_agents in self.subscriptions.values():
                    topic_agents.discard(agent_name)
                logger.info(f"Agent '{agent_name}' unregistered")

    def subscribe(self, agent_name: str, topics: List[str]):
        """Subscribe agent to topics."""
        with self.lock:
            for topic in topics:
                self.subscriptions[topic].add(agent_name)
                logger.debug(f"Agent '{agent_name}' subscribed to '{topic}'")

    def unsubscribe(self, agent_name: str, topics: List[str]):
        """Unsubscribe agent from topics."""
        with self.lock:
            for topic in topics:
                self.subscriptions[topic].discard(agent_name)
                logger.debug(f"Agent '{agent_name}' unsubscribed from '{topic}'")

    def publish(self,
                topic: str,
                payload: Any,
                from_agent: str,
                priority: MessagePriority = MessagePriority.NORMAL,
                ttl: Optional[int] = None) -> int:
        """
        Publish message to a topic.

        Args:
            topic: Topic to publish to
            payload: Message payload
            from_agent: Sender agent name
            priority: Message priority
            ttl: Time to live in seconds

        Returns:
            Number of agents that received the message
        """
        message = Message(
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            topic=topic,
            payload=payload,
            priority=priority,
            ttl=ttl
        )

        delivered = 0
        with self.lock:
            # Get all subscribers
            subscribers = self.subscriptions.get(topic, set())

            for agent_name in subscribers:
                if agent_name in self.agent_queues:
                    if self.agent_queues[agent_name].put(message):
                        delivered += 1
                    else:
                        self.metrics['messages_dropped'] += 1

            self.metrics['broadcasts'] += 1
            self.metrics['messages_sent'] += delivered

        # Store in history
        self.message_history.append(message)

        logger.debug(f"Published to '{topic}': delivered to {delivered} agents")
        return delivered

    def send(self,
             to_agent: str,
             payload: Any,
             from_agent: str,
             message_type: MessageType = MessageType.REQUEST,
             priority: MessagePriority = MessagePriority.NORMAL,
             correlation_id: Optional[str] = None,
             ttl: Optional[int] = None) -> bool:
        """
        Send direct message to an agent.

        Returns:
            True if message was queued, False otherwise
        """
        if to_agent not in self.agent_queues:
            logger.error(f"Agent '{to_agent}' not registered")
            return False

        message = Message(
            type=message_type,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            ttl=ttl
        )

        with self.lock:
            success = self.agent_queues[to_agent].put(message)
            if success:
                self.metrics['messages_sent'] += 1
            else:
                self.metrics['messages_dropped'] += 1

        # Store in history
        self.message_history.append(message)

        return success

    def receive(self, agent_name: str) -> Optional[Message]:
        """
        Receive next message for an agent.

        Returns:
            Next message or None if queue is empty
        """
        if agent_name not in self.agent_queues:
            return None

        message = self.agent_queues[agent_name].get()
        if message:
            self.metrics['messages_received'] += 1
            logger.debug(f"Agent '{agent_name}' received message {message.id}")

        return message

    def receive_batch(self, agent_name: str, max_messages: int = 10) -> List[Message]:
        """Receive multiple messages at once."""
        messages = []
        for _ in range(max_messages):
            message = self.receive(agent_name)
            if message is None:
                break
            messages.append(message)
        return messages

    async def call_rpc(self,
                       to_agent: str,
                       method: str,
                       params: Any,
                       from_agent: str,
                       timeout: float = 30.0) -> Any:
        """
        Make RPC-style call to another agent.

        Args:
            to_agent: Target agent
            method: Method to call
            params: Method parameters
            from_agent: Calling agent
            timeout: Response timeout in seconds

        Returns:
            Response from the called agent

        Raises:
            TimeoutError: If response not received within timeout
        """
        correlation_id = str(uuid.uuid4())

        # Create future for response
        future = asyncio.Future()
        self.pending_responses[correlation_id] = future

        # Send RPC request
        message = Message(
            type=MessageType.REQUEST,
            from_agent=from_agent,
            to_agent=to_agent,
            payload={'method': method, 'params': params},
            correlation_id=correlation_id,
            priority=MessagePriority.HIGH
        )

        if not self.send(to_agent, message.payload, from_agent,
                        MessageType.REQUEST, MessagePriority.HIGH,
                        correlation_id):
            del self.pending_responses[correlation_id]
            raise Exception(f"Failed to send RPC to {to_agent}")

        self.metrics['rpc_calls'] += 1

        try:
            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            del self.pending_responses[correlation_id]
            raise TimeoutError(f"RPC call to {to_agent}.{method} timed out")
        finally:
            # Clean up
            self.pending_responses.pop(correlation_id, None)

    def send_rpc_response(self,
                         correlation_id: str,
                         result: Any,
                         from_agent: str):
        """Send response to an RPC call."""
        if correlation_id in self.pending_responses:
            future = self.pending_responses[correlation_id]
            if not future.done():
                future.set_result(result)

    def broadcast(self,
                 payload: Any,
                 from_agent: str,
                 exclude_agents: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to all registered agents.

        Args:
            payload: Message payload
            from_agent: Sender agent
            exclude_agents: Agents to exclude from broadcast

        Returns:
            Number of agents that received the message
        """
        exclude_agents = exclude_agents or set()
        exclude_agents.add(from_agent)  # Don't send to self

        delivered = 0
        message = Message(
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            payload=payload,
            priority=MessagePriority.NORMAL
        )

        with self.lock:
            for agent_name, queue in self.agent_queues.items():
                if agent_name not in exclude_agents:
                    if queue.put(message):
                        delivered += 1

        self.metrics['broadcasts'] += 1
        logger.debug(f"Broadcast from '{from_agent}' delivered to {delivered} agents")
        return delivered

    def register_handler(self, agent_name: str, handler: Callable):
        """Register a message handler for an agent."""
        self.handlers[agent_name].append(handler)

    def process_messages(self, agent_name: str) -> int:
        """
        Process all pending messages for an agent.

        Returns:
            Number of messages processed
        """
        processed = 0
        handlers = self.handlers.get(agent_name, [])

        while True:
            message = self.receive(agent_name)
            if message is None:
                break

            # Call all registered handlers
            for handler in handlers:
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Handler error for {agent_name}: {e}")

            processed += 1

        return processed

    def get_metrics(self) -> Dict[str, Any]:
        """Get message bus metrics."""
        metrics = dict(self.metrics)

        # Add queue sizes
        metrics['queue_sizes'] = {
            agent: queue.size()
            for agent, queue in self.agent_queues.items()
        }

        # Add subscription counts
        metrics['subscription_counts'] = {
            topic: len(agents)
            for topic, agents in self.subscriptions.items()
        }

        return metrics

    def get_message_history(self,
                           agent_name: Optional[str] = None,
                           limit: int = 50) -> List[Message]:
        """Get recent message history."""
        history = list(self.message_history)

        if agent_name:
            history = [
                msg for msg in history
                if msg.from_agent == agent_name or msg.to_agent == agent_name
            ]

        return history[-limit:]

    def clear_agent_queue(self, agent_name: str):
        """Clear all messages for an agent."""
        if agent_name in self.agent_queues:
            self.agent_queues[agent_name].clear()

    def get_queue_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of an agent's queue."""
        if agent_name not in self.agent_queues:
            return {'error': 'Agent not registered'}

        queue = self.agent_queues[agent_name]
        return {
            'size': queue.size(),
            'max_size': queue.max_size,
            'next_message': queue.peek()
        }


# Global message bus instance
_message_bus_instance = None


def get_message_bus() -> AgentMessageBus:
    """Get or create the global message bus instance."""
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = AgentMessageBus()
    return _message_bus_instance


# Async message processing
class AsyncMessageProcessor:
    """
    Asynchronous message processor for agents.
    """

    def __init__(self, agent_name: str, message_bus: AgentMessageBus):
        self.agent_name = agent_name
        self.message_bus = message_bus
        self.running = False
        self.handlers: Dict[MessageType, Callable] = {}

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for message type."""
        self.handlers[message_type] = handler

    async def process_messages(self):
        """Process messages asynchronously."""
        self.running = True

        while self.running:
            message = self.message_bus.receive(self.agent_name)

            if message is None:
                await asyncio.sleep(0.1)  # No messages, wait
                continue

            # Get handler for message type
            handler = self.handlers.get(message.type)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Error processing message {message.id}: {e}")

    def stop(self):
        """Stop processing messages."""
        self.running = False