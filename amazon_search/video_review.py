# -*- coding: utf-8 -*-
"""Product claims mined from real YouTube reviews, not marketing copy.

Titles and listing photos tell you what a product *is*; they don't tell you
if it actually works. Real owners talking about it on video do — but
watching dozens of reviews doesn't scale. This pulls auto-generated
subtitles (yt-dlp, no audio download) and has an LLM extract short factual
claims per product/attribute, tagged with sentiment.

Fully generic: pass your own search queries, product names, and attribute
list — nothing here is tied to any specific product category. Needs the
`yt-dlp` binary on PATH and a Groq-compatible API key.

Usage (resumable — safe to stop and rerun each stage):
    search_videos(["best wireless earbuds 2026"], out_dir="out/reviews")
    fetch_transcripts(out_dir="out/reviews")
    extract_claims(out_dir="out/reviews", products=["SoundCore Buds Air 3"],
                    attributes=["battery", "comfort", "price", "sound"],
                    groq_key=os.environ["GROQ_KEY"])
"""
from __future__ import annotations
import glob
import json
import os
import re
import subprocess
import time
import urllib.request

GROQ_MODEL = "llama-3.3-70b-versatile"


def _load(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def search_videos(queries: list[str], out_dir: str, *, target: int = 40,
                   per_query: int = 12) -> dict:
    """Collect candidate video ids via yt-dlp search (metadata only, no download).
    Resumable: skips queries once `target` ids are already collected."""
    os.makedirs(out_dir, exist_ok=True)
    videos_path = os.path.join(out_dir, "videos.json")
    videos = _load(videos_path, {})
    for q in queries:
        if len(videos) >= target:
            break
        try:
            out = subprocess.run(
                ["yt-dlp", f"ytsearch{per_query}:{q}", "--flat-playlist",
                 "--print", "%(id)s\t%(title)s", "--no-warnings"],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace").stdout
        except Exception:
            continue
        for line in out.splitlines():
            if "\t" not in line:
                continue
            vid, title = line.split("\t", 1)
            if vid and vid not in videos:
                videos[vid] = {"query": q, "title": title.strip()}
        _save(videos_path, videos)
    return videos


def _vtt_to_text(path: str) -> str:
    seen, out = set(), []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\[[^\]]+\]", "", line).strip()
        if line and line not in seen:
            seen.add(line)
            out.append(line)
    return " ".join(out)


def fetch_transcripts(out_dir: str, *, sub_langs: str = "en.*,it.*") -> int:
    """Download auto-subs (no video/audio) for every collected id, resumable.
    Returns count of newly fetched transcripts."""
    videos = _load(os.path.join(out_dir, "videos.json"), {})
    tdir = os.path.join(out_dir, "transcripts")
    os.makedirs(tdir, exist_ok=True)
    done = 0
    for vid in videos:
        txt = os.path.join(tdir, f"{vid}.txt")
        if os.path.exists(txt):
            continue
        try:
            subprocess.run(
                ["yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                 "--sub-langs", sub_langs, "--sub-format", "vtt",
                 "-o", os.path.join(tdir, "%(id)s.%(ext)s"),
                 f"https://www.youtube.com/watch?v={vid}", "--no-warnings"],
                capture_output=True, text=True, timeout=120)
        except Exception:
            continue
        cands = sorted(glob.glob(os.path.join(tdir, f"{vid}.*.vtt")))
        if not cands:
            open(txt, "w").close()  # placeholder: no subs, don't retry
            continue
        pick = (next((c for c in cands if ".it." in c), None)
                or next((c for c in cands if ".en." in c), None) or cands[0])
        with open(txt, "w", encoding="utf-8") as f:
            f.write(_vtt_to_text(pick))
        for c in cands:
            os.remove(c)
        done += 1
    return done


def _chunks(s: str, n: int = 4000):
    for i in range(0, len(s), n):
        yield s[i:i + n]


def _groq(prompt: str, groq_key: str) -> str | None:
    body = json.dumps({
        "model": GROQ_MODEL, "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", body,
        {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(req, timeout=60)
            return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


_CLAIM_PROMPT = """You extract factual claims from a product review video transcript.
Only consider these products: {products}.
For each factual claim, produce an object: product (one of the products or "generic"),
attribute (one of {attributes}), sentiment ("pos"/"neg"/"neutral"), claim (short sentence).
Ignore vague ads/sponsor reads. If nothing useful, return an empty list.
Reply JSON: {{"claims": [...]}}.
TEXT:
{text}"""


def extract_claims(out_dir: str, *, products: list[str], attributes: list[str],
                    groq_key: str) -> int:
    """LLM-extract short factual claims from every fetched transcript.
    Appends to claims.jsonl, resumable via processed.json. Returns new-claim count."""
    videos = _load(os.path.join(out_dir, "videos.json"), {})
    processed_path = os.path.join(out_dir, "processed.json")
    processed = set(_load(processed_path, []))
    tdir = os.path.join(out_dir, "transcripts")
    claims_path = os.path.join(out_dir, "claims.jsonl")
    new = 0
    with open(claims_path, "a", encoding="utf-8") as out:
        for vid in videos:
            if vid in processed:
                continue
            txt = os.path.join(tdir, f"{vid}.txt")
            if not os.path.exists(txt):
                continue
            body = open(txt, encoding="utf-8").read().strip()
            if len(body) < 100:
                processed.add(vid)
                continue
            for chunk in _chunks(body):
                res = _groq(_CLAIM_PROMPT.format(
                    products=", ".join(products), attributes=", ".join(attributes),
                    text=chunk), groq_key)
                if not res:
                    continue
                try:
                    found = json.loads(res).get("claims", [])
                except Exception:
                    continue
                for c in found:
                    c["video"] = vid
                    c["title"] = videos[vid]["title"]
                    out.write(json.dumps(c, ensure_ascii=False) + "\n")
                    new += 1
            processed.add(vid)
            _save(processed_path, sorted(processed))
    return new
