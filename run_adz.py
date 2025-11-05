#!/usr/bin/env python3
"""
Agentic Drop Zone CLI Tool

Simple CLI for starting, stopping, and checking status of the ADZ file watcher.

Usage:
    python run_adz.py start              # Start watching (runs forever)
    python run_adz.py process             # Process existing tasks once (one-shot mode)
    python run_adz.py status              # Check current status
    python run_adz.py demo                # Run demonstration

Examples:
    # Start ADZ in watch mode (Ctrl+C to stop)
    python run_adz.py start

    # Process all existing task files once
    python run_adz.py process

    # Check status
    python run_adz.py status
"""

import sys
import asyncio
import argparse
from pathlib import Path
import logging

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agentic_dropzone import AgenticDropZone, demonstrate_adz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_command(args):
    """Start ADZ in watch mode (runs forever)."""
    print("=" * 70)
    print("🚀 STARTING AGENTIC DROP ZONE")
    print("=" * 70)
    print()

    # Initialize ADZ
    adz = AgenticDropZone(dropzone_root=Path(args.dropzone) if args.dropzone else None)

    print(f"📁 Dropzone: {adz.dropzone_root}")
    print(f"📥 Tasks Directory: {adz.tasks_dir}")
    print(f"📤 Results Directory: {adz.results_dir}")
    print(f"📦 Archive Directory: {adz.archive_dir}")
    print()
    print("💡 Drop JSON task files in the tasks/ directory")
    print("💡 Results will automatically appear in results/")
    print("💡 Press Ctrl+C to stop")
    print()

    # Start watching
    try:
        adz.start()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        adz.stop()


def process_command(args):
    """Process existing tasks once (one-shot mode)."""
    print("=" * 70)
    print("⚙️  PROCESSING EXISTING TASKS")
    print("=" * 70)
    print()

    # Initialize ADZ
    adz = AgenticDropZone(dropzone_root=Path(args.dropzone) if args.dropzone else None)

    print(f"📁 Dropzone: {adz.dropzone_root}")
    print(f"📥 Tasks Directory: {adz.tasks_dir}")
    print()

    # Process existing tasks
    asyncio.run(adz.process_existing_tasks())

    # Show final status
    print()
    print("=" * 70)
    print("📊 FINAL STATUS")
    print("=" * 70)
    status = adz.status()
    print(f"✅ Tasks Processed: {status['tasks_processed']}")
    print(f"❌ Tasks Failed: {status['tasks_failed']}")
    print(f"📈 Success Rate: {status['success_rate']:.1f}%")


def status_command(args):
    """Show ADZ status."""
    print("=" * 70)
    print("📊 AGENTIC DROP ZONE STATUS")
    print("=" * 70)
    print()

    # Initialize ADZ
    adz = AgenticDropZone(dropzone_root=Path(args.dropzone) if args.dropzone else None)

    # Get status
    status = adz.status()

    print(f"Running: {'✅ Yes' if status['running'] else '❌ No'}")
    print(f"Dropzone: {adz.dropzone_root}")
    print(f"Tasks Directory: {adz.tasks_dir}")
    print(f"Results Directory: {adz.results_dir}")
    print(f"Archive Directory: {adz.archive_dir}")
    print()

    # Check for pending tasks
    pending_tasks = list(adz.tasks_dir.glob("*.json"))
    pending_tasks = [f for f in pending_tasks if 'result' not in f.name and 'error' not in f.name]

    if pending_tasks:
        print(f"📥 Pending Tasks: {len(pending_tasks)}")
        for task in pending_tasks:
            print(f"   - {task.name}")
    else:
        print("📭 No pending tasks")

    print()
    print(f"✅ Tasks Processed: {status['tasks_processed']}")
    print(f"❌ Tasks Failed: {status['tasks_failed']}")
    print(f"📈 Success Rate: {status['success_rate']:.1f}%")


def demo_command(args):
    """Run ADZ demonstration."""
    print("=" * 70)
    print("🎯 RUNNING DEMONSTRATION")
    print("=" * 70)
    print()

    asyncio.run(demonstrate_adz())


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agentic Drop Zone - Zero-Touch Task Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_adz.py start                    # Start watching for tasks
  python run_adz.py process                  # Process existing tasks once
  python run_adz.py status                   # Show status
  python run_adz.py demo                     # Run demonstration
  python run_adz.py start --dropzone ~/my_dropzone  # Use custom directory
        """
    )

    # Global options
    parser.add_argument(
        '--dropzone',
        type=str,
        default=None,
        help='Custom dropzone directory (default: ~/dropzone)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Start command
    start_parser = subparsers.add_parser(
        'start',
        help='Start ADZ in watch mode (runs forever, Ctrl+C to stop)'
    )
    start_parser.set_defaults(func=start_command)

    # Process command
    process_parser = subparsers.add_parser(
        'process',
        help='Process existing tasks once (one-shot mode)'
    )
    process_parser.set_defaults(func=process_command)

    # Status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show ADZ status and pending tasks'
    )
    status_parser.set_defaults(func=status_command)

    # Demo command
    demo_parser = subparsers.add_parser(
        'demo',
        help='Run ADZ demonstration'
    )
    demo_parser.set_defaults(func=demo_command)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Run command
    args.func(args)


if __name__ == "__main__":
    main()
