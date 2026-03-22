"""
Shared display helpers for CLI output.
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

_console = Console()


def banner(text: str) -> None:
    """Print a prominent banner line."""
    _console.print()
    _console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    _console.print(f"[bold cyan]  {text}[/bold cyan]")
    _console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    _console.print()


def header(text: str) -> None:
    """Print a section header."""
    _console.print(f"\n[bold green]--- {text} ---[/bold green]")


def val(label: str, value: object) -> None:
    """Print a label-value pair."""
    _console.print(f"  [dim]{label}:[/dim] {value}")


def table(title: str, columns: list[str], rows: list[list[object]]) -> None:
    """Print a rich table."""
    t = Table(title=title, show_lines=False)
    for col in columns:
        t.add_column(col)
    for row in rows:
        t.add_row(*(str(c) for c in row))
    _console.print(t)
