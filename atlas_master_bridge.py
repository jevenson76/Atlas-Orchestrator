"""
Atlas Master Bridge - Connects Streamlit UI to Real MasterOrchestrator

Integrates the ACTUAL multi-workflow orchestration system with Atlas:
- MasterOrchestrator (auto-selects workflow)
- SpecializedRolesOrchestrator (4-phase: ARCHITECT → DEVELOPER → TESTER → REVIEWER)
- ParallelDevelopmentOrchestrator (distributed execution)
- ProgressiveEnhancementOrchestrator (tier escalation with brutal critic)

Handles Streamlit event loop compatibility.
"""

import json
import time
import asyncio
import nest_asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

# Fix event loop for Streamlit
nest_asyncio.apply()

from multi_ai_workflow import MasterOrchestrator, WorkflowType


class AtlasMasterBridge:
    """
    Bridge between Atlas UI and MasterOrchestrator system.

    Routes tasks through the intelligent workflow selector which chooses:
    - Specialized Roles (complex, high-quality tasks)
    - Parallel Development (multi-component tasks)
    - Progressive Enhancement (simple/fast tasks with tier escalation)
    """

    def __init__(self, event_callback: Optional[Callable] = None, project_root: str = "/mnt/d/Dev"):
        """
        Initialize bridge to MasterOrchestrator.

        Args:
            event_callback: Function to call for progress events
            project_root: Project root for validation
        """
        self.event_callback = event_callback or self._default_callback
        self.project_root = project_root

        # Initialize REAL MasterOrchestrator
        self.master = MasterOrchestrator(project_root=project_root)

        # Thread pool for async execution (avoids Streamlit event loop conflicts)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def _default_callback(self, agent: str, action: str, **kwargs):
        """Default event handler."""
        print(f"[{agent}] {action}")

    def emit_event(self, agent: str, action: str, model: str = "", **kwargs):
        """Emit progress event to Streamlit UI."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "model": model,
            **kwargs
        }
        self.event_callback(agent, action, model=model, **kwargs)
        return event

    def process_task(
        self,
        task_data: Dict[str, Any],
        output_path: Optional[Path] = None,
        workflow: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process task using MasterOrchestrator.

        Args:
            task_data: Task configuration from Atlas UI
            output_path: Where to save results
            workflow: Workflow type ('auto', 'specialized_roles', 'parallel', 'progressive')

        Returns:
            Processing result with output and metadata
        """
        start_time = time.time()
        task_id = task_data.get("task_id", "unknown")

        # Step 1: Task received
        self.emit_event(
            agent="Atlas Master Bridge",
            action=f"Task {task_id} received - routing to MasterOrchestrator",
            progress=0
        )

        # Step 2: Build comprehensive prompt from task data
        source_files_config = task_data.get('user_prompt', {}).get('source_files', {})
        directory = source_files_config.get('directory', '')

        # Convert Windows path to WSL path if needed
        if directory.startswith('C:\\') or directory.startswith('C:/'):
            directory = directory.replace('C:\\', '/mnt/c/').replace('C:/', '/mnt/c/').replace('\\', '/')

        self.emit_event(
            agent="File Manager",
            action=f"Scanning ALL files from: {directory}",
            model="File System",
            progress=5
        )

        # Read ALL source files from directory
        files_content = {}
        directory_path = Path(directory)

        if directory_path.exists() and directory_path.is_dir():
            text_extensions = {'.txt', '.md', '.csv', '.json', '.html'}

            for file_path in directory_path.iterdir():
                if not file_path.is_file():
                    continue

                suffix = file_path.suffix.lower()

                # Handle text files
                if suffix in text_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            files_content[file_path.name] = f.read()
                    except Exception:
                        pass

                # Handle PDF files
                elif suffix == '.pdf':
                    try:
                        import PyPDF2
                        with open(file_path, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            text_parts = []
                            for page in pdf_reader.pages:
                                text_parts.append(page.extract_text())
                            files_content[file_path.name] = '\n\n'.join(text_parts)
                    except Exception:
                        pass

            self.emit_event(
                agent="File Manager",
                action=f"✅ Loaded {len(files_content)} files (including PDFs)",
                model="File System",
                progress=10
            )

        # Build comprehensive task prompt
        task_rules = task_data.get('user_prompt', {}).get('task_generation_rules', [])
        system_message = task_data.get('system_message', '')

        # Create compact file summaries instead of full content to avoid CLI arg limits
        file_summaries = {}
        for filename, content in files_content.items():
            lines = content.split('\n')
            file_summaries[filename] = {
                'size_kb': round(len(content.encode('utf-8')) / 1024, 1),
                'lines': len(lines),
                'preview': '\n'.join(lines[:10]) if len(lines) > 0 else '',  # First 10 lines only
                'type': Path(filename).suffix
            }

        comprehensive_task = f"""{system_message}

SOURCE FILES ({len(files_content)} files analyzed - summaries with previews provided):
{json.dumps(file_summaries, indent=2)}

TASK GENERATION RULES:
{json.dumps(task_rules, indent=2)}

Based on the file summaries (size, line count, type, and 10-line preview) and task generation rules above, generate a comprehensive CSV project plan with all tasks, dependencies, timelines, and resource assignments."""

        # Build context (WITHOUT full files_content to avoid CLI arg limit)
        # File summaries are already embedded in comprehensive_task prompt above
        context = {
            "language": "csv",
            "quality_target": 90,  # High quality for project plans
            "task_rules": task_rules,
            "file_count": len(files_content),
            "file_names": list(files_content.keys())
        }

        # Step 3: Route to MasterOrchestrator
        self.emit_event(
            agent="Master Orchestrator",
            action=f"Analyzing task to select optimal workflow (mode: {workflow})...",
            model="Workflow Router",
            progress=10
        )

        # Execute in thread pool to avoid event loop conflicts
        future = self.executor.submit(
            self._run_master_orchestrator,
            comprehensive_task,
            workflow,
            context
        )

        # Monitor progress
        last_progress = 10
        while not future.done():
            time.sleep(2)
            last_progress = min(last_progress + 5, 85)
            self.emit_event(
                agent="Orchestrator",
                action="Processing with selected workflow...",
                progress=last_progress
            )

        result = future.result()

        # Step 4: Extract results
        duration = time.time() - start_time

        workflow_used = result.get('workflow_used', 'unknown')
        final_output = result.get('output', '')
        quality_score = result.get('quality_score', 0)

        self.emit_event(
            agent="Result Processor",
            action=f"✅ Workflow complete - Used: {workflow_used} | Quality: {quality_score}/100",
            model=workflow_used,
            progress=90
        )

        # Show phase breakdown if available
        phases = result.get('phases', [])
        if phases:
            phase_summary = " → ".join([f"{p.get('phase', '?')} ({p.get('status', '?')})" for p in phases])
            self.emit_event(
                agent="Workflow Report",
                action=f"Phases: {phase_summary}",
                model=workflow_used,
                progress=92
            )

        # Step 5: Save output
        if output_path:
            self.emit_event(
                agent="File Writer",
                action=f"Saving results to {output_path}...",
                model="File System",
                progress=95
            )

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_output)

            self.emit_event(
                agent="File Writer",
                action=f"✅ Results saved: {output_path}",
                model="File System",
                progress=98
            )

        # Final summary
        self.emit_event(
            agent="Atlas Master Bridge",
            action=f"✅ Task {task_id} completed in {duration:.1f}s | Workflow: {workflow_used} | Quality: {quality_score}/100",
            model="Completion",
            progress=100
        )

        return {
            "task_id": task_id,
            "status": "completed",
            "output_path": str(output_path) if output_path else None,
            "duration": duration,
            "workflow_used": workflow_used,
            "quality_score": quality_score,
            "phases_completed": len(phases),
            "result": final_output
        }

    def _run_master_orchestrator(
        self,
        task: str,
        workflow: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run MasterOrchestrator in thread-safe way.

        This creates a new event loop for async execution.
        """
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Execute through MasterOrchestrator
            result = loop.run_until_complete(
                self.master.execute(
                    task=task,
                    workflow=workflow,
                    context=context
                )
            )

            # Extract final output from WorkflowResult
            # Check phase results in priority order (reviewer -> tester -> developer -> architect)
            final_output = ""
            if result.reviewer_result and result.reviewer_result.output:
                final_output = result.reviewer_result.output
            elif result.tester_result and result.tester_result.output:
                final_output = result.tester_result.output
            elif result.developer_result and result.developer_result.output:
                final_output = result.developer_result.output
            elif result.architect_result and result.architect_result.output:
                final_output = result.architect_result.output

            # Build phase info
            phases = []
            for phase_name in ['architect', 'developer', 'tester', 'reviewer']:
                phase_result = getattr(result, f'{phase_name}_result', None)
                if phase_result:
                    phases.append({
                        "phase": phase_name,
                        "status": "completed" if phase_result.success else "failed",
                        "model": phase_result.model_used,
                        "tokens": 0  # Tokens disabled per user request
                    })

            # Determine workflow type from context
            workflow_used = result.context.get('workflow_metadata', {}).get('selected_workflow', workflow)

            # Extract relevant data from WorkflowResult
            return {
                "output": final_output,
                "quality_score": result.overall_quality_score or 0,
                "workflow_used": workflow_used,
                "phases": phases,
                "context": result.context
            }
        finally:
            loop.close()
