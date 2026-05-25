"""Graft CLI — AI-native BI report translation between platforms."""

import click
from rich.console import Console
from rich.table import Table

from graft import __version__

console = Console()


@click.group()
@click.version_option(version=__version__)
def main():
    """Graft: Transplant BI reports between platforms."""
    pass


@main.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "auto"]),
    default="auto",
    help="Source format. Auto-detected from file extension if omitted.",
)
def ingest(source_file: str, fmt: str):
    """Parse a BI report file into Graft's intermediate representation."""
    from graft.readers.registry import resolve_reader

    try:
        reader = resolve_reader(source_file, fmt)
    except (ValueError, NotImplementedError, ImportError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    console.print(f"Reader: [bold]{type(reader).__name__}[/]")
    console.print(f"Parsing [bold]{source_file}[/]...\n")

    report = reader.read(source_file)

    table = Table(title=f"Report: {report.name}", show_lines=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    table.add_row("Platform", report.platform.value)
    table.add_row("Data Sources", str(len(report.data_sources)))
    table.add_row("Calculated Fields", str(len(report.calculated_fields)))
    table.add_row("Pages", str(len(report.pages)))
    total_visuals = sum(len(p.visuals) for p in report.pages)
    table.add_row("Visuals", str(total_visuals))
    total_filters = (
        len(report.filters)
        + sum(len(p.filters) for p in report.pages)
        + sum(len(v.filters) for p in report.pages for v in p.visuals)
    )
    table.add_row("Filters", str(total_filters))

    console.print(table)


@main.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--target",
    required=True,
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase"]),
    help="Target BI platform.",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
def translate(source_file: str, target: str, output: str | None):
    """Translate a BI report from one platform to another."""
    console.print(f"Translating [bold]{source_file}[/] → [bold]{target}[/]")
    click.echo("Not yet implemented.")


@main.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "auto"]),
    default="auto",
    help="Source format for parsing.",
)
def analyze(source_file: str, fmt: str):
    """Analyze a BI report's structure, complexity, and translation readiness."""
    from graft.analysis.complexity import analyze_complexity
    from graft.readers.registry import resolve_reader

    try:
        reader = resolve_reader(source_file, fmt)
    except (ValueError, NotImplementedError, ImportError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    report = reader.read(source_file)
    result = analyze_complexity(report)

    table = Table(title=f"Analysis: {result.report_name}", show_lines=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    table.add_row(
        "Complexity",
        f"[{'red' if result.complexity_score == 'high' else 'yellow' if result.complexity_score == 'medium' else 'green'}]{result.complexity_score}[/]",
    )
    table.add_row("Data Sources", str(result.total_data_sources))
    table.add_row("Calculated Fields", str(result.total_calculated_fields))
    table.add_row("Pages (total)", str(result.total_pages))
    table.add_row("  Worksheets", str(result.details.get("worksheets", 0)))
    table.add_row("  Dashboards", str(result.details.get("dashboards", 0)))
    table.add_row("Visuals", str(result.total_visuals))
    table.add_row("Filters", str(result.total_filters))
    table.add_row("Unique Chart Types", str(result.unique_chart_types))

    console.print(table)


@main.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.argument("translated_file", type=click.Path(exists=True))
def validate(source_file: str, translated_file: str):
    """Compare source and translated reports for semantic equivalence."""
    click.echo("Not yet implemented.")


@main.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "markdown"]),
    default="json",
)
@click.argument("source_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option(
    "--format-source",
    "source_fmt",
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "auto"]),
    default="auto",
    help="Source format for parsing.",
)
def export(fmt: str, source_file: str, output: str | None, source_fmt: str):
    """Export the parsed IR to JSON or Markdown."""
    from pathlib import Path

    from graft.export import export_report
    from graft.readers.registry import resolve_reader

    try:
        reader = resolve_reader(source_file, source_fmt)
    except (ValueError, NotImplementedError, ImportError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    report = reader.read(source_file)
    result = export_report(report, fmt)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        console.print(f"Exported to [bold]{output}[/]")
    else:
        click.echo(result)


if __name__ == "__main__":
    main()
