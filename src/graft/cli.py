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
    type=click.Choice(
        ["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "finereport", "auto"]
    ),
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
    type=click.Choice(
        ["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "finereport", "auto"]
    ),
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
    lines.append("")
    lines.append("## What these mean")
    lines.append("")
    for term, definition in _TERMS.items():
        lines.append(f"- **{term}** — {definition}")
    return "\n".join(lines) + "\n"


_PORTFOLIO_CSS = """
:root{
  --bg:#0a1628;--surface:#132238;--text:#c8d6e5;--muted:#5a7a9b;--emph:#e8f0f8;
  --accent:#2aa198;--accent-dim:rgba(42,161,152,0.15);
  --warn:#b58900;--warn-dim:rgba(181,137,0,0.15);
  --risk:#dc322f;--risk-dim:rgba(220,50,47,0.15);--border:#1e3454;
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:'DM Sans',system-ui,-apple-system,sans-serif;font-size:18px;line-height:1.5;
  -webkit-font-smoothing:antialiased;}
.wrap{max-width:1200px;margin:0 auto;padding:64px 32px;}
.eyebrow{font-size:14px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;}
h1{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:48px;color:var(--emph);margin:8px 0 4px;}
.sub{color:var(--muted);margin:0 0 48px;}
.bar{display:flex;height:48px;border-radius:6px;overflow:hidden;border:1px solid var(--border);margin-bottom:16px;}
.seg{display:flex;align-items:center;justify-content:center;color:#0a1628;
  font-variant-numeric:tabular-nums;font-weight:700;font-size:16px;overflow:hidden;white-space:nowrap;}
.seg.automatic{background:var(--accent);}
.seg.assisted{background:var(--warn);}
.seg.manual{background:var(--risk);}
.legend{display:flex;gap:24px;color:var(--muted);font-size:14px;margin-bottom:48px;flex-wrap:wrap;}
.legend span{display:inline-flex;align-items:center;gap:8px;}
.dot{width:10px;height:10px;border-radius:2px;display:inline-block;}
.dot.automatic{background:var(--accent);}.dot.assisted{background:var(--warn);}.dot.manual{background:var(--risk);}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:48px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:24px;}
.card .label{font-size:14px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:600;}
.card .big{font-family:'Instrument Serif',Georgia,serif;font-size:40px;margin-top:8px;font-variant-numeric:tabular-nums;}
.card .pct{color:var(--muted);font-size:16px;}
.card.automatic .big{color:var(--accent);}.card.assisted .big{color:var(--warn);}.card.manual .big{color:var(--risk);}
.signals{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:24px;margin-bottom:48px;}
.signals b{color:var(--emph);}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}
th{text-align:left;font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  font-weight:600;padding:12px 16px;border-bottom:1px solid var(--border);}
th.num,td.num{text-align:right;}
td{padding:12px 16px;border-bottom:1px solid var(--border);}
td.name{font-family:'JetBrains Mono',monospace;font-size:15px;color:var(--emph);}
.pill{font-size:13px;font-weight:600;padding:4px 10px;border-radius:4px;text-transform:capitalize;}
.pill.automatic{background:var(--accent-dim);color:var(--accent);}
.pill.assisted{background:var(--warn-dim);color:var(--warn);}
.pill.manual{background:var(--risk-dim);color:var(--risk);}
footer{margin-top:48px;color:var(--muted);font-size:14px;border-top:1px solid var(--border);padding-top:24px;}
footer a{color:var(--accent);text-decoration:none;}
.help{border-bottom:1px dotted var(--muted);cursor:help;position:relative;}
.help:hover::after{content:attr(data-tip);position:absolute;left:0;top:150%;z-index:20;
  width:260px;white-space:normal;text-transform:none;letter-spacing:normal;font-weight:400;
  background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:6px;
  padding:10px 12px;font-size:13px;line-height:1.45;box-shadow:0 8px 24px rgba(0,0,0,.45);}
.help.right:hover::after{left:auto;right:0;}
h2.gloss-title{font-family:'Instrument Serif',Georgia,serif;font-weight:400;font-size:32px;
  color:var(--emph);margin:56px 0 16px;}
.glossary{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0;}
.glossary .term{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px 20px;}
.glossary dt{font-weight:600;color:var(--emph);margin-bottom:4px;}
.glossary dt .swatch{width:10px;height:10px;border-radius:2px;display:inline-block;margin-right:8px;vertical-align:middle;}
.glossary dd{margin:0;color:var(--muted);font-size:15px;line-height:1.5;}
"""


# Plain-English definitions for the conversion-readiness terms, surfaced as
# in-context tooltips on the table headers and a glossary panel. Customers
# (and downstream readers) shouldn't need to know JasperReports internals.
_TERMS: dict[str, str] = {
    "Automatic": "Converts with deterministic rules — no human needed.",
    "Assisted": "Converts with rules plus AI help; a quick human review is recommended.",
    "Manual": "Contains logic — usually embedded Java — that must be reimplemented by hand.",
    "Band": (
        "A horizontal section of the report layout (title, page header, detail rows, "
        "footer). JasperReports and FineReport are both band-based, which is why the "
        "migration is mostly mechanical."
    ),
    "Element": "A single positioned item inside a band: a label, data field, image, or line.",
    "Java callout": (
        "Custom Java embedded in an expression (e.g. QR-code or image generation). "
        "Rules can't translate it — the main driver of a Manual verdict."
    ),
    "Component": (
        "A table or list block with its own dataset. It converts, but its layout must "
        "be mapped — drives an Assisted verdict."
    ),
    "Subreport": (
        "A separate report embedded inside this one; its linked layout must be handled "
        "during conversion — drives an Assisted verdict."
    ),
}


def _portfolio_html(p) -> str:
    import datetime
    import html as _html

    generated = datetime.date.today().isoformat()

    def tip(label: str, term: str, right: bool = False) -> str:
        cls = "help right" if right else "help"
        return f'<span class="{cls}" data-tip="{_html.escape(_TERMS[term], quote=True)}">{label}</span>'

    verdict_tip = _html.escape(
        "Automatic = rules only · Assisted = rules + AI, review advised · "
        "Manual = embedded logic, reimplement by hand.",
        quote=True,
    )

    segments = ""
    for kind, count, pct in (
        ("automatic", p.automatic, p.automatic_pct),
        ("assisted", p.assisted, p.assisted_pct),
        ("manual", p.manual, p.manual_pct),
    ):
        if count:
            segments += f'<div class="seg {kind}" style="width:{pct}%">{pct}%</div>'

    rows = "\n".join(
        f'<tr><td class="name">{_html.escape(r.report_name)}</td>'
        f'<td><span class="pill {r.verdict.value}">{r.verdict.value}</span></td>'
        f'<td class="num">{r.band_count}</td>'
        f'<td class="num">{r.element_count}</td>'
        f'<td class="num">{r.java_callout_count}</td>'
        f'<td class="num">{r.component_count}</td>'
        f'<td class="num">{r.subreport_count}</td></tr>'
        for r in p.per_report
    )

    swatch = {"Automatic": "automatic", "Assisted": "assisted", "Manual": "manual"}
    glossary = ""
    for term, definition in _TERMS.items():
        dot = f'<span class="swatch dot {swatch[term]}"></span>' if term in swatch else ""
        glossary += (
            f'<div class="term"><dt>{dot}{term}</dt><dd>{_html.escape(definition)}</dd></div>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conversion Readiness — {p.total_reports} reports</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=Instrument+Serif&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{_PORTFOLIO_CSS}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="eyebrow">Graft · Conversion Readiness</div>
  <h1>JasperReports Portfolio</h1>
  <p class="sub">{p.total_reports} reports analyzed · generated {generated}</p>
</header>

<div class="bar">{segments}</div>
<div class="legend">
  <span><i class="dot automatic"></i>Automatic — rule-convertible</span>
  <span><i class="dot assisted"></i>Assisted — rules + AI</span>
  <span><i class="dot manual"></i>Manual — human reimplementation</span>
</div>

<div class="cards">
  <div class="card automatic"><div class="label">Automatic</div>
    <div class="big">{p.automatic}</div><div class="pct">{p.automatic_pct}% of portfolio</div></div>
  <div class="card assisted"><div class="label">Assisted</div>
    <div class="big">{p.assisted}</div><div class="pct">{p.assisted_pct}% of portfolio</div></div>
  <div class="card manual"><div class="label">Manual</div>
    <div class="big">{p.manual}</div><div class="pct">{p.manual_pct}% of portfolio</div></div>
</div>

<div class="signals">
  Conversion signals: <b>{p.reports_with_java_callouts}</b> report(s) with custom Java callouts,
  <b>{p.reports_with_components}</b> with table/list components,
  <b>{p.reports_with_subreports}</b> with subreports —
  <b>{p.total_java_callouts}</b> Java callouts across <b>{p.total_elements}</b> elements.
</div>

<p class="sub" style="margin:0 0 8px">Hover any column heading for a definition.</p>
<table>
<thead><tr>
  <th>Report</th>
  <th><span class="help" data-tip="{verdict_tip}">Verdict</span></th>
  <th class="num">{tip("Bands", "Band", right=True)}</th>
  <th class="num">{tip("Elements", "Element", right=True)}</th>
  <th class="num">{tip("Java", "Java callout", right=True)}</th>
  <th class="num">{tip("Components", "Component", right=True)}</th>
  <th class="num">{tip("Subreports", "Subreport", right=True)}</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>

<h2 class="gloss-title">What these mean</h2>
<dl class="glossary">
{glossary}
</dl>

<footer>
  Structural metadata only — Graft reads report definitions (structure, formulas, SQL text),
  never the data they contain; connection credentials are stripped on ingest.<br>
  Generated by <a href="https://github.com/digital-rain-tech/graft">Graft</a> · Digital Rain Technologies
</footer>
</div>
</body>
</html>
"""


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
@click.option("--output", "-o", type=click.Path(), help="Write a summary report here.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "html"]),
    default=None,
    help="Output file format. Default: inferred from --output extension, else markdown.",
)
def portfolio(source_path: str, recursive: bool, output: str | None, fmt: str | None):
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
        chosen = fmt or ("html" if output.lower().endswith((".html", ".htm")) else "markdown")
        text = _portfolio_html(report) if chosen == "html" else _portfolio_markdown(report)
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"\nWrote {chosen} summary to [bold]{output}[/]")


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
    type=click.Choice(
        ["tableau", "powerbi", "yonghong", "looker", "metabase", "jasper", "finereport", "auto"]
    ),
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
