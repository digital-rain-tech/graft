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
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "auto"]),
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


def _render_jasper_analysis(report) -> None:
    from graft.analysis.jasper_complexity import (
        ConvertibilityVerdict,
        analyze_jasper_complexity,
    )

    result = analyze_jasper_complexity(report)
    verdict_color = {
        ConvertibilityVerdict.AUTOMATIC: "green",
        ConvertibilityVerdict.ASSISTED: "yellow",
        ConvertibilityVerdict.MANUAL: "red",
    }[result.verdict]

    table = Table(title=f"Conversion Readiness: {result.report_name}", show_lines=False)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold")
    table.add_row("Verdict", f"[{verdict_color}]{result.verdict.value}[/]")
    table.add_row("Bands", str(result.band_count))
    table.add_row("Elements", str(result.element_count))
    table.add_row("Parameters", str(result.parameter_count))
    table.add_row("Fields", str(result.field_count))
    table.add_row("Variables", str(result.variable_count))
    table.add_row("Subreports", str(result.subreport_count))
    table.add_row("Components (table/list)", str(result.component_count))
    table.add_row("Expressions", str(result.expression_count))
    table.add_row("Java callouts", str(result.java_callout_count))
    console.print(table)

    if result.blockers:
        console.print("\n[bold]Conversion blockers:[/]")
        for blocker in result.blockers:
            console.print(f"  • {blocker}")


@main.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "auto"]),
    default="auto",
    help="Source format for parsing.",
)
def analyze(source_file: str, fmt: str):
    """Analyze a BI report's structure, complexity, and translation readiness."""
    from graft.analysis.complexity import analyze_complexity
    from graft.models import Platform
    from graft.readers.registry import resolve_reader

    try:
        reader = resolve_reader(source_file, fmt)
    except (ValueError, NotImplementedError, ImportError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    report = reader.read(source_file)

    if report.platform is Platform.JASPER:
        _render_jasper_analysis(report)
        return

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


def _portfolio_markdown(p) -> str:
    lines = [
        f"# Portfolio Conversion Readiness ({p.total_reports} reports)",
        "",
        "| Verdict | Reports | Share |",
        "|---|---:|---:|",
        f"| Automatic | {p.automatic} | {p.automatic_pct}% |",
        f"| Assisted | {p.assisted} | {p.assisted_pct}% |",
        f"| Manual | {p.manual} | {p.manual_pct}% |",
        "",
        f"- Reports with custom Java callouts: **{p.reports_with_java_callouts}**",
        f"- Reports with table/list components: **{p.reports_with_components}**",
        f"- Reports with subreports: **{p.reports_with_subreports}**",
        f"- Total Java callouts: {p.total_java_callouts} across {p.total_elements} elements",
        "",
        "## Per report",
        "",
        "| Report | Verdict | Bands | Elements | Java | Components | Subreports |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in p.per_report:
        lines.append(
            f"| {r.report_name} | {r.verdict.value} | {r.band_count} | {r.element_count} "
            f"| {r.java_callout_count} | {r.component_count} | {r.subreport_count} |"
        )
    return "\n".join(lines) + "\n"


def _render_portfolio(p) -> None:
    table = Table(
        title=f"Portfolio Conversion Readiness ({p.total_reports} reports)",
        show_lines=False,
    )
    table.add_column("Verdict", style="cyan", no_wrap=True)
    table.add_column("Reports", style="bold", justify="right")
    table.add_column("Share", style="bold", justify="right")
    table.add_row("[green]Automatic[/]", str(p.automatic), f"{p.automatic_pct}%")
    table.add_row("[yellow]Assisted[/]", str(p.assisted), f"{p.assisted_pct}%")
    table.add_row("[red]Manual[/]", str(p.manual), f"{p.manual_pct}%")
    console.print(table)
    console.print(
        f"\nSignals: {p.reports_with_java_callouts} report(s) with custom Java, "
        f"{p.reports_with_components} with table/list components, "
        f"{p.reports_with_subreports} with subreports "
        f"({p.total_java_callouts} Java callouts across {p.total_elements} elements)."
    )


@main.command()
@click.argument("source_path", type=click.Path(exists=True))
@click.option("-r", "--recursive", is_flag=True, help="Recurse into subdirectories.")
@click.option("--output", "-o", type=click.Path(), help="Write a Markdown summary here.")
def portfolio(source_path: str, recursive: bool, output: str | None):
    """Aggregate conversion-readiness across many JasperReports (.jrxml) files."""
    from pathlib import Path

    from graft.analysis.jasper_complexity import (
        analyze_jasper_complexity,
        analyze_portfolio,
    )
    from graft.readers.jasper import JasperReader

    p = Path(source_path)
    if p.is_dir():
        files = sorted(p.rglob("*.jrxml") if recursive else p.glob("*.jrxml"))
    else:
        files = [p]

    if not files:
        console.print(f"[bold red]Error:[/] no .jrxml files found under {source_path}")
        raise SystemExit(1)

    reader = JasperReader()
    results = []
    for f in files:
        try:
            results.append(analyze_jasper_complexity(reader.read(str(f))))
        except Exception as e:  # noqa: BLE001 — one bad file shouldn't sink the batch
            console.print(f"[yellow]skipped {f.name}: {e}[/]")

    report = analyze_portfolio(results)
    _render_portfolio(report)

    if output:
        Path(output).write_text(_portfolio_markdown(report), encoding="utf-8")
        console.print(f"\nWrote summary to [bold]{output}[/]")


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
    type=click.Choice(["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "auto"]),
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
