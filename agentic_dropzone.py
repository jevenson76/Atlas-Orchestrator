"""
Agentic Drop Zone (ADZ) - Zero-Touch Task Execution

The final piece of Priority 3! Drop task files, get results automatically.

Architecture:
┌─────────────────────────────────────────────────────────────┐
│ User drops task_042.json → ~/dropzone/tasks/               │
├─────────────────────────────────────────────────────────────┤
│ Watchdog detects new file                                   │
│ ADZ reads task JSON                                         │
│ MasterOrchestrator routes to optimal workflow               │
│   ├─ Specialized Roles (complex, quality=90+)              │
│   ├─ Parallel Development (multi-component)                 │
│   └─ Progressive Enhancement (simple, speed)                │
│ Executes workflow (3-8 minutes)                            │
│ Validates result                                            │
│ Saves to ~/dropzone/results/task_042_result.json          │
│ Archives task_042.json → ~/dropzone/archive/               │
│ Logs completion                                             │
└─────────────────────────────────────────────────────────────┘

ZERO HUMAN INTERVENTION!
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
import logging
import time
import traceback

# Observability
try:
    from observability.event_emitter import EventEmitter, EventType, EventSeverity
except ImportError:
    EventEmitter = None
    EventType = None
    EventSeverity = None

# File watcher (requires: pip install watchdog)
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("watchdog not installed - file watching disabled. Install with: pip install watchdog")

# Import orchestrators
try:
    from .multi_ai_workflow import MasterOrchestrator, WorkflowResult
    from .workflow_metrics import WorkflowMetricsTracker
except ImportError:
    from multi_ai_workflow import MasterOrchestrator, WorkflowResult
    from workflow_metrics import WorkflowMetricsTracker

logger = logging.getLogger(__name__)


class TaskFileHandler(FileSystemEventHandler):
    """
    Watches dropzone directory for new task files.
    Triggers execution when .json files appear.
    """

    def __init__(self, adz_instance):
        self.adz = adz_instance
        super().__init__()

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        # Only process JSON task files
        if not event.src_path.endswith('.json'):
            return

        # Ignore result/error files
        filename = Path(event.src_path).name
        if 'result' in filename or 'error' in filename:
            return

        logger.info(f"📥 New task detected: {event.src_path}")

        # Queue task for execution (run in event loop)
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.adz.process_task_file(event.src_path))
        except RuntimeError:
            # No event loop running - schedule for later
            self.adz.pending_tasks.append(event.src_path)


class AgenticDropZone:
    """
    Agentic Drop Zone - True Zero-Touch task execution.

    Drop JSON task files in tasks/ directory, results appear automatically in results/.

    Usage:
        # Start watching (runs forever)
        adz = AgenticDropZone()
        adz.start()

        # Process once and exit
        adz = AgenticDropZone()
        adz.process_existing_tasks()

    Task File Format:
        {
          "task": "Build a calculator",
          "workflow": "auto",  # auto, specialized_roles, parallel, progressive
          "context": {
            "language": "python",
            "quality_target": 90
          },
          "priority": "normal"  # low, normal, high
        }
    """

    def __init__(self, dropzone_root: Optional[Path] = None):
        """
        Initialize Agentic Drop Zone.

        Args:
            dropzone_root: Root directory for dropzone (default: ~/dropzone)
        """
        # Set up directories
        self.dropzone_root = dropzone_root or Path.home() / "dropzone"
        self.tasks_dir = self.dropzone_root / "tasks"
        self.results_dir = self.dropzone_root / "results"
        self.archive_dir = self.dropzone_root / "archive"

        # Create directories if needed
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 Dropzone initialized at: {self.dropzone_root}")
        logger.info(f"   Tasks: {self.tasks_dir}")
        logger.info(f"   Results: {self.results_dir}")
        logger.info(f"   Archive: {self.archive_dir}")

        # Initialize MasterOrchestrator
        self.master = MasterOrchestrator(project_root=str(self.dropzone_root))

        # Metrics tracking
        self.metrics = WorkflowMetricsTracker()

        # File watcher
        self.observer = None
        self.handler = None
        self.running = False

        # Pending tasks (for when event loop isn't running)
        self.pending_tasks = []

        # Stats
        self.tasks_processed = 0
        self.tasks_failed = 0

        # Initialize observability
        if EventEmitter is not None:
            self.emitter = EventEmitter(enable_console=False)
        else:
            self.emitter = None

    def start(self):
        """Start watching dropzone for new tasks (runs forever)"""
        if not WATCHDOG_AVAILABLE:
            logger.error("❌ watchdog library not installed!")
            logger.error("   Install with: pip install watchdog")
            return

        logger.info("🚀 Starting Agentic Drop Zone")
        logger.info("=" * 60)
        logger.info(f"📁 Watching: {self.tasks_dir}")
        logger.info(f"📤 Results: {self.results_dir}")
        logger.info("")
        logger.info("💡 Drop .json task files in tasks/ folder")
        logger.info("💡 Results will appear in results/ folder")
        logger.info("💡 Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Set up file watcher
        self.handler = TaskFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.tasks_dir),
            recursive=False
        )
        self.observer.start()
        self.running = True

        logger.info("✅ ADZ is now watching for tasks!")

        # Process any existing files
        asyncio.run(self.process_existing_tasks())

        try:
            # Keep running and process pending tasks
            while self.running:
                # Process any pending tasks
                while self.pending_tasks:
                    task_file = self.pending_tasks.pop(0)
                    asyncio.run(self.process_task_file(task_file))

                time.sleep(1)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching dropzone"""
        logger.info("\n🛑 Stopping Agentic Drop Zone...")
        self.running = False

        if self.observer:
            self.observer.stop()
            self.observer.join()

        logger.info(f"📊 Stats: {self.tasks_processed} processed, {self.tasks_failed} failed")
        logger.info("✅ ADZ stopped")

    async def process_existing_tasks(self):
        """Process any task files that already exist"""
        existing = list(self.tasks_dir.glob("*.json"))

        # Filter out result/error files
        existing = [f for f in existing if 'result' not in f.name and 'error' not in f.name]

        if existing:
            logger.info(f"📥 Found {len(existing)} existing task files")
            for task_file in existing:
                await self.process_task_file(str(task_file))
        else:
            logger.info("📭 No existing tasks found")

    async def process_task_file(self, filepath: str):
        """
        Process a task file from dropzone.

        Args:
            filepath: Path to task JSON file
        """
        filepath = Path(filepath)
        task_id = filepath.stem  # filename without extension

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"⚙️  Processing task: {task_id}")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Start workflow trace
        if self.emitter:
            self.emitter.start_trace(
                workflow="agentic_dropzone",
                context={"task_id": task_id, "filepath": str(filepath)}
            )

        try:
            # 1. Read task file
            task_data = self._read_task_file(filepath)
            logger.info(f"📋 Task: {task_data['task'][:100]}...")
            logger.info(f"🔄 Workflow: {task_data['workflow']}")

            # 2. Execute task
            result = await self._execute_task(task_data)

            # 3. Save results
            self._save_results(task_id, result, task_data)

            # 4. Archive task file
            self._archive_task(filepath)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Task {task_id} completed in {duration:.1f}s!")

            self.tasks_processed += 1

            # End workflow trace successfully
            if self.emitter:
                self.emitter.end_trace(
                    success=True,
                    result={
                        "task_id": task_id,
                        "quality_score": result.overall_quality_score,
                        "cost": result.total_cost_usd,
                        "duration": duration
                    }
                )

                # Emit metrics
                self.emitter.emit(
                    event_type=EventType.COST_INCURRED,
                    component="agentic-dropzone",
                    message=f"Task {task_id} cost: ${result.total_cost_usd:.4f}",
                    severity=EventSeverity.INFO,
                    cost_usd=result.total_cost_usd,
                    data={"task_id": task_id}
                )

                self.emitter.emit(
                    event_type=EventType.QUALITY_MEASURED,
                    component="agentic-dropzone",
                    message=f"Task {task_id} quality: {result.overall_quality_score}/100",
                    severity=EventSeverity.INFO,
                    quality_score=float(result.overall_quality_score),
                    data={"task_id": task_id}
                )

        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}")

            # Emit workflow failure
            if self.emitter:
                self.emitter.emit(
                    event_type=EventType.WORKFLOW_FAILED,
                    component="agentic-dropzone",
                    message=f"Task {task_id} failed: {str(e)}",
                    severity=EventSeverity.ERROR,
                    workflow="agentic_dropzone",
                    error=str(e),
                    stack_trace=traceback.format_exc(),
                    data={"task_id": task_id}
                )

                self.emitter.end_trace(success=False, result={"error": str(e)})

            self._save_error(task_id, str(e), task_data if 'task_data' in locals() else {})
            self.tasks_failed += 1

    def _read_task_file(self, filepath: Path) -> Dict:
        """Parse task JSON file"""
        try:
            with open(filepath, 'r') as f:
                task_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in task file: {e}")

        # Validate required fields
        if 'task' not in task_data:
            raise ValueError("Missing required field: 'task'")

        # Set defaults
        task_data.setdefault('workflow', 'auto')
        task_data.setdefault('context', {})
        task_data.setdefault('priority', 'normal')

        return task_data

    async def _execute_task(self, task_data: Dict) -> WorkflowResult:
        """
        Execute task via MasterOrchestrator.

        Routes to optimal workflow automatically.
        """
        task = task_data['task']
        workflow = task_data['workflow']
        context = task_data['context']

        # Add ADZ metadata to context
        context['adz'] = {
            'enabled': True,
            'dropzone_root': str(self.dropzone_root),
            'processed_at': datetime.now().isoformat()
        }

        # Execute via MasterOrchestrator
        result = await self.master.execute(
            task=task,
            workflow=workflow,
            context=context
        )

        return result

    def _save_results(self, task_id: str, result: WorkflowResult, task_data: Dict):
        """Save execution results to results directory"""
        result_file = self.results_dir / f"{task_id}_result.json"

        # Extract key info from WorkflowResult
        result_data = {
            'task_id': task_id,
            'status': 'success' if result.success else 'failed',
            'task': task_data['task'],
            'workflow_used': result.context.get('workflow_metadata', {}).get('selected_workflow', 'unknown'),
            'quality_score': result.overall_quality_score,
            'duration_seconds': result.total_execution_time_ms / 1000,
            'cost_usd': result.total_cost_usd,
            'completed_at': datetime.now().isoformat(),

            # Output
            'output': self._extract_output(result),

            # Metadata
            'metadata': result.context.get('workflow_metadata', {}),
            'validation': self._extract_validation(result),
        }

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"💾 Results saved: {result_file}")
        logger.info(f"   Quality: {result.overall_quality_score}/100")
        logger.info(f"   Duration: {result_data['duration_seconds']:.1f}s")
        logger.info(f"   Cost: ${result.total_cost_usd:.4f}")

    def _extract_output(self, result: WorkflowResult) -> str:
        """Extract output from WorkflowResult"""
        # Try to get output from developer phase
        if result.developer_result:
            return result.developer_result.output

        # Fallback to other phases
        if result.architect_result:
            return result.architect_result.output
        if result.tester_result:
            return result.tester_result.output
        if result.reviewer_result:
            return result.reviewer_result.output

        return "No output generated"

    def _extract_validation(self, result: WorkflowResult) -> Optional[Dict]:
        """Extract validation results if available"""
        if result.developer_result and result.developer_result.validation_result:
            return result.developer_result.validation_result
        return None

    def _save_error(self, task_id: str, error: str, task_data: Dict):
        """Save error information"""
        error_file = self.results_dir / f"{task_id}_error.json"

        error_data = {
            'task_id': task_id,
            'status': 'failed',
            'error': error,
            'task': task_data.get('task', 'unknown'),
            'failed_at': datetime.now().isoformat()
        }

        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)

        logger.info(f"📝 Error logged: {error_file}")

    def _archive_task(self, filepath: Path):
        """Move processed task to archive"""
        archive_path = self.archive_dir / filepath.name
        filepath.rename(archive_path)
        logger.info(f"📦 Task archived: {archive_path}")

    def status(self) -> Dict:
        """Get ADZ status"""
        return {
            'running': self.running,
            'watching': str(self.tasks_dir) if self.running else None,
            'results_dir': str(self.results_dir),
            'tasks_processed': self.tasks_processed,
            'tasks_failed': self.tasks_failed,
            'success_rate': self.tasks_processed / max(self.tasks_processed + self.tasks_failed, 1) * 100
        }


# ================== DEMONSTRATION ==================

async def demonstrate_adz():
    """Demonstrate ADZ with example tasks"""
    print("=" * 70)
    print("🎯 AGENTIC DROP ZONE DEMONSTRATION")
    print("=" * 70)

    adz = AgenticDropZone()

    print(f"\n📁 Dropzone: {adz.dropzone_root}")
    print(f"📥 Tasks: {adz.tasks_dir}")
    print(f"📤 Results: {adz.results_dir}")
    print(f"📦 Archive: {adz.archive_dir}")

    # Create example task
    example_task = {
        "task": "Create a Python function to calculate the Fibonacci sequence",
        "workflow": "progressive",
        "context": {
            "language": "python",
            "include_docstring": True
        },
        "priority": "low"
    }

    task_file = adz.tasks_dir / "demo_fibonacci.json"
    with open(task_file, 'w') as f:
        json.dump(example_task, f, indent=2)

    print(f"\n✅ Created example task: {task_file.name}")
    print("\n🔄 Processing task...")
    print("-" * 60)

    # Process the task
    await adz.process_existing_tasks()

    # Show results
    result_file = adz.results_dir / "demo_fibonacci_result.json"
    if result_file.exists():
        with open(result_file, 'r') as f:
            result = json.load(f)

        print("\n✅ TASK COMPLETED!")
        print(f"   Quality: {result['quality_score']}/100")
        print(f"   Duration: {result['duration_seconds']:.1f}s")
        print(f"   Workflow: {result['workflow_used']}")

    # Show stats
    print("\n📊 ADZ STATUS:")
    status = adz.status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 70)
    print("💡 ADZ FEATURES:")
    print("=" * 70)
    print("""
    ✅ Zero-touch task execution
    ✅ Automatic workflow selection
    ✅ Results saved automatically
    ✅ Task archiving
    ✅ Error logging
    ✅ Metrics tracking

    Perfect for: Batch processing, overnight jobs, automation pipelines
    """)


if __name__ == "__main__":
    asyncio.run(demonstrate_adz())
