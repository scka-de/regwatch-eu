"""CLI for regwatch-eu."""

from __future__ import annotations

import os

import click
import pandas as pd
from rich.console import Console
from rich.table import Table

from regwatch import DEFAULT_CACHE_DIR, RegWatch, __version__

console = Console()


def _get_cache_dir() -> str:
    return os.environ.get("REGWATCH_CACHE_DIR", DEFAULT_CACHE_DIR)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Monitor EU regulatory changes.

    Track DORA, MiCA, AI Act, PSD3, AMLD6 across EUR-Lex, ESMA and EBA.
    """


@cli.command()
@click.option("--source", default=None, help="Only fetch from this source (eurlex, esma, eba).")
def update(source):
    """Fetch latest changes from all sources."""
    with RegWatch(cache_dir=_get_cache_dir()) as rw:
        stats = rw.update(source=source)
    for src_id, count in stats.items():
        if count == -1:
            console.print(f"Fetching {src_id}... [red]ERROR[/red]")
        else:
            console.print(f"Fetching {src_id}... {count} new items")
    total = sum(c for c in stats.values() if c > 0)
    failed = sum(1 for c in stats.values() if c == -1)
    msg = f"Cache updated: {total} new regulatory changes"
    if failed:
        msg += f" ({failed} source(s) failed)"
    console.print(msg)


@cli.command()
@click.option("--regulation", default=None, help="Filter by regulation (comma-separated).")
@click.option("--since", default=None, help="Only changes after this date (YYYY-MM-DD).")
@click.option("--type", "doc_type", default=None, help="Filter by document type.")
@click.option("--source", default=None, help="Filter by source.")
@click.option("--format", "fmt", default="table", help="Output format: table, json, csv.")
def check(regulation, since, doc_type, source, fmt):
    """Query regulatory changes from local cache."""
    with RegWatch(cache_dir=_get_cache_dir()) as rw:
        regs = regulation.split(",") if regulation else None
        types = [doc_type] if doc_type else None
        sources = [source] if source else None
        df = rw.check(regulations=regs, since=since, types=types, sources=sources)
    if fmt == "json":
        click.echo(df.to_json(orient="records", date_format="iso", indent=2))
    elif fmt == "csv":
        click.echo(df.to_csv(index=False))
    else:
        if df.empty:
            console.print("No regulatory changes found.")
            return
        table = Table(title="Regulatory Changes")
        table.add_column("Date", style="cyan")
        table.add_column("Reg", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Source")
        table.add_column("Title", max_width=60)
        for _, row in df.iterrows():
            reg = row["regulation"]
            table.add_row(
                str(row["date"]),
                str(reg) if pd.notna(reg) else "---",
                str(row["type"]),
                str(row["source"]),
                str(row["title"])[:60],
            )
        console.print(table)


@cli.command()
def status():
    """Show cache info and last update time."""
    with RegWatch(cache_dir=_get_cache_dir()) as rw:
        df = rw.check(since="2000-01-01")
    console.print(f"regwatch-eu v{__version__}\n")
    console.print(f"Cache: {_get_cache_dir()}/cache.db")
    if df.empty:
        console.print("\nTotal: 0 items")
        return
    console.print("\nItems by source:")
    for src, count in df["source"].value_counts().items():
        console.print(f"  {src:10} {count}")
    console.print("\nItems by regulation:")
    for reg, count in df["regulation"].fillna("unclassified").value_counts().items():
        console.print(f"  {reg:10} {count}")
    console.print(f"\nTotal: {len(df)} items")


@cli.command()
def regulations():
    """List supported regulations."""
    from regwatch.registry import get_regulations as _get_regs

    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    for reg in _get_regs():
        table.add_row(reg.id, reg.name)
    console.print(table)
