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
                 "--print", "%(id)s\t%(channel)s\t%(title)s", "--no-warnings"],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace").stdout
        except Exception:
            continue
        for line in out.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            vid, channel, title = parts
            if vid and vid not in videos:
                videos[vid] = {"query": q, "title": title.strip(),
                               "channel": channel.strip()}
        _save(videos_path, videos)
    return videos


def _vtt_to_text(path: str) -> str:
    seen, out = set(), []
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\[[^\]]+\]", "", line).strip()
        if line and line not in seen:
            seen.add(line)
            out.append(line)
    return " ".join(out)


# affiliate/shortlink patterns in a video description = the reviewer earns on the sale.
# Not proof of dishonesty, but "N video, tutti con link affiliato" reads very differently
# from independent coverage — so it's measured and shown, never silently judged.
_AFFILIATE_RX = re.compile(
    r"(amzn\.to/|amazon\.[a-z.]{2,6}/[^\s\"']*[?&]tag=|bit\.ly/|geni\.us/|howl\.me/|shop-links\.co/)",
    re.I)


def fetch_transcripts(out_dir: str, *, sub_langs: str = "en.*,it.*") -> int:
    """Download auto-subs + description (no video/audio) for every collected id,
    resumable. Marks videos whose description carries affiliate links.
    Returns count of newly fetched transcripts."""
    videos_path = os.path.join(out_dir, "videos.json")
    videos = _load(videos_path, {})
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
                 "--sub-langs", sub_langs, "--sub-format", "vtt", "--write-description",
                 "-o", os.path.join(tdir, "%(id)s.%(ext)s"),
                 f"https://www.youtube.com/watch?v={vid}", "--no-warnings"],
                capture_output=True, text=True, timeout=120)
        except Exception:
            continue
        desc_fp = os.path.join(tdir, f"{vid}.description")
        if os.path.exists(desc_fp):
            try:
                desc = open(desc_fp, encoding="utf-8", errors="replace").read()
                videos[vid]["affiliate"] = bool(_AFFILIATE_RX.search(desc))
                _save(videos_path, videos)
            except Exception:
                pass
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
                    c["channel"] = videos[vid].get("channel", "")
                    c["affiliate"] = videos[vid].get("affiliate", False)
                    out.write(json.dumps(c, ensure_ascii=False) + "\n")
                    new += 1
            processed.add(vid)
            _save(processed_path, sorted(processed))
    return new


def load_claims(out_dir: str) -> list[dict]:
    """Read every claim written by extract_claims() so far."""
    path = os.path.join(out_dir, "claims.jsonl")
    if not os.path.exists(path):
        return []
    claims = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    claims.append(json.loads(line))
                except Exception:
                    continue
    return claims


def coverage(claims: list[dict]) -> dict[str, dict]:
    """Per product: how many DISTINCT videos mention it (not claim count — one chatty
    video shouldn't outweigh five short ones) and the actual video ids, for report links.

    Concentration is itself a signal: a handful of products absorbing almost all serious
    review coverage is real information, not noise. A product backed by a single video is
    a flag to look closer (could be new, could be sponsored) — not proof of anything either
    way, so callers should show it as a prompt to check, never as an auto-exclusion."""
    _LISTICLE_RX = re.compile(r"\b(top\s*\d+|best|migliori?|classifica|ranking|vs\.?)\b", re.I)
    by_product: dict[str, dict] = {}
    for c in claims:
        product = c.get("product")
        if not product or product == "generic" or not c.get("video"):
            continue
        entry = by_product.setdefault(product, {"videos": set(), "titles": {},
                                                 "channels": set(), "dedicated": 0,
                                                 "affiliate_videos": set()})
        if c.get("affiliate"):
            entry["affiliate_videos"].add(c["video"])
        if c["video"] not in entry["videos"] and not _LISTICLE_RX.search(c.get("title", "")):
            # a video ABOUT this product, not a "top 10" listicle: listicles copy each
            # other's product lists, so they confirm popularity, not quality.
            entry["dedicated"] += 1
        entry["videos"].add(c["video"])
        entry["titles"][c["video"]] = c.get("title", "")
        if c.get("channel"):
            entry["channels"].add(c["channel"])
    out = {}
    for product, info in by_product.items():
        n_vid, n_ch = len(info["videos"]), len(info["channels"])
        # many videos from ONE channel = one voice repeated, not independent coverage
        single_source = n_vid >= 2 and n_ch == 1
        n_aff = len(info["affiliate_videos"])
        out[product] = {
            "video_count": n_vid,
            "channel_count": n_ch,
            "dedicated_count": info["dedicated"],
            "single_source": single_source,
            "affiliate_count": n_aff,
            "all_affiliate": n_vid >= 2 and n_aff == n_vid,
            "videos": [{"id": v, "title": info["titles"][v]} for v in info["videos"]],
        }
    return out
