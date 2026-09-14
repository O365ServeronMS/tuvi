#!/usr/bin/env python3
"""Cut the four source books into stable, addressable chunks for tuvi-kb.

Output: output/tuvi-kb/90-source/<book>/NNNN-slug[-pNN].md, one chunk per file,
with YAML frontmatter (id, heading_path, source_lines, detected stars/palaces,
non_luan flag). Also writes _meta/chunking-report.json and _meta/ocr-joins.json.

Guarantees:
- Every non-whitespace character of the (cleaned) input lands in exactly one
  chunk, in source order. The report shows the exact character delta.
- Cleaning is limited to Unicode NFC, a short explicit replacement table, and
  OCR word-gap joins ("Kh ắc" -> "Khắc") that are verified against corpus
  frequencies. Every join is logged.
- Chunk ids depend only on the source text and this script, so re-running
  yields identical ids.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuvi_kb_common import (  # noqa: E402
    BOOKS,
    INDEX_DIR,
    INPUT_DIR,
    META_DIR,
    SOURCE_DIR,
    Book,
    dump_frontmatter,
    fold,
    load_palaces,
    load_stars,
    nfc,
    normalize_key,
    palace_detector,
    squash_ws,
    star_detector,
    NameDetector,
)

MIN_CHUNK = 1_500  # smaller sections are merged into a neighbour
TARGET_CHUNK = 6_000  # preferred size when splitting oversize sections
MAX_CHUNK = 10_000  # hard ceiling per chunk file body
SLUG_MAX = 48

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
SUBNUM_RE = re.compile(r"^\d+\.\d+\.\d+\.\s+\S")  # "4.2.1. Tử Vi" inline sub-items (Tân Biên)
INLINE_SUBNUM_RE = re.compile(r"(?<=[.:;!?])[ \t]+(?=\d+\.\d+\.\d+\.\s+\S)")
LEADING_NUM_RE = re.compile(r"^(?:phần|chương|quyển)?\s*[0-9ivx]+(?:\.[0-9]+)*\.?\s*[-–:]?\s*", re.I)

# Explicit, reviewed replacements (kept from the earlier splitter; OCR tone/spacing defects).
REPLACEMENTS = {
    "Qúy": "Quý",
    "qúy": "quý",
    "Qủa": "Quả",
    "qủa": "quả",
    "Lồc": "Lộc",
    "NhũNg": "Những",
    "NHŨNG": "NHỮNG",
}

# OCR word-gap joining -----------------------------------------------------------
# Rule A: a bare Vietnamese onset (never a word on its own) + space + vowel with a
#         diacritic: "Kh ắc", "ng ười", "M ệnh". Always joined.
# Rule B: a vowel-final token + space + diacritic-initial token: "Vi ệt", "su ốt".
#         Joined only when the joined word is frequent in the corpus and the second
#         token is not itself a common standalone word ("tai ương", "hay ở" stay).
_ONSET = r"(?:ngh|ng|nh|ch|gh|kh|ph|th|tr|gi|qu|[bcdđghklmnpqrstvx])"
_DIA = "àáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵăâêôơư"
_DIAV = f"[{_DIA}{_DIA.upper()}]"
_LB = r"(?<![^\s(\"'“‘/,.;:\-])"
GAP_A_RE = re.compile(rf"{_LB}({_ONSET}) ({_DIAV}[^\s.,;:!?)]*)", re.I)
GAP_B_RE = re.compile(rf"{_LB}([A-Za-zĐđ]*[aeiouyăâêôơưAEIOUYĂÂÊÔƠƯ]) ({_DIAV}[^\s.,;:!?)]*)")
WORD_RE = re.compile(r"[^\W\d_]+")
JOIN_MIN_COUNT = 20
JOIN_RATIO = 3

# Chunks whose heading path matches one of these (folded, word-bounded) are flagged
# non_luan: chart construction, prefaces, biographies, tables of contents.
NON_LUAN_KEYS = (
    "loi noi dau", "loi gioi thieu", "loi tac gia", "loi mo dau", "tieu su", "muc luc",
    "published", "phan 1 - lap thanh", "cach tinh tong so", "phu truong",
)
NON_LUAN_EXACT_TITLES = ("dan",)  # Trần Đoàn's "Dẫn" (introduction)
LUAN_OVERRIDE_KEYS = ("ly giai ngu hanh",)  # theory inside Tân Biên Phần I stays luận


@dataclass
class Section:
    level: int
    title: str
    lines: list[str]
    start_line: int  # 1-based line of heading (or first line for preamble)

    @property
    def body_chars(self) -> int:
        return sum(len(l) for l in self.lines[1:] if l.strip()) if self.level else sum(len(l) for l in self.lines)


@dataclass
class Chunk:
    ordinal: int
    title: str
    heading_path: list[str]
    level: int
    lines: list[str]
    start_line: int
    end_line: int
    part: int = 1
    parts: int = 1
    id: str = ""
    filename: str = ""
    stars: dict[str, int] = field(default_factory=dict)
    palaces: dict[str, int] = field(default_factory=dict)
    non_luan: bool = False

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip("\n") + "\n"


# ------------------------------------------------------------------------ cleaning


def corpus_word_counts(texts: list[str]) -> collections.Counter:
    counter: collections.Counter = collections.Counter()
    for t in texts:
        counter.update(WORD_RE.findall(t))
    return counter


def clean_text(text: str, words: collections.Counter, joins: collections.Counter) -> str:
    text = nfc(text.replace("﻿", ""))
    for src, dst in REPLACEMENTS.items():
        text = text.replace(src, dst)

    def join_a(m: re.Match) -> str:
        if m.group(2)[0].isupper():  # "Th Âm": a mangled proper name, leave it for a human
            return m.group(0)
        joined = m.group(1) + m.group(2)
        joins[f"A|{m.group(0)}|{joined}"] += 1
        return joined

    def join_b(m: re.Match) -> str:
        first, second = m.group(1), m.group(2)
        joined = first + second
        # compare against the base word (strip trailing punctuation-free suffixes already excluded)
        if words[joined] >= JOIN_MIN_COUNT and words[joined] >= JOIN_RATIO * words[second]:
            joins[f"B|{m.group(0)}|{joined}"] += 1
            return joined
        return m.group(0)

    text = GAP_A_RE.sub(join_a, text)
    text = GAP_B_RE.sub(join_b, text)
    lines = [l.rstrip() for l in text.split("\n")]
    return "\n".join(lines)


def break_inline_subnums(text: str) -> tuple[str, list[int]]:
    """OCR glued numbered sub-items onto the previous sentence ("... áo mặc. 4.2.8. Thái Âm").
    Start a new paragraph there so they can serve as split points (whitespace-only change).
    Returns the new text and, for each new line, the 1-based line number in `text`."""
    out: list[str] = []
    origin: list[int] = []
    for n, line in enumerate(text.split("\n"), start=1):
        pieces = INLINE_SUBNUM_RE.split(line)
        for i, piece in enumerate(pieces):
            if i:
                out.append("")
                origin.append(n)
            out.append(piece.rstrip())
            origin.append(n)
    return "\n".join(out), origin


# ------------------------------------------------------------------------- parsing


def parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current = Section(0, "(mở đầu)", [], 1)
    for n, line in enumerate(text.split("\n"), start=1):
        m = HEADING_RE.match(line)
        if m:
            if current.lines or current.level:
                sections.append(current)
            current = Section(len(m.group(1)), m.group(2), [line], n)
        else:
            current.lines.append(line)
    sections.append(current)
    if sections and sections[0].level == 0 and not "".join(sections[0].lines).strip():
        sections.pop(0)
    return sections


def merge_split_titles(sections: list[Section]) -> list[Section]:
    """'# NHỮNG CÂU PHÚ' + '# NÊN THẬN TRỌNG ÁP DỤNG' (empty body between) -> one section."""
    out: list[Section] = []
    for sec in sections:
        if out and out[-1].level == sec.level and sec.level > 0 and out[-1].body_chars == 0:
            prev = out[-1]
            prev.title = f"{prev.title} {sec.title}"
            prev.lines.extend(sec.lines)
            continue
        out.append(sec)
    return out


def build_chunks(sections: list[Section]) -> list[Chunk]:
    chunks: list[Chunk] = []
    path: list[Section] = []
    pending: list[Section] = []  # container headings with tiny bodies, prepended to next chunk

    def flush_pending_into(target: Chunk) -> None:
        pass

    for i, sec in enumerate(sections):
        next_level = sections[i + 1].level if i + 1 < len(sections) else 0
        if sec.level:
            path = [p for p in path if p.level < sec.level] + [sec]
        is_container = next_level > sec.level
        if is_container and sec.body_chars < MIN_CHUNK:
            pending.append(sec)
            continue
        lines = [l for p in pending for l in p.lines] + sec.lines
        start = pending[0].start_line if pending else sec.start_line
        pending = []
        end = sec.start_line + len(sec.lines) - 1
        size = _size(lines)
        # A tiny section joins the previous chunk only while that chunk is itself still
        # small, so a run of short sections (Tân Biên mục 3: 85 star entries) packs into
        # chunks of MIN..~2*MIN chars instead of being swallowed by one big neighbour.
        if size < MIN_CHUNK and chunks and not is_container and _size(chunks[-1].lines) < MIN_CHUNK:
            prev = chunks[-1]
            prev.lines.extend(lines)
            prev.end_line = end
            continue
        chunks.append(Chunk(0, sec.title, [p.title for p in path], sec.level, lines, start, end))
    if pending:
        lines = [l for p in pending for l in p.lines]
        if chunks:
            chunks[-1].lines.extend(lines)
            chunks[-1].end_line = pending[-1].start_line + len(pending[-1].lines) - 1
        else:
            chunks.append(Chunk(0, pending[0].title, [pending[0].title], pending[0].level, lines,
                                pending[0].start_line, pending[-1].start_line + len(pending[-1].lines) - 1))
    # A lone short section wedged between two big ones stays tiny; fold it into the
    # previous chunk when that one still has room.
    packed: list[Chunk] = []
    carry: list[Chunk] = []  # tiny chunks waiting to be prepended to the next chunk
    for c in chunks:
        if _size(c.lines) < MIN_CHUNK:
            if packed and _size(packed[-1].lines) < TARGET_CHUNK:
                packed[-1].lines.extend(c.lines)
                packed[-1].end_line = c.end_line
            else:
                carry.append(c)
            continue
        if carry:
            c.lines = [l for t in carry for l in t.lines] + c.lines
            c.start_line = carry[0].start_line
            carry = []
        packed.append(c)
    if carry:
        if packed:
            packed[-1].lines.extend(l for t in carry for l in t.lines)
            packed[-1].end_line = carry[-1].end_line
        else:
            packed.extend(carry)
    chunks = packed
    if len(chunks) > 1 and _size(chunks[0].lines) < MIN_CHUNK:
        first = chunks.pop(0)  # publisher page / bare book title: fold into the next chunk
        chunks[0].lines = first.lines + chunks[0].lines
        chunks[0].start_line = first.start_line
    for n, c in enumerate(chunks, start=1):
        c.ordinal = n
    return chunks


# ---------------------------------------------------------------------- splitting


def _blocks(lines: list[str]) -> list[list[str]]:
    """Split lines into paragraph blocks; blank lines attach to the preceding block."""
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if not line.strip():
            cur.append(line)
            continue
        if cur and cur[-1].strip() == "":
            blocks.append(cur)
            cur = []
        cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def _hard_split(block: list[str]) -> list[list[str]]:
    """A single paragraph larger than MAX_CHUNK: split at sentence ends."""
    text = "\n".join(block)
    pieces: list[str] = []
    while len(text) > MAX_CHUNK:
        cut = max(text.rfind(". ", 0, TARGET_CHUNK), text.rfind("\n", 0, TARGET_CHUNK))
        if cut < MIN_CHUNK:
            cut = TARGET_CHUNK
        pieces.append(text[: cut + 1])
        text = text[cut + 1 :].lstrip(" ")
    pieces.append(text)
    return [p.split("\n") for p in pieces]


def _size(lines: list[str]) -> int:
    """Body size as written to disk: characters plus one newline per line."""
    return sum(len(l) + 1 for l in lines)


def sub_title(line: str) -> str:
    """'4.2.10. Cự Môn - Đại cương + Cung Mệnh có...' -> '4.2.10. Cự Môn'.
    Keeps the numbering and the name, drops the running text that OCR glued on."""
    text = squash_ws(line)
    m = re.match(r"^(\d+\.\d+\.\d+\.)\s+(.*)$", text)
    if not m:
        return text[:60]
    rest = m.group(2)
    cut = re.search(r"\s[-–+:]\s|[.:;]\s|\s\+", rest)
    name = rest[: cut.start()] if cut else rest
    return f"{m.group(1)} {name.strip()[:60]}"


def split_oversize(chunk: Chunk) -> list[Chunk]:
    if _size(chunk.lines) <= MAX_CHUNK:
        return [chunk]
    parts: list[list[str]] = []
    cur: list[str] = []

    def flush() -> None:
        nonlocal cur
        if cur:
            parts.append(cur)
        cur = []

    for block in _blocks(chunk.lines):
        first = next((l for l in block if l.strip()), "")
        if SUBNUM_RE.match(first) and _size(cur) >= MIN_CHUNK:
            flush()
        elif cur and _size(cur) + _size(block) > TARGET_CHUNK and _size(cur) >= MIN_CHUNK:
            flush()
        if _size(block) > MAX_CHUNK:
            flush()
            parts.extend(_hard_split(block))
            continue
        cur.extend(block)
    flush()
    if len(parts) > 1 and _size(parts[-1]) < MIN_CHUNK:
        parts[-2].extend(parts.pop())

    out: list[Chunk] = []
    line_cursor = chunk.start_line
    last_sub = ""  # most recent "x.y.z." sub-item title, carried into continuation parts
    for n, lines in enumerate(parts, start=1):
        first = next((l for l in lines if l.strip()), "")
        if SUBNUM_RE.match(first):
            last_sub = sub_title(first)
            title = last_sub
        elif n == 1:
            title = chunk.title
        elif last_sub:
            title = f"{last_sub} (tiếp)"
        else:
            title = f"{chunk.title} (tiếp {n})"
        for line in lines:  # remember the last sub-item that starts inside this part
            if SUBNUM_RE.match(line):
                last_sub = sub_title(line)
        end = line_cursor + len(lines) - 1
        out.append(Chunk(chunk.ordinal, title, chunk.heading_path, chunk.level, lines, line_cursor, end, n, len(parts)))
        line_cursor = end + 1
    return out


# -------------------------------------------------------------------------- naming


def slug_for(title: str) -> str:
    base = LEADING_NUM_RE.sub("", title).strip() or title
    slug = normalize_key(base)
    if len(slug) > SLUG_MAX:
        cut = slug.rfind("-", 0, SLUG_MAX)
        slug = slug[: cut if cut > 16 else SLUG_MAX]
    return slug or "khuc"


def assign_ids(book: Book, chunks: list[Chunk]) -> None:
    for c in chunks:
        base = f"{c.ordinal:04d}-{slug_for(c.title if c.part == 1 else c.heading_path[-1] if c.heading_path else c.title)}"
        if c.parts > 1:
            base = f"{base}-p{c.part:02d}"
        c.id = f"{book.code}#{base}"
        c.filename = f"{base}.md"


def is_non_luan(chunk: Chunk) -> bool:
    if chunk.level == 0:
        return True
    elements = [squash_ws(fold(t)).lower() for t in chunk.heading_path + [chunk.title]]
    hay = " | ".join(elements)
    if any(re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", hay) for k in LUAN_OVERRIDE_KEYS):
        return False
    if any(e in NON_LUAN_EXACT_TITLES for e in elements):
        return True
    return any(re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", hay) for k in NON_LUAN_KEYS)


# --------------------------------------------------------------------------- main


def process_book(book: Book, words: collections.Counter, joins: collections.Counter,
                 sdet, pdet, tdet, write: bool) -> dict:
    src = INPUT_DIR / book.input_name
    raw = src.read_text(encoding="utf-8")
    cleaned = clean_text(raw, words, joins)
    cleaned, origin = break_inline_subnums(cleaned)  # origin[i] = input line of cleaned line i+1
    sections = merge_split_titles(parse_sections(cleaned))
    chunks: list[Chunk] = []
    for c in build_chunks(sections):
        chunks.extend(split_oversize(c))
    assign_ids(book, chunks)

    for c in chunks:
        c.stars = dict(sorted(sdet.count(c.text).items(), key=lambda kv: (-kv[1], kv[0])))
        c.palaces = dict(sorted(pdet.count(c.text).items(), key=lambda kv: (-kv[1], kv[0])))
        c.non_luan = is_non_luan(c)

    # preservation check: non-whitespace characters, cleaned input vs chunk bodies
    def nws(s: str) -> int:
        return len(re.sub(r"\s+", "", s))

    in_nws, out_nws = nws(cleaned), sum(nws(c.text) for c in chunks)
    roundtrip_ok = re.sub(r"\s+", " ", cleaned).strip() == re.sub(r"\s+", " ", "\n".join(c.text for c in chunks)).strip()

    out_dir = SOURCE_DIR / book.slug
    if write:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        for c in chunks:
            meta = {
                "id": c.id,
                "book": book.slug,
                "book_code": book.code,
                "book_title": book.title,
                "title": c.title,
                "heading_path": c.heading_path,
                "level": c.level,
                "ordinal": c.ordinal,
                "part": c.part,
                "parts": c.parts,
                "source_file": f"input/{book.input_name}",
                "source_lines": f"{origin[c.start_line - 1]}-{origin[c.end_line - 1]}",
                "chars": len(c.text),
                "stars_detected": list(c.stars)[:20],
                "stars_in_title": sorted(tdet.count(c.title)),
                "palaces_detected": list(c.palaces)[:6],
                "non_luan": c.non_luan,
            }
            (out_dir / c.filename).write_text(dump_frontmatter(meta) + "\n" + c.text, encoding="utf-8")

    sizes = sorted(_size(c.lines) for c in chunks)
    return {
        "book": book.slug,
        "code": book.code,
        "input_chars": len(raw),
        "cleaned_chars": len(cleaned),
        "input_nonws_chars": nws(raw),
        "cleaned_nonws_chars": in_nws,
        "chunk_nonws_chars": out_nws,
        "nonws_delta": in_nws - out_nws,
        "roundtrip_whitespace_insensitive": roundtrip_ok,
        "sections": len(sections),
        "chunks": len(chunks),
        "chunks_split_from_oversize": sum(1 for c in chunks if c.parts > 1),
        "non_luan_chunks": sum(1 for c in chunks if c.non_luan),
        "chunks_over_max": sum(1 for s in sizes if s > MAX_CHUNK),
        "size_min": sizes[0] if sizes else 0,
        "size_median": sizes[len(sizes) // 2] if sizes else 0,
        "size_max": sizes[-1] if sizes else 0,
        "output_dir": str(out_dir.relative_to(SOURCE_DIR.parent.parent.parent)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--books", default="all", help="comma-separated book codes (tb,tl,td,npl) or 'all'")
    ap.add_argument("--dry-run", action="store_true", help="compute and report without writing files")
    args = ap.parse_args(argv)

    codes = [b.code for b in BOOKS] if args.books == "all" else args.books.split(",")
    unknown = [c for c in codes if c not in {b.code for b in BOOKS}]
    if unknown:
        ap.error(f"mã sách không hợp lệ: {unknown}")

    stars = load_stars(INDEX_DIR / "stars.md")
    palaces = load_palaces(INDEX_DIR / "palaces.md")
    sdet, pdet = star_detector(stars), palace_detector(palaces)
    # titles are short and star-dense, so short forms ("Không, Kiếp") are safe there
    tdet = NameDetector({s.id: [s.name] + s.aliases + [a for a in s.abbreviations if "." not in a]
                         for s in stars.values()})

    # corpus statistics use every book, whichever subset is written
    corpus = []
    for b in BOOKS:
        t = nfc((INPUT_DIR / b.input_name).read_text(encoding="utf-8"))
        for src, dst in REPLACEMENTS.items():
            t = t.replace(src, dst)
        corpus.append(t)
    words = corpus_word_counts(corpus)

    joins: collections.Counter = collections.Counter()
    reports = []
    for b in BOOKS:
        if b.code not in codes:
            continue
        rep = process_book(b, words, joins, sdet, pdet, tdet, write=not args.dry_run)
        reports.append(rep)
        flag = "OK " if rep["nonws_delta"] == 0 and rep["roundtrip_whitespace_insensitive"] else "!! "
        print(f"{flag}{b.code:<4}{rep['chunks']:>5} chunks  sections={rep['sections']:<4} "
              f"nonws-delta={rep['nonws_delta']:<4} over-max={rep['chunks_over_max']:<3} "
              f"non-luan={rep['non_luan_chunks']:<4} size min/med/max={rep['size_min']}/{rep['size_median']}/{rep['size_max']}")

    join_rows = sorted(({"rule": k.split("|")[0], "from": k.split("|")[1], "to": k.split("|")[2], "count": v}
                        for k, v in joins.items()), key=lambda r: (-r["count"], r["from"]))
    print(f"OCR joins: {sum(joins.values())} occurrences, {len(joins)} distinct "
          f"(rule A: {sum(r['count'] for r in join_rows if r['rule']=='A')}, rule B: {sum(r['count'] for r in join_rows if r['rule']=='B')})")

    if not args.dry_run:
        META_DIR.mkdir(parents=True, exist_ok=True)
        (META_DIR / "chunking-report.json").write_text(
            json.dumps({"books": reports, "settings": {"MIN_CHUNK": MIN_CHUNK, "TARGET_CHUNK": TARGET_CHUNK,
                                                          "MAX_CHUNK": MAX_CHUNK}}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        (META_DIR / "ocr-joins.json").write_text(json.dumps(join_rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {META_DIR / 'chunking-report.json'} and ocr-joins.json")

    bad = [r for r in reports if r["nonws_delta"] != 0 or not r["roundtrip_whitespace_insensitive"] or r["chunks_over_max"]]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
