# -*- coding: utf-8 -*-
"""Entry-point robusto: evita lo shadow di rich.py (rogue in home).

Mette la home in FONDO a sys.path: le librerie vere (rich, httpx deps) in
site-packages vincono, e amazon_search resta importabile.
Uso: python <path>/amazon_search  oppure  python -m amazon_search (da parent sicuro).
"""
import sys
from pathlib import Path

# console Windows e' cp1252: caratteri come Omega/accenti crashano print().
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_home = str(Path.home())
while _home in sys.path:
    sys.path.remove(_home)
sys.path.append(_home)  # priorita' minima: non fa ombra a site-packages

from amazon_search.main import main  # noqa: E402

if __name__ == "__main__":
    main()
