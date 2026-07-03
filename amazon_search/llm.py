"""LLM layer for Amazon search analysis.

Rotates across 14 endpoints: Groq×4, Cerebras×3, Sambanova×3, OpenRouter×3, Gemini.
Tries next provider on rate-limit/error. Returns "" on total failure (non-blocking).
"""
from __future__ import annotations

import json
import os
import time

import httpx

TIMEOUT = 20.0

# Provider configs: (env_key_name, base_url, model, max_tokens_param)
_PROVIDERS = [
    # Groq — fast, free, 4 keys
    ("GROQ_KEY",  "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", "max_tokens"),
    ("GROQ_KEY2", "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", "max_tokens"),
    ("GROQ_KEY3", "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", "max_tokens"),
    ("GROQ_KEY4", "https://api.groq.com/openai/v1", "llama-3.1-8b-instant", "max_tokens"),
    # Cerebras — fastest inference, free tier
    ("CEREBRAS_KEY",  "https://api.cerebras.ai/v1", "llama3.1-8b", "max_tokens"),
    ("CEREBRAS_KEY2", "https://api.cerebras.ai/v1", "llama3.1-8b", "max_tokens"),
    ("CEREBRAS_KEY3", "https://api.cerebras.ai/v1", "llama3.1-8b", "max_tokens"),
    # Sambanova — fast, free
    ("SAMBANOVA_KEY",  "https://api.sambanova.ai/v1", "Meta-Llama-3.1-8B-Instruct", "max_tokens"),
    ("SAMBANOVA_KEY2", "https://api.sambanova.ai/v1", "Meta-Llama-3.1-8B-Instruct", "max_tokens"),
    ("SAMBANOVA_KEY3", "https://api.sambanova.ai/v1", "Meta-Llama-3.1-8B-Instruct", "max_tokens"),
    # OpenRouter — routes to free models
    ("OPENROUTER_KEY",  "https://openrouter.ai/api/v1", "meta-llama/llama-3.1-8b-instruct:free", "max_tokens"),
    ("OPENROUTER_KEY2", "https://openrouter.ai/api/v1", "meta-llama/llama-3.1-8b-instruct:free", "max_tokens"),
    ("OPENROUTER_KEY3", "https://openrouter.ai/api/v1", "meta-llama/llama-3.1-8b-instruct:free", "max_tokens"),
]


def _load_key(key_name: str) -> str:
    return os.environ.get(key_name, "")


def _call_provider(key_name: str, base_url: str, model: str, max_tok_param: str, prompt: str) -> str:
    key = _load_key(key_name)
    if not key:
        raise ValueError(f"Key {key_name} not available")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if "openrouter" in base_url:
        headers["HTTP-Referer"] = "https://termux.local"

    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                max_tok_param: 250,
                "temperature": 0.3,
            },
        )
        if resp.status_code == 429:
            raise RuntimeError("rate_limited")
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def _llm(prompt: str) -> str:
    """Try providers in order, skip on rate-limit/error."""
    for key_name, base_url, model, max_tok_param in _PROVIDERS:
        if not _load_key(key_name):
            continue
        try:
            return _call_provider(key_name, base_url, model, max_tok_param, prompt)
        except RuntimeError as e:
            if "rate_limited" in str(e):
                continue  # try next key
            continue
        except Exception:
            continue
    return ""


def compare_products(products: list, query: str) -> str:
    """1-3 sentence Italian recommendation. Returns '' on failure."""
    if not products:
        return ""

    items = []
    for p in products[:8]:
        entry = {
            "titolo": p.title[:70],
            "prezzo": p.price_str or "N/D",
            "stelle": p.stars,
            "recensioni": p.reviews,
            "prime": p.prime,
        }
        if p.specs:
            entry["specs"] = dict(list(p.specs.items())[:6])
        if p.bullets:
            entry["features"] = p.bullets[:3]
        items.append(entry)

    prompt = (
        f"Sei un esperto acquisti Amazon.it. Cerca: '{query}'.\n"
        f"Analizza questi prodotti e in 1-2 frasi italiane consiglia il migliore "
        f"(nomina il prodotto esatto). Considera prezzo/qualità, stelle, specifiche.\n\n"
        f"Prodotti:\n{json.dumps(items, ensure_ascii=False)}"
    )
    return _llm(prompt)


def ai_rank(products: list, query: str, budget: float | None = None) -> list:
    """Ask LLM to rank products. Returns reordered list (best first).
    Falls back to original order if LLM unavailable.
    """
    if len(products) <= 1:
        return products

    items_summary = []
    for i, p in enumerate(products):
        items_summary.append({
            "idx": i,
            "titolo": p.title[:60],
            "prezzo_eur": p.price,
            "stelle": p.stars,
            "recensioni": p.reviews,
        })

    budget_str = f" Budget max: €{budget}." if budget else ""
    prompt = (
        f"Cerca: '{query}'.{budget_str}\n"
        f"Ordina questi prodotti dal migliore al peggiore per rapporto qualità/prezzo.\n"
        f"Rispondi SOLO con una lista di numeri idx separati da virgola, es: 3,0,5,1,2\n\n"
        f"Prodotti:\n{json.dumps(items_summary, ensure_ascii=False)}"
    )

    result = _llm(prompt)
    if not result:
        return products

    try:
        order = [int(x.strip()) for x in result.split(",") if x.strip().isdigit()]
        seen = set()
        reordered = []
        for idx in order:
            if 0 <= idx < len(products) and idx not in seen:
                reordered.append(products[idx])
                seen.add(idx)
        # Append any not mentioned
        for i, p in enumerate(products):
            if i not in seen:
                reordered.append(p)
        return reordered
    except Exception:
        return products
