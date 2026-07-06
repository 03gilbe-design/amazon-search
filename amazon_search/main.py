#!/usr/bin/env python3
"""Amazon product search CLI.

Usage:
  amazon-search "subwoofer 200W" --max-price 120 --min-stars 4 --specs
  amazon-search "collare cervicale" --dedup --criteria "regolabile,traspirante" --junk "cuscino"
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


def _parse_kv_list(raw: str | None) -> list[str]:
    """"a,b,c" -> ["a","b","c"], "" / None -> []"""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("query", required=False, default=None)
@click.option("--max-price", type=float, default=None, help="Prezzo massimo in €")
@click.option("--budget", type=float, default=None, help="Budget (usato da AI per ranking)")
@click.option("--min-stars", type=float, default=None, help="Stelle minime (es: 4.0)")
@click.option("--results", type=int, default=15, show_default=True, help="N. risultati da cercare")
@click.option("--specs", is_flag=True, help="Fetch specifiche tecniche top 6 (costa crediti Canopy)")
@click.option("--dedup", is_flag=True, help="Rileva stesso prodotto rivenduto a prezzi diversi (pHash foto, N download extra)")
@click.option("--montage", "make_montage", is_flag=True, help="Salva griglia numerata thumbnail per revisione visiva, IN PIÙ al report")
@click.option("--criteria", default=None, help="Criteri feature-fit, es: 'regolabile,traspirante,sostiene mento' (match su titolo+specs, più forte con --specs)")
@click.option("--junk", "junk", default=None, help="Categorie da escludere (negative sampling), es: 'cuscino,pillow' — esclusi mostrati in report, non nascosti")
@click.option("--pull-asin", "pull_asins", default=None, help="ASIN specifici da includere sempre (comma-separated), bypassano il filtro --junk")
@click.option("--suggest-queries", is_flag=True, help="Suggerisce query alternative (gratis, deterministico + AI se disponibile)")
@click.option("--categorize", "category_defs", default=None, help="Sotto-categorie per titolo, es: 'Gonfiabile:gonfiabile,inflatable|Rigido:rigido,semirigido' (ordine=priorità, primo match vince)")
@click.option("--no-llm", is_flag=True, help="Salta AI ranking e comparazione")
@click.option("--no-open", is_flag=True, help="Non aprire il browser")
@click.option("--domain", default="IT", show_default=True, help="Marketplace Amazon (es: IT, DE, UK)")
@click.option("--quota", "show_quota", is_flag=True, help="Mostra quota API ed esci")
@click.option("--cache-status", "show_cache", is_flag=True, help="Mostra cache status ed esci")
@click.option("--clear-cache", is_flag=True, help="Svuota cache ed esci")
@click.option("--test", is_flag=True, help="Esegui test suite (3 ricerche predefinite)")
@click.option("--log-summary", is_flag=True, help="Mostra riassunto log ed esci")
@click.option("--clear-log", is_flag=True, help="Svuota log ed esci")
def main(query, max_price, budget, min_stars, results, specs, dedup, make_montage,
         criteria, junk, pull_asins, suggest_queries, category_defs, no_llm, no_open, domain,
         show_quota, show_cache, clear_cache, test, log_summary, clear_log):
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

    from amazon_search import pipeline
    from amazon_search.html_gen import generate_report

    criteria_list = _parse_kv_list(criteria)
    junk_list = _parse_kv_list(junk)
    pull_list = _parse_kv_list(pull_asins)
    categories = None
    if category_defs:
        categories = {}
        for chunk in category_defs.split("|"):
            if ":" not in chunk:
                continue
            name, kws = chunk.split(":", 1)
            categories[name.strip()] = _parse_kv_list(kws)

    with console.status(f"[bold green]Cercando '{query}' su Amazon.{domain}...[/bold green]"):
        try:
            result = pipeline.run(
                query,
                max_price=max_price, min_stars=min_stars, n=results, domain=domain,
                specs=specs, dedup=dedup, rank=not no_llm, budget=budget,
                criteria={c: [c] for c in criteria_list} if criteria_list else None,
                junk_patterns={j: [j] for j in junk_list} if junk_list else None,
                pull_asins=pull_list or None,
                suggest_queries=suggest_queries,
                categories=categories,
            )
        except Exception as e:
            console.print(f"[red]Errore ricerca: {e}[/red]")
            sys.exit(1)

    if not result.products:
        console.print("[yellow]0 prodotti trovati. Prova una query diversa o rimuovi i filtri.[/yellow]")
        return

    if result.excluded:
        console.print(f"[dim]negative sampling: {len(result.excluded)} esclusi (vedi report per i motivi)[/dim]")
    if result.families:
        n_flagged = sum(1 for f in result.families if f["spread"] and f["spread"] > 2)
        console.print(f"[dim]dedup: {len(result.families)} famiglie foto-simile, {n_flagged} con differenza di prezzo rilevante[/dim]")

    montage_path = None
    if make_montage:
        from amazon_search import imagecache
        from amazon_search.montage import build_montage
        paths = {p.asin: imagecache.local_path(p.asin, domain=domain.lower())
                 for p in result.products if p.asin}
        paths = {a: fp for a, fp in paths.items() if fp}
        if paths:
            out_dir = Path.home() / "amazon_search_reports"
            out_dir.mkdir(exist_ok=True)
            price_lookup = {p.asin: p.price for p in result.products}
            items = [{"image": fp, "label": f"€{price_lookup.get(a) or '?'}"} for a, fp in paths.items()]
            montage_path = build_montage(items, out_dir / "montage.png", cols=5)
            console.print(f"[dim]montage salvato: {montage_path} (embedded nel report)[/dim]")

    # Print quick table
    table = Table(title=f"Amazon.{domain} — {query}", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Prodotto", min_width=30, max_width=50)
    table.add_column("Prezzo", justify="right", style="yellow")
    table.add_column("Stelle", justify="center")
    table.add_column("Reviews", justify="right", style="dim")
    table.add_column("Prime", justify="center")

    for i, p in enumerate(result.products, 1):
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

    if result.ai_summary:
        console.print(f"\n[bold yellow]🤖 AI:[/bold yellow] {result.ai_summary}\n")

    with console.status("[bold]Generando HTML...[/bold]"):
        html_path = generate_report(result, montage_path=montage_path)

    console.print(f"\n[green]✓ HTML salvato:[/green] {html_path}")
    console.print(f"[dim]{q.status_line()}[/dim]")

    if not no_open:
        _open_browser(html_path)


if __name__ == "__main__":
    main()
