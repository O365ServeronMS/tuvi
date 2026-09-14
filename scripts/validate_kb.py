#!/usr/bin/env python3
"""Validate tuvi-kb cards against the schema in output/tuvi-kb/_meta/schema.md.

Checks (E = error, W = warning):
  E frontmatter parses; required keys per card type; id matches path
  E star / palace ids exist in 00-index registries (luu-<id> accepted for han cards)
  E chunk ids in `chunks:` exist under 90-source
  E every bullet carries exactly one source label [TB] [TL] [TĐ] [NPL]
  E [TĐ]/[NPL] only inside "Đối chứng"; only [TB]/[TL] elsewhere
  E required sections present; "Nguyên văn" quotes are verbatim in a referenced chunk
  E two palace cards with the same palaces + stars; two star cards for one star
  E file over 100 KB          W card over 8 KB, index file over 60 KB
  E registry: duplicate ids, alias shared by two stars
Also writes _meta/coverage.json (which source chunks are referenced by cards).
Exit code 1 when any error was found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuvi_kb_common import (  # noqa: E402
    BRANCH_IDS,
    CROSS_CODES,
    INDEX_DIR,
    KB_DIR,
    LABEL_TO_CODE,
    META_DIR,
    PRIMARY_CODES,
    SOURCE_DIR,
    FrontmatterError,
    fold,
    load_palaces,
    load_stars,
    nfc,
    parse_frontmatter,
    squash_ws,
)

CARD_DIRS = {
    "10-stars": "star-card",
    "20-palaces": "palace-card",
    "30-combos": "combo-card",
    "40-han": "han-card",
    "50-rules": "rule-card",
    "60-phu": "phu-card",
}
ID_PREFIX = {"star-card": "star", "palace-card": "palace", "combo-card": "combo",
             "han-card": "han", "rule-card": "rule", "phu-card": "phu"}

REQUIRED_SECTIONS = {
    "star-card": ["Bản chất", "Vị trí miếu hãm", "Gặp sao khác", "Nam nữ", "Đối chứng", "Nguyên văn"],
    "palace-card": ["Kết luận", "Điều kiện và sắc thái", "Đối chứng", "Nguyên văn"],
    "combo-card": ["Thành phần", "Điều kiện thành cách", "Ý nghĩa", "Phá cách", "Cung áp dụng", "Đối chứng", "Nguyên văn"],
    "han-card": ["Kết luận", "Tốt khi", "Xấu khi", "Kết hợp Mệnh Thân", "Đối chứng", "Nguyên văn"],
    "rule-card": ["Điều kiện", "Kết luận", "Ngoại lệ", "Ví dụ trong sách", "Khi nào không áp dụng", "Nguyên văn"],
    "phu-card": ["Câu phú", "Giải nghĩa", "Sao và cung liên quan", "Nguồn giải", "Nguyên văn"],
}
LABEL_FREE_SECTIONS = {"Nguyên văn", "Phú liên quan", "Sao và cung liên quan", "Thành phần", "Cung áp dụng", "Câu phú"}
CROSS_SECTION = "Đối chứng"

REQUIRED_KEYS = {"id", "type", "primary", "chunks"}
LIST_KEYS = {"palace", "stars", "positions", "tags", "primary", "cross", "chunks"}
GENDERS = {"any", "nam", "nu"}

CARD_WARN_BYTES = 8 * 1024
FILE_MAX_BYTES = 100 * 1024
INDEX_WARN_BYTES = 60 * 1024
QUOTE_MAX_CHARS = 400

LABEL_RE = re.compile(r"^\[(TB|TL|TĐ|NPL)\]\s+\S")
BULLET_RE = re.compile(r"^\s*[-+*]\s+(.*)$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
QUOTE_RE = re.compile(r"^[\"“](.+)[\"”]\s*\(([^()\s]+)\)\s*$", re.S)
ELLIPSIS_SPLIT_RE = re.compile(r"\s*(?:\[\.\.\.\]|\[…\]|\.\.\.|…)\s*")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: Path | str, msg: str) -> None:
        self.errors.append(f"{_rel(path)}: {msg}")

    def warn(self, path: Path | str, msg: str) -> None:
        self.warnings.append(f"{_rel(path)}: {msg}")


def _rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(KB_DIR.parent.parent)).replace("\\", "/")
    except ValueError:
        return str(p)


def norm_quote(text: str) -> str:
    return squash_ws(nfc(text)).casefold()


# --------------------------------------------------------------------- registries


def check_registries(rep: Report):
    stars = palaces = None
    try:
        stars = load_stars()
    except Exception as exc:  # noqa: BLE001
        rep.error(INDEX_DIR / "stars.md", f"không đọc được sổ sao: {exc}")
    try:
        palaces = load_palaces()
    except Exception as exc:  # noqa: BLE001
        rep.error(INDEX_DIR / "palaces.md", f"không đọc được sổ cung: {exc}")
    if stars:
        seen: dict[str, str] = {}
        for s in stars.values():
            if not SLUG_RE.match(s.id):
                rep.error(INDEX_DIR / "stars.md", f"id không phải slug: {s.id}")
            if not s.detect:
                continue  # collisions only matter for automatic detection
            for name in [s.name] + s.aliases:
                key = fold(name).lower()
                if key in seen and seen[key] != s.id:
                    rep.error(INDEX_DIR / "stars.md", f"alias '{name}' dò cho cả {seen[key]} và {s.id}; tắt 'dò' ở một trong hai")
                seen.setdefault(key, s.id)
    if palaces:
        for p in palaces.values():
            if not SLUG_RE.match(p.id) or not SLUG_RE.match(p.directory):
                rep.error(INDEX_DIR / "palaces.md", f"id hoặc thư mục không phải slug: {p.id}")
    return stars or {}, palaces or {}


# ------------------------------------------------------------------------- chunks


def load_chunks(rep: Report) -> dict[str, dict]:
    chunks: dict[str, dict] = {}
    if not SOURCE_DIR.exists():
        rep.error(SOURCE_DIR, "chưa có tầng nguyên văn; chạy scripts/chunk_sources.py trước")
        return chunks
    for path in sorted(SOURCE_DIR.rglob("*.md")):
        try:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        except FrontmatterError as exc:
            rep.error(path, f"frontmatter khúc lỗi: {exc}")
            continue
        cid = meta.get("id")
        if not cid:
            rep.error(path, "khúc thiếu id")
            continue
        if cid in chunks:
            rep.error(path, f"id khúc trùng: {cid}")
        chunks[cid] = {"path": path, "book": meta.get("book_code"), "non_luan": bool(meta.get("non_luan")),
                       "norm": norm_quote(body)}
    return chunks


# -------------------------------------------------------------------------- cards


def split_sections(body: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Return (title line, [(section name, lines)])."""
    title = ""
    sections: list[tuple[str, list[str]]] = []
    cur_name, cur_lines = "(trước mục đầu)", []
    for line in body.split("\n"):
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        m = H2_RE.match(line)
        if m:
            sections.append((cur_name, cur_lines))
            cur_name, cur_lines = m.group(1), []
            continue
        cur_lines.append(line)
    sections.append((cur_name, cur_lines))
    return title, sections


def star_id_ok(sid: str, stars: dict, ctype: str) -> bool:
    if sid in stars:
        return True
    return ctype == "han-card" and sid.startswith("luu-") and sid[4:] in stars


def check_card(path: Path, ctype: str, stars: dict, palaces: dict, chunks: dict, rep: Report,
               seen_keys: dict, coverage: defaultdict) -> None:
    raw = path.read_text(encoding="utf-8")
    size = len(raw.encode("utf-8"))
    if size > FILE_MAX_BYTES:
        rep.error(path, f"file {size} byte, vượt {FILE_MAX_BYTES}")
    elif size > CARD_WARN_BYTES:
        rep.warn(path, f"thẻ {size} byte, nên dưới {CARD_WARN_BYTES}")

    try:
        meta, body = parse_frontmatter(raw)
    except FrontmatterError as exc:
        rep.error(path, f"frontmatter lỗi: {exc}")
        return

    missing = REQUIRED_KEYS - set(meta)
    if missing:
        rep.error(path, f"frontmatter thiếu khoá: {sorted(missing)}")
    for key in LIST_KEYS & set(meta):
        if not isinstance(meta[key], list):
            rep.error(path, f"khoá '{key}' phải là danh sách")
            meta[key] = []

    if meta.get("type") != ctype:
        rep.error(path, f"type '{meta.get('type')}' không khớp thư mục ({ctype})")

    stem = path.stem
    expected_id = f"{ID_PREFIX[ctype]}:{path.parent.name}:{stem}" if ctype == "palace-card" else f"{ID_PREFIX[ctype]}:{stem}"
    if meta.get("id") != expected_id:
        rep.error(path, f"id phải là '{expected_id}', đang là '{meta.get('id')}'")

    # sources
    primary = meta.get("primary") or []
    cross = meta.get("cross") or []
    if not primary or not set(primary) <= PRIMARY_CODES:
        rep.error(path, f"primary phải là tập con không rỗng của {sorted(PRIMARY_CODES)}: {primary}")
    if not set(cross) <= CROSS_CODES:
        rep.error(path, f"cross chỉ được chứa {sorted(CROSS_CODES)}: {cross}")

    # stars / palaces / positions / gender / tags
    card_stars = meta.get("stars") or []
    for sid in card_stars:
        if not star_id_ok(str(sid), stars, ctype):
            rep.error(path, f"sao '{sid}' không có trong 00-index/stars.md")
    if ctype == "star-card" and len(card_stars) != 1:
        rep.error(path, "star-card phải có đúng một sao trong 'stars'")
    if ctype == "combo-card" and len(card_stars) < 2:
        rep.error(path, "combo-card phải có ít nhất hai sao trong 'stars'")
    if ctype == "palace-card":
        card_palaces = meta.get("palace") or []
        if not card_palaces or not card_stars:
            rep.error(path, "palace-card cần 'palace' và 'stars' không rỗng")
        dirs = set()
        for pid in card_palaces:
            if pid not in palaces:
                rep.error(path, f"cung '{pid}' không có trong 00-index/palaces.md")
            else:
                dirs.add(palaces[pid].directory)
        if dirs and dirs != {path.parent.name}:
            rep.error(path, f"cung {card_palaces} thuộc thư mục {sorted(dirs)}, file nằm ở '{path.parent.name}'")
        if card_stars and all(star_id_ok(str(s), stars, ctype) for s in card_stars):
            if stem != "+".join(card_stars):
                rep.error(path, f"tên file phải là '{'+'.join(card_stars)}.md' theo thứ tự 'stars'")
            groups = [stars[s].group if s in stars else "" for s in card_stars]
            main_idx = [i for i, g in enumerate(groups) if g == "chinh-tinh"]
            if main_idx and main_idx != list(range(len(main_idx))):
                rep.warn(path, "chính tinh nên đứng trước phụ tinh trong 'stars' và tên file")
        key = (tuple(sorted(card_palaces)), tuple(sorted(card_stars)))
        if key in seen_keys:
            rep.error(path, f"trùng bộ sao và cung với {_rel(seen_keys[key])}")
        seen_keys.setdefault(key, path)
    elif ctype == "star-card" and card_stars:
        key = ("star", card_stars[0])
        if key in seen_keys:
            rep.error(path, f"đã có thẻ sao cho '{card_stars[0]}': {_rel(seen_keys[key])}")
        seen_keys.setdefault(key, path)
        if stem != card_stars[0]:
            rep.error(path, f"tên file phải là '{card_stars[0]}.md'")

    for pos in meta.get("positions") or []:
        if pos not in BRANCH_IDS:
            rep.error(path, f"positions chứa địa chi lạ '{pos}', hợp lệ: {list(BRANCH_IDS)}")
    if "gender" in meta and meta["gender"] not in GENDERS:
        rep.error(path, f"gender phải thuộc {sorted(GENDERS)}")
    for tag in meta.get("tags") or []:
        if not SLUG_RE.match(str(tag)):
            rep.error(path, f"tag '{tag}' phải là slug ASCII")

    # chunks
    card_chunks = [str(c) for c in (meta.get("chunks") or [])]
    if not card_chunks:
        rep.error(path, "thẻ phải tham chiếu ít nhất một khúc trong 'chunks'")
    for cid in card_chunks:
        if cid not in chunks:
            rep.error(path, f"khúc '{cid}' không tồn tại trong 90-source")
        else:
            coverage[cid].append(meta.get("id") or _rel(path))
    referenced_books = {chunks[c]["book"] for c in card_chunks if c in chunks}
    for code in primary:
        if chunks and code not in referenced_books:
            rep.warn(path, f"primary có '{code}' nhưng không tham chiếu khúc nào của sách đó")

    # body
    title, sections = split_sections(body)
    if not title:
        rep.error(path, "thiếu tiêu đề '# ...' ở đầu thân bài")
    names = [n for n, _ in sections]
    for req in REQUIRED_SECTIONS[ctype]:
        if req not in names:
            rep.error(path, f"thiếu mục '## {req}'")
    dup = {n for n in names if names.count(n) > 1 and n != "(trước mục đầu)"}
    if dup:
        rep.error(path, f"mục lặp lại: {sorted(dup)}")
    if cross and CROSS_SECTION in names:
        cross_lines = "\n".join(dict(sections)[CROSS_SECTION])
        for code in cross:
            label = {v: k for k, v in LABEL_TO_CODE.items()}[code]
            if label not in cross_lines:
                rep.warn(path, f"cross có '{code}' nhưng mục Đối chứng không có dòng {label}")

    quotes_found = 0
    for name, lines in sections:
        if name == "Nguyên văn":
            quotes_found += check_quotes(path, lines, card_chunks, chunks, rep)
            continue
        for line in lines:
            m = BULLET_RE.match(line)
            if not m:
                continue
            content = m.group(1)
            if name in LABEL_FREE_SECTIONS:
                continue
            lm = LABEL_RE.match(content)
            if not lm:
                rep.error(path, f"[{name}] gạch đầu dòng thiếu nhãn nguồn: {content[:60]!r}")
                continue
            code = LABEL_TO_CODE[f"[{lm.group(1)}]"]
            if name == CROSS_SECTION and code not in CROSS_CODES:
                rep.error(path, f"[{name}] chỉ nhận nhãn [TĐ]/[NPL], gặp [{lm.group(1)}]")
            if name != CROSS_SECTION and code not in PRIMARY_CODES:
                rep.error(path, f"[{name}] chỉ nhận nhãn [TB]/[TL], gặp [{lm.group(1)}]: {content[:60]!r}")
            if code in PRIMARY_CODES and code not in primary:
                rep.error(path, f"[{name}] dùng nhãn [{lm.group(1)}] nhưng frontmatter primary={primary}")
    if "Nguyên văn" in names and quotes_found == 0:
        rep.error(path, "mục Nguyên văn không có trích dẫn hợp lệ dạng > \"...\" (id-khúc)")


def check_quotes(path: Path, lines: list[str], card_chunks: list[str], chunks: dict, rep: Report) -> int:
    groups: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if line.startswith(">"):
            text = line[1:].lstrip()
            if text == "" and cur:
                groups.append(cur)
                cur = []
            elif text:
                cur.append(text)
        elif cur:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    ok = 0
    for group in groups:
        joined = " ".join(group).strip()
        m = QUOTE_RE.match(joined)
        if not m:
            rep.error(path, f"[Nguyên văn] trích dẫn sai dạng, cần > \"...\" (id-khúc): {joined[:60]!r}")
            continue
        quote, cid = m.group(1), m.group(2)
        if len(squash_ws(quote)) > QUOTE_MAX_CHARS:
            rep.error(path, f"[Nguyên văn] trích dẫn dài {len(squash_ws(quote))} ký tự, tối đa {QUOTE_MAX_CHARS}")
        if cid not in chunks:
            rep.error(path, f"[Nguyên văn] khúc '{cid}' không tồn tại")
            continue
        if cid not in card_chunks:
            rep.error(path, f"[Nguyên văn] khúc '{cid}' chưa được khai trong frontmatter 'chunks'")
        hay = chunks[cid]["norm"]
        pos = 0
        for seg in ELLIPSIS_SPLIT_RE.split(quote):
            seg_n = norm_quote(seg).strip("\"'“”‘’ ")
            if not seg_n:
                continue
            found = hay.find(seg_n, pos)
            if found < 0:
                rep.error(path, f"[Nguyên văn] đoạn không khớp nguyên văn trong {cid}: {seg_n[:50]!r}")
                break
            pos = found + len(seg_n)
        else:
            ok += 1
    return ok


# ------------------------------------------------------------------------- driver


def check_index_sizes(rep: Report) -> None:
    if not INDEX_DIR.exists():
        return
    for path in INDEX_DIR.glob("*.md"):
        size = path.stat().st_size
        if size > INDEX_WARN_BYTES:
            rep.warn(path, f"file index {size} byte, nên dưới {INDEX_WARN_BYTES}")


def write_coverage(chunks: dict, coverage: defaultdict) -> dict:
    per_book: dict[str, dict] = {}
    for cid, info in chunks.items():
        book = per_book.setdefault(info["book"], {"chunks": 0, "non_luan": 0, "referenced": 0, "unreferenced": []})
        book["chunks"] += 1
        if info["non_luan"]:
            book["non_luan"] += 1
            continue
        if cid in coverage:
            book["referenced"] += 1
        else:
            book["unreferenced"].append(cid)
    for book in per_book.values():
        luan = book["chunks"] - book["non_luan"]
        book["coverage_percent"] = round(100 * book["referenced"] / luan, 1) if luan else 0.0
        book["unreferenced"].sort()
    summary = {"books": per_book, "chunk_refs": {cid: sorted(set(v)) for cid, v in sorted(coverage.items())}}
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / "coverage.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return per_book


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="chỉ kiểm các file/thư mục thẻ này (mặc định: toàn bộ)")
    ap.add_argument("--no-coverage", action="store_true", help="không ghi _meta/coverage.json")
    ap.add_argument("--quiet", action="store_true", help="chỉ in tổng kết")
    args = ap.parse_args(argv)

    rep = Report()
    stars, palaces = check_registries(rep)
    chunks = load_chunks(rep)
    check_index_sizes(rep)

    card_paths: list[tuple[Path, str]] = []
    for dirname, ctype in CARD_DIRS.items():
        d = KB_DIR / dirname
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name.startswith("_"):
                continue
            card_paths.append((p, ctype))
    if args.paths:
        wanted = [Path(p).resolve() for p in args.paths]
        card_paths = [(p, t) for p, t in card_paths if any(p.resolve() == w or w in p.resolve().parents for w in wanted)]

    seen_keys: dict = {}
    coverage: defaultdict = defaultdict(list)
    for p, ctype in card_paths:
        check_card(p, ctype, stars, palaces, chunks, rep, seen_keys, coverage)

    per_book = {}
    if not args.no_coverage and not args.paths and chunks:
        per_book = write_coverage(chunks, coverage)

    if not args.quiet:
        for w in rep.warnings:
            print(f"WARN  {w}")
        for e in rep.errors:
            print(f"ERROR {e}")
    print(f"thẻ kiểm: {len(card_paths)}  khúc nguồn: {len(chunks)}  lỗi: {len(rep.errors)}  cảnh báo: {len(rep.warnings)}")
    for code, info in per_book.items():
        print(f"  phủ {code}: {info['referenced']}/{info['chunks'] - info['non_luan']} khúc luận ({info['coverage_percent']}%), non_luan={info['non_luan']}")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
