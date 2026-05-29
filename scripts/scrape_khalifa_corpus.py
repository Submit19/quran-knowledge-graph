#!/usr/bin/env python3
"""Scrape the Khalifa primary-source corpus from masjidtucson.org.

The Khalifa-only source rule binds this scrape (memory/feedback_khalifa_only_sources.md):
only the Quran's verse text and Rashad Khalifa's OWN primary writings are authoritative.
Every source fetched here is confirmed Khalifa-primary by the discovery manifest
(data/research/khalifa_corpus_discovery/02_primary_source_manifest.json on
claude/khalifa-corpus-discovery-2026-05-27).

Buckets (ungated only — VP/CS are behind a copyright gate, deferred):
  intro        Introduction to The Final Testament (1 HTML page)
  appendices   38 Appendices to The Final Testament (HTML)
  qhi          Quran, Hadith and Islam (per-page PDFs, stitched into chapters)
  sp           Submitters Perspective, Khalifa-edited era 1985-02..1990-03 (HTML)

Provenance: every output .md carries YAML frontmatter (title, author, year, source URL,
masthead, scrape timestamp, sha256 of the extracted body, word count). 9:128/9:129
references are FLAGGED, never stripped — the no-surface rule binds the composer's output,
not this corpus (see COMPOSER_CONSTRAINTS.md).

Usage:
  python scripts/scrape_khalifa_corpus.py --smoke            # 3-file quality check
  python scripts/scrape_khalifa_corpus.py --bucket intro
  python scripts/scrape_khalifa_corpus.py --bucket appendices
  python scripts/scrape_khalifa_corpus.py --bucket qhi
  python scripts/scrape_khalifa_corpus.py --bucket sp
  python scripts/scrape_khalifa_corpus.py --bucket all
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
import requests
from bs4 import BeautifulSoup, NavigableString
from markdownify import markdownify as html_to_md

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

USER_AGENT = (
    "QuranKG-KhalifaCorpus/1.0 "
    "(+non-commercial Submitter research/study tool; contact ali.katkodia@gmail.com)"
)
RATE_LIMIT_SEC = 1.1  # >= 1 second between network requests, per the brief
REQUEST_TIMEOUT = 60
RATE_429_BACKOFF_SEC = 300  # 5 minute back-off on rate-limit
RATE_429_RETRIES = 3
LOW_CHAR_THRESHOLD = 50  # flag (don't drop) extractions below this

CORPUS_DIR = Path("data/khalifa_corpus")
CACHE_DIR = CORPUS_DIR / ".cache"
SMOKE_DIR = CORPUS_DIR / ".smoke"

SITE = "https://www.masjidtucson.org"
APPENDIX_BASE = f"{SITE}/quran/appendices"
QHI_BASE = f"{SITE}/publications/books/qhi"
SP_BASE = f"{SITE}/publications/books/sp"

# 9:128 / 9:129 detector — flag for provenance, never redact at corpus layer.
NINE_FALSE_VERSES_RE = re.compile(r"9\s*[:.]\s*12[89]")

# Appendix titles (n -> title), from the discovery manifest.
APPENDICES = {
    1: "One of the Great Miracles [74:35]",
    2: "God's Messenger of the Covenant [3:81]",
    3: "We Made the Quran Easy [54:17]",
    4: "Why Was the Quran Revealed in Arabic?",
    5: "Heaven and Hell",
    6: "Greatness of God",
    7: "Why Were We Created?",
    8: "The Myth of Intercession",
    9: "Abraham: Original Messenger of Islam",
    10: "God's Usage of the Plural Tense",
    11: "The Day of Resurrection",
    12: "Role of the Prophet Muhammad",
    13: "The First Pillar of Islam",
    14: "Predestination",
    15: "Religious Duties: Gift from God",
    16: "Dietary Prohibition",
    17: "Death",
    18: "Quran is All You Need",
    19: "Hadith and Sunna: Satanic Innovations",
    20: "Quran: Unlike Any Other Book",
    21: "Satan: Fallen Angel",
    22: "Jesus",
    23: "Chronological Order of Revelation",
    24: "Two False Verses Removed from the Quran",
    25: "End of the World",
    26: "The Three Messengers of Islam",
    27: "Who Is Your God?",
    28: "Muhammad Wrote God's Revelations With His Own Hand",
    29: "The Missing Basmalah",
    30: "Polygamy",
    31: "Evolution: A Divinely Guided Process",
    32: "The Crucial Age of 40",
    33: "Why Did God Send a Messenger Now?",
    34: "Virginity/Chastity: A Trait of the True Believers",
    35: "Drugs & Alcohol",
    36: "What Price A Great Nation",
    37: "Criminal Justice in Islam",
    38: "The Creator's Signature",
}

# Submitters Perspective, Khalifa-editorship era only (1985-02 .. 1990-03).
# Post-1990-03 issues are community-edited and EXCLUDED per the binding rule.
SP_ISSUES = {
    1985: ["feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
    1986: [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ],
    1987: [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ],
    1988: [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "may_bonus",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ],
    1989: [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ],
    1990: ["jan", "jan_bonus", "feb", "mar"],
}
MONTH_NUM = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}

# --------------------------------------------------------------------------- #
# Rate-limited, caching fetcher
# --------------------------------------------------------------------------- #


class Fetcher:
    """Fetches URLs with a >=1s rate limit, on-disk caching, and 429 back-off."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_fetch = 0.0
        self.network_requests = 0
        self.cache_hits = 0

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        suffix = ".pdf" if url.lower().endswith(".pdf") else ".bin"
        return self.cache_dir / f"{digest}{suffix}"

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_fetch
        if elapsed < RATE_LIMIT_SEC:
            time.sleep(RATE_LIMIT_SEC - elapsed)

    def get(self, url: str) -> tuple[bytes | None, int]:
        """Return (content_bytes, status). content is None on a hard failure."""
        cache_path = self._cache_path(url)
        if cache_path.exists():
            self.cache_hits += 1
            return cache_path.read_bytes(), 200

        for attempt in range(RATE_429_RETRIES + 1):
            self._throttle()
            try:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            except requests.RequestException as exc:
                self._last_fetch = time.monotonic()
                print(f"    ! network error {url}: {exc}", file=sys.stderr)
                return None, 0
            self._last_fetch = time.monotonic()
            self.network_requests += 1

            if resp.status_code == 429:
                if attempt < RATE_429_RETRIES:
                    print(
                        f"    ! 429 rate-limited on {url}; backing off "
                        f"{RATE_429_BACKOFF_SEC}s (retry {attempt + 1}/{RATE_429_RETRIES})",
                        file=sys.stderr,
                    )
                    time.sleep(RATE_429_BACKOFF_SEC)
                    continue
                print(f"    ! 429 persisted on {url}; giving up", file=sys.stderr)
                return None, 429

            if resp.status_code == 200:
                cache_path.write_bytes(resp.content)
                return resp.content, 200

            return None, resp.status_code

        return None, 429


# --------------------------------------------------------------------------- #
# Extraction helpers
# --------------------------------------------------------------------------- #

_CHROME_CLASS_RE = re.compile(
    r"linkbar|contact|copyright|basmal|volume|published", re.I
)
_LAYOUT_TAGS = [
    "table",
    "tbody",
    "thead",
    "tr",
    "td",
    "th",
    "font",
    "span",
    "center",
    "div",
]


def _slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)  # drop [74:35] style refs
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return text[:max_len].strip("_") or "untitled"


def _clean_markdown(text: str) -> str:
    text = text.replace("\xa0", " ")
    # Drop the dangling cell separator at the end of each line and remove lines
    # that are only separators (empty layout spacer cells in SP newsletters).
    text = re.sub(r"(?m)[ \t]*\|[ \t]*$", "", text)
    text = re.sub(r"(?m)^[ \t|]*\|[ \t|]*$\n?", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)  # trailing whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)  # runs of spaces
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse blank lines
    return text.strip() + "\n"


def html_body_to_markdown(html: str) -> str:
    """Strip site chrome and layout tables, then convert prose to Markdown."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "noscript"]):
        tag.decompose()
    # Drop nav / footer / decorative chrome by class.
    for tag in soup.find_all(class_=_CHROME_CLASS_RE):
        tag.decompose()
    body = soup.body or soup
    # Preserve cell/row boundaries before flattening, else dense data tables
    # (e.g. Appendix 23's revelation-order grid) collapse into one merged token.
    for cell in body.find_all(["td", "th"]):
        cell.append(NavigableString(" | "))
    for row in body.find_all("tr"):
        row.append(soup.new_tag("br"))
    # Flatten layout containers so prose flows instead of becoming pipe-tables.
    for tag in body.find_all(_LAYOUT_TAGS):
        tag.unwrap()
    markdown = html_to_md(str(body), strip=["a", "img"], heading_style="ATX")
    return _clean_markdown(markdown)


def pdf_bytes_to_text(data: bytes) -> str:
    """Extract text from a masjidtucson PDF. x_tolerance=3 merges the wide
    intra-word letter spacing these typeset PDFs use."""
    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text(x_tolerance=3) or "")
    return _clean_markdown("\n\n".join(parts))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_frontmatter(**fields) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        else:
            escaped = str(value).replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
    lines.append("---\n")
    return "\n".join(lines)


def write_doc(
    out_path: Path, frontmatter_fields: dict, body: str, failures: list
) -> dict:
    body = body.strip()
    char_count = len(body)
    word_count = len(body.split())
    flagged = bool(NINE_FALSE_VERSES_RE.search(body))
    warning = "low_char_count" if char_count < LOW_CHAR_THRESHOLD else None
    if warning:
        failures.append(
            {"file": str(out_path), "warning": warning, "chars": char_count}
        )
        print(f"    ! LOW CHARS ({char_count}) -> {out_path.name}", file=sys.stderr)

    fields = dict(frontmatter_fields)
    fields["word_count"] = word_count
    fields["char_count"] = char_count
    fields["content_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    fields["flagged_9_128_129"] = flagged
    if warning:
        fields["extraction_warning"] = warning

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_frontmatter(**fields) + "\n" + body + "\n", encoding="utf-8"
    )
    return {
        "file": str(out_path),
        "words": word_count,
        "chars": char_count,
        "flagged": flagged,
    }


# --------------------------------------------------------------------------- #
# Bucket scrapers
# --------------------------------------------------------------------------- #


def scrape_intro(fetcher: Fetcher, out_dir: Path, failures: list) -> list[dict]:
    url = f"{APPENDIX_BASE}/introduction.html"
    print(f"[intro] {url}")
    content, status = fetcher.get(url)
    if content is None:
        failures.append({"url": url, "status": status})
        return []
    body = html_body_to_markdown(content.decode("utf-8", errors="replace"))
    rec = write_doc(
        out_dir / "introduction_to_final_testament.md",
        {
            "title": "Introduction to The Final Testament",
            "author": "Rashad Khalifa",
            "year": 1989,
            "category": "introduction",
            "source_url": url,
            "source_format": "html",
            "scraped_at": _now_iso(),
        },
        body,
        failures,
    )
    return [rec]


def scrape_appendices(
    fetcher: Fetcher, out_dir: Path, failures: list, only=None
) -> list[dict]:
    records = []
    numbers = only if only else sorted(APPENDICES)
    for n in numbers:
        title = APPENDICES[n]
        url = f"{APPENDIX_BASE}/appendix{n}.html"
        print(f"[appendix {n}] {title}")
        content, status = fetcher.get(url)
        if content is None:
            failures.append({"url": url, "status": status})
            continue
        body = html_body_to_markdown(content.decode("utf-8", errors="replace"))
        fname = f"appendix_{n:02d}_{_slugify(title)}.md"
        rec = write_doc(
            out_dir / fname,
            {
                "title": f"Appendix {n}: {title}",
                "author": "Rashad Khalifa",
                "year": 1989,
                "category": "appendix",
                "appendix_number": n,
                "source_url": url,
                "source_format": "html",
                "scraped_at": _now_iso(),
            },
            body,
            failures,
        )
        records.append(rec)
    return records


def _qhi_contents(fetcher: Fetcher) -> list[tuple[str, str]]:
    """Return ordered (title, pdf_url) for the QHI book from its contents page."""
    url = f"{QHI_BASE}/contents.html"
    content, status = fetcher.get(url)
    if content is None:
        raise RuntimeError(f"QHI contents fetch failed: {status}")
    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    items = []
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        if href.lower().endswith(".pdf"):
            items.append((a.get_text(strip=True), f"{QHI_BASE}/{href}"))
    return items


def scrape_qhi(
    fetcher: Fetcher, out_dir: Path, failures: list, limit=None
) -> list[dict]:
    items = _qhi_contents(fetcher)
    if limit:
        items = items[:limit]
    print(f"[qhi] {len(items)} PDFs from contents.html")

    # Extract every PDF, then stitch consecutive same-title pages into chapters.
    pages = []  # (title, url, text)
    for title, url in items:
        print(f"[qhi] {url.split('/')[-1]}  {title[:60]}")
        content, status = fetcher.get(url)
        if content is None:
            failures.append({"url": url, "status": status})
            continue
        try:
            text = pdf_bytes_to_text(content)
        except Exception as exc:  # noqa: BLE001 - pdfminer/pdfplumber can raise broadly
            failures.append({"url": url, "error": str(exc)})
            print(f"    ! PDF extract failed: {exc}", file=sys.stderr)
            continue
        pages.append((title, url, text))

    # Group: front matter (TitlePage/Copyright/Preface) each stand alone;
    # numbered pages collapse runs of an identical section title into one chapter.
    records = []
    chapter_idx = 0
    i = 0
    while i < len(pages):
        title, url, text = pages[i]
        urls = [url]
        bodies = [text]
        is_front = "pg" not in url.rsplit("/", 1)[-1].lower()
        if not is_front:
            j = i + 1
            while (
                j < len(pages)
                and pages[j][0] == title
                and "pg" in pages[j][1].rsplit("/", 1)[-1].lower()
            ):
                urls.append(pages[j][1])
                bodies.append(pages[j][2])
                j += 1
            i = j
        else:
            i += 1

        body = f"# {title}\n\n" + "\n\n".join(b for b in bodies if b.strip())
        fname = f"chapter_{chapter_idx:02d}_{_slugify(title)}.md"
        rec = write_doc(
            out_dir / fname,
            {
                "title": title,
                "author": "Rashad Khalifa, Ph.D.",
                "year": 1982,
                "category": "book_chapter",
                "book": "Quran, Hadith and Islam",
                "source_url": " ".join(urls),
                "source_format": "pdf",
                "page_count": len(urls),
                "arabic_note": "Arabic quotations in the source PDFs render as glyphs; "
                "Unicode Arabic is not reliably preserved.",
                "scraped_at": _now_iso(),
            },
            body,
            failures,
        )
        records.append(rec)
        chapter_idx += 1
    return records


def _sp_dir(month: str) -> str:
    """Map a logical month key to its URL directory. Bonus issues live at
    e.g. 1988/may_2/ and 1990/jan_2/, not may_bonus/jan_bonus."""
    return month.replace("_bonus", "_2")


def _sp_pages_for_issue(fetcher: Fetcher, year: int, month: str) -> list[str]:
    """Return ordered page URLs for one SP issue by reading page1's nav."""
    mdir = _sp_dir(month)
    p1 = f"{SP_BASE}/{year}/{mdir}/page1.html"
    content, status = fetcher.get(p1)
    if content is None:
        return []
    soup = BeautifulSoup(content.decode("latin-1", errors="replace"), "html.parser")
    nums = {1}
    for a in soup.find_all("a"):
        m = re.fullmatch(r"page(\d+)\.html", (a.get("href") or "").strip())
        if m:
            nums.add(int(m.group(1)))
    return [f"{SP_BASE}/{year}/{mdir}/page{n}.html" for n in sorted(nums)]


def scrape_sp(
    fetcher: Fetcher, out_dir: Path, failures: list, only_issues=None
) -> list[dict]:
    records = []
    issues = (
        only_issues
        if only_issues
        else [(y, m) for y in sorted(SP_ISSUES) for m in SP_ISSUES[y]]
    )
    for year, month in issues:
        page_urls = _sp_pages_for_issue(fetcher, year, month)
        if not page_urls:
            failures.append({"issue": f"{year}/{month}", "status": "no_page1"})
            print(f"[sp {year}/{month}] ! page1 missing", file=sys.stderr)
            continue
        print(f"[sp {year}/{month}] {len(page_urls)} pages")

        masthead = None
        lead_title = None
        page_bodies = []
        for idx, url in enumerate(page_urls, start=1):
            content, status = fetcher.get(url)
            if content is None:
                failures.append({"url": url, "status": status})
                continue
            html = content.decode("latin-1", errors="replace")
            if idx == 1:
                soup = BeautifulSoup(html, "html.parser")
                sp_tag = soup.find("p", class_="sp")
                if sp_tag:
                    masthead = sp_tag.get_text(strip=True)
                if soup.title and soup.title.string:
                    lead_title = soup.title.string.split(";")[0].strip()
            body = html_body_to_markdown(html)
            page_bodies.append(f"## Page {idx}\n\n{body}")

        month_label = MONTH_NUM.get(month, month)
        if month.endswith("_bonus"):
            base = month.replace("_bonus", "")
            month_label = f"{MONTH_NUM.get(base, base)}b"
        slug = _slugify(lead_title) if lead_title else "issue"
        fname = f"{year}-{month_label}_{slug}.md"
        body = "\n\n".join(page_bodies)
        rec = write_doc(
            out_dir / fname,
            {
                "title": lead_title or f"Submitters Perspective {year}/{month}",
                "author": "Rashad Khalifa, Ph.D. (issue editor)",
                "year": year,
                "category": "newsletter_issue",
                "masthead": masthead or "Submitters Perspective",
                "issue": f"{year}-{month_label}",
                "source_url": " ".join(page_urls),
                "source_format": "html",
                "page_count": len(page_urls),
                "byline_note": "Khalifa edited every issue 1985-02..1990-03. Lead pieces are "
                "typically his; shorter items may be other contributors. "
                "Treated as issue-level Khalifa-primary.",
                "scraped_at": _now_iso(),
            },
            body,
            failures,
        )
        records.append(rec)
    return records


# --------------------------------------------------------------------------- #
# Smoke test + CLI
# --------------------------------------------------------------------------- #


def run_smoke(fetcher: Fetcher) -> None:
    failures: list = []
    print("=== SMOKE TEST (1 appendix, 1 QHI chapter, 1 SP issue) ===")
    recs = []
    recs += scrape_appendices(fetcher, SMOKE_DIR / "appendices", failures, only=[1])
    recs += scrape_qhi(fetcher, SMOKE_DIR / "qhi", failures, limit=4)
    recs += scrape_sp(fetcher, SMOKE_DIR / "sp", failures, only_issues=[(1985, "feb")])
    print("\n=== SMOKE RESULTS ===")
    for r in recs:
        print(f"  {r['words']:>6} words  flagged={r['flagged']}  {r['file']}")
    print(f"failures: {failures}")
    print(
        f"network requests: {fetcher.network_requests}, cache hits: {fetcher.cache_hits}"
    )


BUCKET_DIRS = {
    "intro": CORPUS_DIR / "introduction",
    "appendices": CORPUS_DIR / "appendices",
    "qhi": CORPUS_DIR / "quran_hadith_islam",
    "sp": CORPUS_DIR / "submitters_perspective",
}


def _parse_frontmatter(md_text: str) -> dict:
    """Parse the simple `key: "value"` YAML frontmatter this script emits."""
    if not md_text.startswith("---"):
        return {}
    end = md_text.find("\n---", 3)
    block = md_text[3:end]
    out = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value and value[0] == '"' and value[-1] == '"':
            value = value[1:-1].replace('\\"', '"')
        elif value in ("true", "false"):
            value = value == "true"
        elif value.lstrip("-").isdigit():
            value = int(value)
        out[key.strip()] = value
    return out


def build_manifest() -> None:
    """Walk the corpus and emit MANIFEST.json from each file's frontmatter."""
    buckets = {
        "introduction": "introduction",
        "appendices": "appendix",
        "quran_hadith_islam": "book_chapter",
        "submitters_perspective": "newsletter_issue",
    }
    items = []
    per_bucket = {}
    total_words = 0
    flagged = 0
    for subdir in buckets:
        bucket_dir = CORPUS_DIR / subdir
        if not bucket_dir.is_dir():
            continue
        files = sorted(bucket_dir.glob("*.md"))
        bw = 0
        for path in files:
            fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
            rel = path.relative_to(CORPUS_DIR).as_posix()
            words = int(fm.get("word_count", 0))
            bw += words
            total_words += words
            if fm.get("flagged_9_128_129"):
                flagged += 1
            items.append(
                {
                    "path": rel,
                    "bucket": subdir,
                    "title": fm.get("title"),
                    "author": fm.get("author"),
                    "year": fm.get("year"),
                    "category": fm.get("category"),
                    "masthead": fm.get("masthead"),
                    "source_url": fm.get("source_url"),
                    "source_format": fm.get("source_format"),
                    "word_count": words,
                    "char_count": int(fm.get("char_count", 0)),
                    "content_sha256": fm.get("content_sha256"),
                    "flagged_9_128_129": bool(fm.get("flagged_9_128_129")),
                    "size_bytes": path.stat().st_size,
                }
            )
        per_bucket[subdir] = {"files": len(files), "words": bw}

    manifest = {
        "schema_version": 1,
        "generated_at": _now_iso(),
        "generated_by": "scripts/scrape_khalifa_corpus.py",
        "binding_rule": "memory/feedback_khalifa_only_sources.md",
        "primary_site": "masjidtucson.org",
        "scope": "Khalifa-primary, ungated sources only (VP/CS deferred — see LICENSE_NOTE.md)",
        "no_surface_rule": "9:128/9:129 references are FLAGGED per file, never stripped. "
        "The no-surface rule binds the composer's output, not this corpus "
        "(see COMPOSER_CONSTRAINTS.md).",
        "totals": {
            "files": len(items),
            "words": total_words,
            "files_flagged_9_128_129": flagged,
            "per_bucket": per_bucket,
        },
        "items": items,
    }
    out_path = CORPUS_DIR / "MANIFEST.json"
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"MANIFEST.json: {len(items)} files, {total_words:,} words, {flagged} flagged"
    )
    for b, stats in per_bucket.items():
        print(f"  {b}: {stats['files']} files, {stats['words']:,} words")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke", action="store_true", help="3-file quality smoke test"
    )
    parser.add_argument(
        "--bucket",
        choices=["intro", "appendices", "qhi", "sp", "all"],
        help="which source bucket to scrape",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="(re)generate MANIFEST.json from the scraped corpus",
    )
    args = parser.parse_args()

    if args.manifest:
        build_manifest()
        return 0

    fetcher = Fetcher(CACHE_DIR)

    if args.smoke:
        run_smoke(fetcher)
        return 0

    if not args.bucket:
        parser.error("specify --bucket or --smoke")

    failures: list = []
    records: list = []
    buckets = (
        ["intro", "appendices", "qhi", "sp"] if args.bucket == "all" else [args.bucket]
    )
    for bucket in buckets:
        out = BUCKET_DIRS[bucket]
        if bucket == "intro":
            records += scrape_intro(fetcher, out, failures)
        elif bucket == "appendices":
            records += scrape_appendices(fetcher, out, failures)
        elif bucket == "qhi":
            records += scrape_qhi(fetcher, out, failures)
        elif bucket == "sp":
            records += scrape_sp(fetcher, out, failures)

    total_words = sum(r["words"] for r in records)
    print(f"\n=== DONE: {len(records)} files, {total_words:,} words ===")
    print(
        f"network requests: {fetcher.network_requests}, cache hits: {fetcher.cache_hits}"
    )
    if failures:
        print(f"FAILURES ({len(failures)}): {json.dumps(failures, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
