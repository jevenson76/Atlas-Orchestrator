"""
CSV generation module for project plans.

This module handles efficient CSV generation with support for large datasets,
custom field ordering, and export formats compatible with MS Project, Jira, and Asana.
"""

import csv
import io
from typing import List, Dict, Optional, Set
from pathlib import Path

import pandas as pd

from .models import ProjectTask, ExtendedProjectTask


class CSVGenerator:
    """
    Generate optimized CSV output for project plans.

    Supports both standard csv module for smaller datasets and pandas
    for high-performance processing of large projects.
    """

    # Standard field order for CSV output
    STANDARD_FIELDS = [
        'task_id', 'task_name', 'wbs_code', 'task_type', 'description',
        'start_date', 'end_date', 'duration_days',
        'status', 'percent_complete', 'priority',
        'assigned_to', 'owner',
        'predecessors', 'successors', 'dependency_type',
        'estimated_cost', 'actual_cost',
        'is_critical', 'slack_days',
        'created_date', 'modified_date',
        'notes', 'tags'
    ]

    # Extended fields for ExtendedProjectTask
    EXTENDED_FIELDS = [
        'estimated_hours', 'actual_hours', 'resource_allocation',
        'risk_level', 'quality_gate',
        'jira_key', 'asana_gid', 'ms_project_id',
        'custom_fields'
    ]

    def __init__(
        self,
        tasks: List[ProjectTask],
        include_extended_fields: bool = True
    ):
        """
        Initialize CSV generator.

        Args:
            tasks: List of ProjectTask objects
            include_extended_fields: Whether to include extended fields
        """
        self.tasks = tasks
        self.include_extended = include_extended_fields

        # Determine fields based on task type
        self.fields = self.STANDARD_FIELDS.copy()
        if include_extended_fields and any(
            isinstance(t, ExtendedProjectTask) for t in tasks
        ):
            self.fields.extend(self.EXTENDED_FIELDS)

    def generate(self, output_path: Optional[Path] = None) -> str:
        """
        Generate CSV using standard csv module.

        Args:
            output_path: Optional file path to write CSV

        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.fields,
            extrasaction='ignore'
        )

        # Write header
        writer.writeheader()

        # Write task rows
        for task in self.tasks:
            row = task.to_csv_row()
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)

        return csv_content

    def generate_with_pandas(
        self,
        output_path: Optional[Path] = None,
        chunk_size: int = 1000
    ) -> pd.DataFrame:
        """
        Generate CSV using pandas for better performance with large datasets.

        Args:
            output_path: Optional file path to write CSV
            chunk_size: Chunk size for processing (helps with memory management)

        Returns:
            DataFrame with task data
        """
        # Convert tasks to dictionaries
        task_dicts = [task.to_csv_row() for task in self.tasks]

        # Create DataFrame
        df = pd.DataFrame(task_dicts, columns=self.fields)

        # Optimize data types
        df = self._optimize_dtypes(df)

        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(
                output_path,
                index=False,
                encoding='utf-8',
                chunksize=chunk_size if len(df) > chunk_size else None
            )

        return df

    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame data types for memory efficiency.

        Args:
            df: Input DataFrame

        Returns:
            Optimized DataFrame
        """
        # Convert date columns to datetime
        date_cols = ['start_date', 'end_date', 'created_date', 'modified_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Convert numeric columns
        numeric_cols = [
            'duration_days', 'percent_complete',
            'estimated_cost', 'actual_cost', 'slack_days'
        ]
        if self.include_extended:
            numeric_cols.extend(['estimated_hours', 'actual_hours', 'resource_allocation'])

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Convert boolean columns
        bool_cols = ['is_critical']
        if self.include_extended:
            bool_cols.append('quality_gate')

        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        return df

    def export_to_ms_project(self, output_path: Path) -> None:
        """
        Export to Microsoft Project compatible CSV format.

        MS Project expects specific column names and formats.

        Args:
            output_path: Output file path
        """
        # MS Project field mapping
        ms_project_fields = {
            'task_id': 'ID',
            'task_name': 'Name',
            'wbs_code': 'WBS',
            'duration_days': 'Duration',
            'start_date': 'Start',
            'end_date': 'Finish',
            'percent_complete': '% Complete',
            'predecessors': 'Predecessors',
            'assigned_to': 'Resource Names',
            'notes': 'Notes',
            'priority': 'Priority',
            'estimated_cost': 'Cost',
            'task_type': 'Type'
        }

        # Create DataFrame and rename columns
        df = self.generate_with_pandas()
        ms_project_df = df.rename(columns=ms_project_fields)

        # Select only MS Project columns
        ms_project_cols = list(ms_project_fields.values())
        ms_project_df = ms_project_df[[col for col in ms_project_cols if col in ms_project_df.columns]]

        # Format dates for MS Project (MM/DD/YYYY)
        for col in ['Start', 'Finish']:
            if col in ms_project_df.columns:
                ms_project_df[col] = pd.to_datetime(ms_project_df[col]).dt.strftime('%m/%d/%Y')

        # Format duration (remove 'days' suffix if present)
        if 'Duration' in ms_project_df.columns:
            ms_project_df['Duration'] = ms_project_df['Duration'].astype(str) + 'd'

        # Write to CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ms_project_df.to_csv(output_path, index=False, encoding='utf-8')

    def export_summary_report(self, output_path: Path) -> None:
        """
        Generate summary report with project statistics.

        Args:
            output_path: Output file path for summary report
        """
        df = self.generate_with_pandas()

        summary = {
            'Total Tasks': len(df),
            'Critical Tasks': df['is_critical'].sum() if 'is_critical' in df else 0,
            'Completed Tasks': (df['status'] == 'Completed').sum() if 'status' in df else 0,
            'In Progress Tasks': (df['status'] == 'In Progress').sum() if 'status' in df else 0,
            'Not Started Tasks': (df['status'] == 'Not Started').sum() if 'status' in df else 0,
            'Total Estimated Cost': df['estimated_cost'].sum() if 'estimated_cost' in df else 0,
            'Total Actual Cost': df['actual_cost'].sum() if 'actual_cost' in df else 0,
            'Average Completion': df['percent_complete'].mean() if 'percent_complete' in df else 0,
            'Total Duration (days)': df['duration_days'].sum() if 'duration_days' in df else 0
        }

        # Priority breakdown
        if 'priority' in df.columns:
            priority_counts = df['priority'].value_counts().to_dict()
            for priority, count in priority_counts.items():
                summary[f'{priority} Priority Tasks'] = count

        # Resource breakdown
        if 'assigned_to' in df.columns:
            resource_counts = df['assigned_to'].value_counts().head(10).to_dict()
            summary['Top Resources'] = resource_counts

        # Write summary to text file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PROJECT SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")

            for key, value in summary.items():
                if isinstance(value, dict):
                    f.write(f"\n{key}:\n")
                    for k, v in value.items():
                        f.write(f"  {k}: {v}\n")
                elif isinstance(value, float):
                    f.write(f"{key}: {value:.2f}\n")
                else:
                    f.write(f"{key}: {value}\n")


class CSVImporter:
    """Import project tasks from CSV files."""

    def __init__(self, use_pandas: bool = True):
        """
        Initialize CSV importer.

        Args:
            use_pandas: Use pandas for faster import (default True)
        """
        self.use_pandas = use_pandas

    def import_from_csv(
        self,
        file_path: Path,
        task_class: type = ProjectTask
    ) -> List[ProjectTask]:
        """
        Import tasks from CSV file.

        Args:
            file_path: Path to CSV file
            task_class: Task class to instantiate (ProjectTask or ExtendedProjectTask)

        Returns:
            List of ProjectTask objects
        """
        if self.use_pandas:
            return self._import_with_pandas(file_path, task_class)
        else:
            return self._import_with_csv(file_path, task_class)

    def _import_with_pandas(
        self,
        file_path: Path,
        task_class: type
    ) -> List[ProjectTask]:
        """Import using pandas for performance."""
        df = pd.read_csv(file_path, encoding='utf-8')

        tasks = []
        for _, row in df.iterrows():
            task_data = self._row_to_dict(row)
            try:
                task = task_class(**task_data)
                tasks.append(task)
            except Exception as e:
                # Log error but continue processing
                print(f"Warning: Failed to import task {task_data.get('task_id')}: {e}")

        return tasks

    def _import_with_csv(
        self,
        file_path: Path,
        task_class: type
    ) -> List[ProjectTask]:
        """Import using standard csv module."""
        tasks = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                task_data = self._row_to_dict(row)
                try:
                    task = task_class(**task_data)
                    tasks.append(task)
                except Exception as e:
                    print(f"Warning: Failed to import task {task_data.get('task_id')}: {e}")

        return tasks

    def _row_to_dict(self, row: Dict[str, any]) -> Dict[str, any]:
        """
        Convert CSV row to task dictionary.

        Handles type conversions and list parsing.

        Args:
            row: CSV row as dictionary

        Returns:
            Dictionary suitable for task instantiation
        """
        from datetime import datetime
        from decimal import Decimal

        task_data = {}

        # Handle each field with appropriate type conversion
        for key, value in row.items():
            if pd.isna(value) or value == '':
                continue

            # Convert date fields
            if key in ['start_date', 'end_date', 'created_date', 'modified_date']:
                task_data[key] = datetime.fromisoformat(str(value))

            # Convert list fields (semicolon-separated)
            elif key in ['predecessors', 'successors', 'tags', 'safety_requirements']:
                task_data[key] = [v.strip() for v in str(value).split(';') if v.strip()]

            # Convert decimal fields
            elif key in ['duration_days', 'estimated_cost', 'actual_cost', 'slack_days',
                         'estimated_hours', 'actual_hours', 'resource_allocation',
                         'materials_cost', 'labor_cost']:
                task_data[key] = Decimal(str(value))

            # Convert integer fields
            elif key in ['percent_complete', 'story_points', 'bug_count', 'ms_project_id']:
                task_data[key] = int(float(value))

            # Convert boolean fields
            elif key in ['is_critical', 'quality_gate', 'code_review_required', 'permit_required']:
                task_data[key] = str(value).lower() in ['true', '1', 'yes']

            # Handle enum fields - pass as string, Pydantic will convert
            elif key in ['task_type', 'status', 'priority', 'dependency_type', 'risk_level']:
                task_data[key] = str(value)

            # All other fields as string
            else:
                task_data[key] = str(value)

        return task_data
