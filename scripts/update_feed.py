#!/usr/bin/env python3
"""Update the public paper feed using Crossref, without third-party packages."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

JOURNALS = [
    ("Nature", "0028-0836"), ("Science", "0036-8075"), ("Cell", "0092-8674"),
    ("Nature Communications", "2041-1723"), ("Science Advances", "2375-2548"),
    ("PNAS", "0027-8424"), ("eLife", "2050-084X"),
    ("Nature Medicine", "1078-8956"), ("Nature Biotechnology", "1087-0156"),
    ("Nature Biomedical Engineering", "2157-846X"), ("Nature Aging", "2662-8465"),
    ("Science Translational Medicine", "1946-6234"), ("Cell Reports Medicine", "2666-3791"),
    ("Nature Cell Biology", "1465-7392"), ("Cell Stem Cell", "1934-5909"),
    ("Developmental Cell", "1534-5807"), ("Development", "0950-1991"),
    ("Bone Research", "2095-6231"), ("Osteoarthritis and Cartilage", "1063-4584"),
    ("Biomaterials", "0142-9612"), ("Nature Genetics", "1061-4036"),
    ("Nature Methods", "1548-7091"), ("Genome Biology", "1474-760X"),
    ("Genes & Development", "0890-9369"), ("Genome Research", "1088-9051"),
]

KEYWORD_WEIGHTS = {
    "aldh1a2": 40, "retinoic": 24, "retinoid": 20, "regenerat": 22,
    "blastema": 22, "wound": 13, "fibroblast": 16, "enhancer": 18,
    "cis-regulat": 18, "chromatin": 14, "accessib": 12, "multiome": 18,
    "single-cell": 12, "single cell": 12, "single-nucleus": 12,
    "atac": 13, "scrna": 12, "snrna": 12, "hi-c": 14, "micro-c": 18,
    "3d genome": 15, "crispr": 10, "lineage": 10, "appendage": 15,
    "limb": 10, "axolotl": 16, "zebrafish fin": 16,
    "gene regulation": 10, "regulatory evolution": 14, "developmental": 6,
    "cartilage": 24, "chondrogen": 26, "chondrocyte": 24,
    "chondral": 18, "osteochondral": 24, "endochondral": 20,
    "articular cartilage": 28, "growth plate": 20, "perichondrium": 22,
    "extracellular matrix": 10, "matrix remodeling": 14,
    "sox9": 24, "col2a1": 24, "aggrecan": 20, "acan": 16,
    "gdf5": 18, "prg4": 18,
}

NON_RESEARCH_PREFIXES = (
    "snapshot:", "corrigendum", "erratum", "retraction", "author correction",
    "publisher correction", "editorial expression of concern", "in this issue",
)


def clean_markup(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def date_from_parts(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts") or []
    if not parts or not parts[0]:
        return ""
    nums = list(parts[0]) + [1, 1]
    try:
        return dt.date(int(nums[0]), int(nums[1]), int(nums[2])).isoformat()
    except (TypeError, ValueError):
        return ""


def published_date(item: dict) -> str:
    for key in ("published-online", "published-print", "published", "issued"):
        value = date_from_parts(item.get(key))
        if value:
            return value
    return (item.get("created", {}).get("date-time", "") or "")[:10]


def is_research_article(doi: str, title: str, abstract: str) -> bool:
    doi_l, title_l = doi.lower(), title.strip().lower()
    if title_l.startswith(NON_RESEARCH_PREFIXES):
        return False
    if "10.1038/" in doi_l:
        suffix = doi_l.split("10.1038/", 1)[1]
        return not suffix.startswith("d") and bool(abstract)
    if "10.1016/" in doi_l:
        return True
    return bool(abstract)


def keyword_rank(title: str, abstract: str) -> tuple[int, str]:
    text = f"{title} {abstract}".lower()
    hits = [(key, weight) for key, weight in KEYWORD_WEIGHTS.items() if key in text]
    hits.sort(key=lambda pair: pair[1], reverse=True)
    score = min(100, sum(weight for _, weight in hits))
    reason = "关键词：" + "、".join(key for key, _ in hits[:6]) if hits else "暂未命中研究画像关键词"
    return score, reason


def request_json(url: str, attempts: int = 3) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "PaperRadar/1.0", "Accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.load(response)
        except Exception as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Crossref request failed: {last_error}")


def fetch_journal(name: str, issn: str, since: str, rows: int = 200) -> list[dict]:
    params = urllib.parse.urlencode({
        "filter": f"from-created-date:{since},type:journal-article",
        "sort": "created", "order": "desc", "rows": rows,
    })
    payload = request_json(f"https://api.crossref.org/journals/{issn}/works?{params}")
    papers: list[dict] = []
    for item in payload.get("message", {}).get("items", []):
        titles = item.get("title") or []
        doi = (item.get("DOI") or "").strip()
        if not titles or not doi:
            continue
        title = clean_markup(titles[0])
        abstract = clean_markup(item.get("abstract", ""))[:1500]
        if not is_research_article(doi, title, abstract):
            continue
        authors = item.get("author") or []
        first_author = ""
        if authors:
            first_author = (authors[0].get("family") or authors[0].get("name") or "").strip()
            if len(authors) > 1:
                first_author += " et al."
        score, reason = keyword_rank(title, abstract)
        papers.append({
            "doi": doi, "journal": name, "title": title, "abstract": abstract,
            "first_author": first_author, "published_date": published_date(item),
            "url": f"https://doi.org/{urllib.parse.quote(doi, safe='/')}",
            "score": score, "reason": reason,
        })
    return papers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path("public/papers.json"))
    args = parser.parse_args()
    existing = json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else []
    by_doi = {paper["doi"].lower(): paper for paper in existing if paper.get("doi")}
    next_id = max((int(paper.get("id", 0)) for paper in existing), default=0) + 1
    since = (dt.date.today() - dt.timedelta(days=max(1, args.days))).isoformat()
    failures: list[str] = []
    added = 0
    for name, issn in JOURNALS:
        try:
            for paper in fetch_journal(name, issn, since):
                key = paper["doi"].lower()
                if key in by_doi:
                    paper["id"] = by_doi[key].get("id", next_id)
                    by_doi[key].update(paper)
                else:
                    paper["id"] = next_id
                    next_id += 1
                    by_doi[key] = paper
                    added += 1
            print(f"{name}: ok")
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            print(f"{name}: failed ({exc})")
    papers = sorted(by_doi.values(), key=lambda paper: (int(paper.get("score", 0)), paper.get("published_date", "")), reverse=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(papers, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Updated {len(papers)} papers; added {added}; failed journals {len(failures)}")
    if len(failures) > len(JOURNALS) // 3:
        raise RuntimeError("Too many journal feeds failed: " + "; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
