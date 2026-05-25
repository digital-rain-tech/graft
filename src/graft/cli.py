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
    except (ValueError, NotImplementedError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    console.print(f"Reader: [bold]{type(reader).__name__}[/]")
    console.print(f"Parsing [bold]{source_file}[/]...\n")

    report = reader.read(source_file)

    table = Table(title=f"Report: {report.name}", show_lines=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")

    table.add_row("Platform", report.source_platform.value)
    table.add_row("Data Sources", str(len(report.data_sources)))
    table.add_row("Calculated Fields", str(len(report.calculated_fields)))
    table.add_row("Pages", str(len(report.pages)))
    total_visuals = sum(len(p.visuals) for p in report.pages)
    table.add_row("Visuals", str(total_visuals))
    table.add_row("Filters", str(len(report.filters)))

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
def analyze(source_file: str):
    """Analyze a BI report's structure, complexity, and translation readiness."""
    click.echo("Not yet implemented.")


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
    type=click.Choice(["json", "markdown", "yaml"]),
    default="json",
)
@click.argument("source_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
def export(fmt: str, source_file: str, output: str | None):
    """Export the parsed IR to JSON, Markdown, or YAML."""
    click.echo(f"Export format: {fmt}")
    click.echo("Not yet implemented.")


if __name__ == "__main__":
    main()
