# -*- coding: utf-8 -*-
"""Arricchimento dati prodotto da fonti ONLINE, con i NOSTRI tool (no WebSearch/WebFetch nativi).

Pipeline (metodo albero applicato ai nostri strumenti):
  topic + intento -> Groq genera ALBERO query (temp 0, ripetibile)
                  -> Tavily cerca (web, API nostra)  [+ Firecrawl per scrape mirato]
                  -> Groq ESTRAE i campi struttura citando la frase-fonte (anti-invenzione)
                  -> merge coi dati Amazon

Key in ~/.tiktok_keys (GROQ_KEY..4, TAVILY_KEY..4) e ~/.env (FIRECRAWL_*). Rotazione su 429.
"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path

import httpx

# ---------- key loading ----------
def _load_keys() -> dict:
    keys = {}
    for fn in (Path.home() / ".tiktok_keys", Path.home() / ".env"):
        try:
            for line in fn.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    keys[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return keys

_K = _load_keys()
_GROQ = [_K[k] for k in ("GROQ_KEY", "GROQ_KEY2", "GROQ_KEY3", "GROQ_KEY4") if _K.get(k)]
_TAVILY = [_K[k] for k in ("TAVILY_KEY", "TAVILY_KEY2", "TAVILY_KEY3", "TAVILY_KEY4") if _K.get(k)]
_FIRECRAWL = [_K[k] for k in ("FIRECRAWL_API_KEY", "FIRECRAWL_KEY2", "FIRECRAWL_KEY3") if _K.get(k)]
_SUPADATA = _K.get("SUPADATA_KEY", "")

GROQ_MODEL = "llama-3.3-70b-versatile"


# ---------- Groq (con rotazione key su 429/errore) ----------
def groq_chat(prompt: str, *, system: str = "", json_mode: bool = False,
              temperature: float = 0.0, max_tokens: int = 1024) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    body = {"model": GROQ_MODEL, "messages": msgs, "temperature": temperature,
            "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    last = ""
    for key in _GROQ or [""]:
        try:
            r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                           headers={"Authorization": f"Bearer {key}"},
                           json=body, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            last = f"{r.status_code}:{r.text[:100]}"
            if r.status_code in (429, 401, 403):
                continue  # prova prossima key
        except Exception as e:
            last = str(e)
            continue
    raise RuntimeError(f"groq fallito: {last}")


def _json_loads_loose(s: str):
    """Estrae il primo blocco JSON da un testo (Groq a volte aggiunge prosa)."""
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"[\[{].*[\]}]", s, re.S)
        if m:
            return json.loads(m.group(0))
        raise


# ---------- albero query ----------
def query_tree(topic: str, intent: str, n: int = 6, *, lang: str = "en") -> list[str]:
    """Groq genera n query mirate per cercare `intent` su `topic`. Ripetibile (temp 0)."""
    sys = ("Sei un esperto di ricerca prodotti. Genera query di ricerca web mirate, "
           "specifiche e DIVERSE tra loro (angoli diversi), per trovare l'informazione richiesta. "
           "Rispondi SOLO con JSON: {\"queries\": [\"...\", ...]}.")
    p = (f"Prodotto/tema: {topic}\nInformazione da trovare: {intent}\n"
         f"Lingua query preferita: {lang}. Numero query: {n}. "
         f"Includi termini tecnici e siti utili (recensioni, schede ufficiali, youtube).")
    out = groq_chat(p, system=sys, json_mode=True, temperature=0.0)
    try:
        data = _json_loads_loose(out)
        qs = data.get("queries") or []
        return [q for q in qs if isinstance(q, str)][:n]
    except Exception:
        return []


# ---------- Tavily (ricerca web, API nostra) ----------
def tavily_search(query: str, *, max_results: int = 5, depth: str = "basic") -> list[dict]:
    for key in _TAVILY or [""]:
        try:
            r = httpx.post("https://api.tavily.com/search",
                           json={"api_key": key, "query": query, "max_results": max_results,
                                 "search_depth": depth, "include_answer": False},
                           timeout=40)
            if r.status_code == 200:
                return r.json().get("results", [])
            if r.status_code in (429, 401, 432):
                continue
        except Exception:
            continue
    return []


# ---------- Firecrawl (scrape mirato in markdown) ----------
def firecrawl_scrape(url: str, *, timeout: float = 60.0) -> str:
    for key in _FIRECRAWL or [""]:
        try:
            r = httpx.post("https://api.firecrawl.dev/v1/scrape",
                           headers={"Authorization": f"Bearer {key}"},
                           json={"url": url, "formats": ["markdown"]}, timeout=timeout)
            if r.status_code == 200:
                return r.json().get("data", {}).get("markdown", "") or ""
            if r.status_code in (429, 401, 402):
                continue
        except Exception:
            continue
    return ""


# ---------- YouTube transcript (Supadata) ----------
def youtube_transcript(url_or_id: str, *, timeout: float = 45.0) -> str:
    """Trascrizione di un video YouTube (testo). Vuoto se fallisce."""
    if not _SUPADATA:
        return ""
    try:
        r = httpx.get("https://api.supadata.ai/v1/youtube/transcript",
                      params={"url": url_or_id, "text": "true"},
                      headers={"x-api-key": _SUPADATA}, timeout=timeout)
        if r.status_code == 200:
            try:
                j = r.json()
                return j.get("content") or j.get("text") or (r.text if isinstance(r.text, str) else "")
            except Exception:
                return r.text
    except Exception:
        pass
    return ""


def _yt_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/|/watch\?v=)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


# ---------- estrazione campi (anti-invenzione: cita la fonte) ----------
def extract_fields(text: str, fields: list[str], *, context: str = "") -> dict:
    """Groq estrae i campi richiesti dal testo. Ogni campo: {value, source_quote}.
    value=null se non trovato (NIENTE invenzioni)."""
    sys = ("Estrai SOLO dati presenti nel testo. Per ogni campo dai un oggetto "
           "{\"value\": <valore o null>, \"source_quote\": <frase esatta dal testo o null>}. "
           "Se il dato non c'e', value=null. NON inventare. Rispondi SOLO JSON.")
    p = (f"Contesto: {context}\nCampi da estrarre: {', '.join(fields)}\n\n"
         f"TESTO:\n{text[:8000]}")
    out = groq_chat(p, system=sys, json_mode=True, temperature=0.0, max_tokens=1200)
    try:
        return _json_loads_loose(out)
    except Exception:
        return {}


# ---------- pipeline completa ----------
def enrich(topic: str, fields: list[str], *, intent: str = "", n_queries: int = 5,
           per_query: int = 4, scrape_top: int = 0, lang: str = "en", verbose: bool = False) -> dict:
    """Cerca online e estrae i campi. Ritorna {fields:{...}, sources:[...], queries:[...]}."""
    intent = intent or f"specifiche tecniche: {', '.join(fields)}"
    queries = query_tree(topic, intent, n_queries, lang=lang)
    if verbose:
        print("  albero:", queries)
    corpus, sources = [], []
    seen = set()
    spec_sites = ("crutchfield", "sonicelectronix", "manufacturer", "jbl.", "pioneer",
                  "alpine", "kicker", "rockford", "hertz", "caraudio")
    for q in queries:
        for res in tavily_search(q, max_results=per_query):
            u = res.get("url")
            if u and u not in seen:
                seen.add(u)
                sources.append({"title": res.get("title"), "url": u})
                corpus.append(f"[{res.get('title','')}] {res.get('content','')}")
    # scrape profondo: prima i siti-scheda noti, poi le altre pagine (dimensioni spesso solo li').
    # + trascrizione dei video YouTube.
    yt_done = 0
    for s in sources:
        u = s["url"]
        if ("youtube.com" in u or "youtu.be" in u) and yt_done < 2:
            tr = youtube_transcript(u)
            if tr:
                corpus.append(f"[VIDEO {s['title']}]\n{tr[:6000]}")
                s["kind"] = "video-transcript"
                yt_done += 1
    # ordina i non-youtube: spec-sites prima
    non_yt = [s for s in sources if "youtube" not in s["url"] and "youtu.be" not in s["url"]]
    non_yt.sort(key=lambda s: 0 if any(k in s["url"].lower() for k in spec_sites) else 1)
    budget = max(scrape_top, 3)
    for s in non_yt[:budget]:
        md = firecrawl_scrape(s["url"])
        if md:
            corpus.append(f"[SCHEDA {s['title']}]\n{md[:7000]}")
            s["kind"] = "scraped-specs"
    text = "\n\n".join(corpus)
    fld = extract_fields(text, fields, context=topic) if text else {}
    return {"topic": topic, "fields": fld, "sources": sources, "queries": queries}


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "JBL BassPro Nano underseat subwoofer"
    flds = ["RMS power W", "frequency response Hz range", "external dimensions cm",
            "impedance ohm", "bass quality from reviews"]
    res = enrich(topic, flds, verbose=True)
    print(json.dumps(res, ensure_ascii=False, indent=2))
