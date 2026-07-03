#!/usr/bin/env python3
"""Amazon product search CLI.

Usage:
  amazon-search "subwoofer 200W" --max-price 120 --min-stars 4 --specs
  amazon-search --quota
"""
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _open_browser(path: Path) -> None:
    try:
        subprocess.run(["termux-open", str(path)], check=False, timeout=10)
    except FileNotFoundError:
        pass  # termux-open not available, just print path


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", required=False, default=None)
@click.option("--max-price", type=float, default=None, help="Prezzo massimo in €")
@click.option("--budget", type=float, default=None, help="Budget (usato da AI per ranking)")
@click.option("--min-stars", type=float, default=None, help="Stelle minime (es: 4.0)")
@click.option("--results", type=int, default=15, show_default=True, help="N. risultati da cercare")
@click.option("--specs", is_flag=True, help="Fetch specifiche tecniche top 3 (costa crediti Canopy)")
@click.option("--no-llm", is_flag=True, help="Salta AI ranking e comparazione")
@click.option("--no-open", is_flag=True, help="Non aprire il browser")
@click.option("--domain", default="IT", show_default=True, help="Marketplace Amazon (es: IT, DE, UK)")
@click.option("--quota", "show_quota", is_flag=True, help="Mostra quota API ed esci")
@click.option("--cache-status", "show_cache", is_flag=True, help="Mostra cache status ed esci")
@click.option("--clear-cache", is_flag=True, help="Svuota cache ed esci")
@click.option("--test", is_flag=True, help="Esegui test suite (3 ricerche predefinite)")
@click.option("--log-summary", is_flag=True, help="Mostra riassunto log ed esci")
@click.option("--clear-log", is_flag=True, help="Svuota log ed esci")
def main(query, max_price, budget, min_stars, results, specs, no_llm, no_open, domain, show_quota, show_cache, clear_cache, test, log_summary, clear_log):
    """Cerca prodotti su Amazon e apre i risultati nel browser."""
    from amazon_search import quota as q

    from amazon_search import cache

    if show_quota:
        console.print(f"[bold]Quota API Amazon Search:[/bold]")
        console.print(q.status_all())
        console.print("[dim]serpapi/canopy: reset il 1° del mese | searchapi: crediti totali[/dim]")
        return

    if show_cache:
        console.print(f"[bold]{cache.status()}[/bold]")
        return

    if clear_cache:
        cache.clear_all()
        console.print("[green]✓ Cache svuotato[/green]")
        return

    from amazon_search import logger as log_module
    from amazon_search import config_search

    if log_summary:
        log_module.print_summary()
        return

    if clear_log:
        log_module.clear_logs()
        console.print("[green]✓ Log svuotato[/green]")
        return

    if test:
        console.print("[bold]Test suite — 3 ricerche predefinite[/bold]\n")
        from amazon_search.searcher import AmazonSearcher
        searcher = AmazonSearcher()
        for i, test_cfg in enumerate(config_search.TEST_QUERIES, 1):
            try:
                console.print(f"[{i}] {test_cfg['query']}")
                products = searcher.search(
                    test_cfg["query"],
                    max_results=test_cfg["results"],
                    max_price=test_cfg["max_price"],
                    min_stars=test_cfg["min_stars"],
                    domain=domain,
                )
                console.print(f"    → {len(products)} prodotti trovati")
            except Exception as e:
                console.print(f"    [red]✗ {e}[/red]")
        console.print("\n[dim]Log salvato in ~/.amazon_search_log.jsonl[/dim]")
        return

    if not query:
        console.print("[red]Specifica una query. Es: amazon-search \"subwoofer 200W\"[/red]")
        sys.exit(1)

    from amazon_search.searcher import AmazonSearcher
    from amazon_search.specs import fetch_specs
    from amazon_search.llm import compare_products, ai_rank
    from amazon_search.html_gen import generate_html

    with console.status(f"[bold green]Cercando '{query}' su Amazon.{domain}...[/bold green]"):
        try:
            searcher = AmazonSearcher()
            products = searcher.search(
                query,
                max_results=results,
                max_price=max_price,
                min_stars=min_stars,
                domain=domain,
            )
        except Exception as e:
            console.print(f"[red]Errore ricerca: {e}[/red]")
            sys.exit(1)

    if not products:
        console.print("[yellow]0 prodotti trovati. Prova una query diversa o rimuovi i filtri.[/yellow]")
        return

    # Fetch specs for top 3 if requested
    if specs:
        top_asins = [p.asin for p in products[:3] if p.asin]
        if top_asins:
            with console.status("[bold]Fetch specifiche tecniche (Canopy)...[/bold]"):
                specs_data = fetch_specs(top_asins, domain=domain)
            for p in products:
                if p.asin in specs_data:
                    d = specs_data[p.asin]
                    p.bullets = d.get("bullets", [])
                    p.specs = d.get("specs", {})
                    p.in_stock = d.get("in_stock", p.in_stock)

    # AI ranking (reorder products best-first)
    if not no_llm and len(products) > 1:
        effective_budget = budget or max_price
        with console.status("[bold]AI ranking prodotti...[/bold]"):
            products = ai_rank(products, query, budget=effective_budget)

    # LLM comparison summary
    summary = ""
    if not no_llm and len(products) > 1:
        with console.status("[bold]AI analisi...[/bold]"):
            summary = compare_products(products, query)

    # Print quick table
    table = Table(title=f"Amazon.{domain} — {query}", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Prodotto", min_width=30, max_width=50)
    table.add_column("Prezzo", justify="right", style="yellow")
    table.add_column("Stelle", justify="center")
    table.add_column("Reviews", justify="right", style="dim")
    table.add_column("Prime", justify="center")

    for i, p in enumerate(products, 1):
        from amazon_search.html_gen import _stars
        table.add_row(
            str(i),
            p.title[:50],
            p.price_str or "N/D",
            _stars(p.stars),
            f"{p.reviews:,}" if p.reviews else "-",
            "✓" if p.prime else "",
        )

    console.print(table)

    if summary:
        console.print(f"\n[bold yellow]🤖 AI:[/bold yellow] {summary}\n")

    from amazon_search import quota as q
    quota_info = f"serpapi {q.remaining('serpapi')} | canopy {q.remaining('canopy')} | searchapi {q.remaining('searchapi')}"
    # Generate HTML
    with console.status("[bold]Generando HTML...[/bold]"):
        html_path = generate_html(
            products,
            query,
            summary=summary,
            quota_info=quota_info,
        )

    console.print(f"\n[green]✓ HTML salvato:[/green] {html_path}")
    console.print(f"[dim]{q.status_line()}[/dim]")

    if not no_open:
        _open_browser(html_path)


if __name__ == "__main__":
    main()
