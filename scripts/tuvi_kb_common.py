#!/usr/bin/env python3
"""Shared helpers for the tuvi-kb pipeline (chunk_sources.py, validate_kb.py).

Kept dependency-free on purpose: only the standard library, so the scripts run
on a bare Python install. The frontmatter reader/writer supports the small YAML
subset the knowledge base uses (scalars, quoted strings, flow lists, block lists).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
KB_DIR = ROOT / "output" / "tuvi-kb"
INDEX_DIR = KB_DIR / "00-index"
SOURCE_DIR = KB_DIR / "90-source"
META_DIR = KB_DIR / "_meta"


@dataclass(frozen=True)
class Book:
    code: str  # tb, tl, td, npl
    slug: str  # directory name under 90-source
    input_name: str
    title: str
    primary: bool


BOOKS: tuple[Book, ...] = (
    Book("tb", "tan-bien", "TU-VI-DAU-SO-TAN-BIEN.clean.md", "Tử Vi Đẩu Số Tân Biên", True),
    Book("tl", "thien-luong", "TU-VI-THIEN-LUONG.clean.md", "Tử Vi Nghiệm Lý Toàn Thư (Thiên Lương)", True),
    Book("td", "tran-doan", "TU-VI-DAU-SO-TOAN-THU-TRAN-DOAN.clean.md", "Tử Vi Đẩu Số Toàn Thư (Trần Đoàn)", False),
    Book("npl", "nguyen-phat-loc", "TU-VI-TONG-HOP-NGUYEN-PHAT-LOC.clean.md", "Tử Vi Tổng Hợp (Nguyễn Phát Lộc)", False),
)
BOOK_BY_CODE = {b.code: b for b in BOOKS}

SOURCE_LABELS = {"tb": "[TB]", "tl": "[TL]", "td": "[TĐ]", "npl": "[NPL]"}
LABEL_TO_CODE = {v: k for k, v in SOURCE_LABELS.items()}
PRIMARY_CODES = frozenset(b.code for b in BOOKS if b.primary)
CROSS_CODES = frozenset(b.code for b in BOOKS if not b.primary)

# Tý and Tỵ both slug to "ty"; the knowledge base spells the snake branch "ti".
BRANCH_IDS = ("ty", "suu", "dan", "mao", "thin", "ti", "ngo", "mui", "than", "dau", "tuat", "hoi")


# --------------------------------------------------------------------------- text


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def fold(text: str) -> str:
    """Accent-free, case-preserving form used for matching star names."""
    return strip_accents(text).replace("Đ", "D").replace("đ", "d")


def normalize_key(text: str) -> str:
    """ASCII slug: 'Tử Vi' -> 'tu-vi'."""
    text = fold(text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def squash_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------- frontmatter


class FrontmatterError(ValueError):
    pass


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s+(.*))?$")


def _scalar(raw: str):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if raw in ("true", "True"):
        return True
    if raw in ("false", "False"):
        return False
    if raw in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _flow_list(raw: str) -> list:
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    items, cur, quote = [], [], None
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch == ",":
            items.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    items.append("".join(cur))
    return [_scalar(i) for i in items if i.strip() != ""]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (metadata, body). Raises FrontmatterError on malformed input."""
    if not text.startswith("---\n"):
        raise FrontmatterError("thiếu khối frontmatter '---' ở đầu file")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise FrontmatterError("khối frontmatter không đóng bằng '---'")
    block = text[4:end].split("\n")
    body = text[end + 5 :]
    meta: dict = {}
    key = None
    i = 0
    while i < len(block):
        line = block[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if m:
            key, rest = m.group(1), (m.group(2) or "")
            if rest.strip() == "":
                meta[key] = []  # block list follows (or empty)
            elif rest.strip().startswith("["):
                meta[key] = _flow_list(rest)
            else:
                meta[key] = _scalar(rest)
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key is not None and isinstance(meta.get(key), list):
            meta[key].append(_scalar(item.group(1)))
            continue
        raise FrontmatterError(f"dòng frontmatter không hợp lệ: {line!r}")
    return meta, body


def _yaml_str(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "null"
    s = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./#+-]+", s) and not re.fullmatch(r"-?\d+|true|false|null", s):
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, (list, tuple)):
            if not value:
                lines.append(f"{key}: []")
            elif all(isinstance(v, (str, int)) and len(str(v)) < 60 for v in value) and len(value) <= 12:
                lines.append(f"{key}: [" + ", ".join(_yaml_str(v) for v in value) + "]")
            else:
                lines.append(f"{key}:")
                lines.extend(f"  - {_yaml_str(v)}" for v in value)
        else:
            lines.append(f"{key}: {_yaml_str(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------- registry


def load_table(path: Path) -> list[dict[str, str]]:
    """Parse the first markdown table in a file; keys are slugged header cells."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if header and rows:
                break
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [normalize_key(c) for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        if len(cells) != len(header):
            raise ValueError(f"{path.name}: hàng bảng có {len(cells)} ô, header có {len(header)}: {line!r}")
        rows.append(dict(zip(header, cells)))
    return rows


def _split_list(cell: str) -> list[str]:
    return [x.strip() for x in cell.split(";") if x.strip()]


@dataclass
class Star:
    id: str
    name: str
    aliases: list[str]
    abbreviations: list[str]
    group: str
    element: str
    polarity: str
    detect: bool
    note: str


@dataclass
class Palace:
    id: str
    name: str
    aliases: list[str]
    directory: str
    detect: bool
    note: str


def load_stars(path: Path | None = None) -> dict[str, Star]:
    path = path or INDEX_DIR / "stars.md"
    stars: dict[str, Star] = {}
    for row in load_table(path):
        star = Star(
            id=row["id"],
            name=row["ten"],
            aliases=_split_list(row.get("aliases", "")),
            abbreviations=_split_list(row.get("viet-tat", "")),
            group=row.get("nhom", ""),
            element=row.get("hanh", ""),
            polarity=row.get("am-duong", ""),
            detect=row.get("do", "").strip().lower() in ("x", "yes", "co", "có"),
            note=row.get("ghi-chu", ""),
        )
        if star.id in stars:
            raise ValueError(f"stars.md: id trùng: {star.id}")
        stars[star.id] = star
    return stars


def load_palaces(path: Path | None = None) -> dict[str, Palace]:
    path = path or INDEX_DIR / "palaces.md"
    palaces: dict[str, Palace] = {}
    for row in load_table(path):
        palace = Palace(
            id=row["id"],
            name=row["ten"],
            aliases=_split_list(row.get("aliases", "")),
            directory=row.get("thu-muc", ""),
            detect=row.get("do", "").strip().lower() in ("x", "yes", "co", "có"),
            note=row.get("ghi-chu", ""),
        )
        if palace.id in palaces:
            raise ValueError(f"palaces.md: id trùng: {palace.id}")
        palaces[palace.id] = palace
    return palaces


# ---------------------------------------------------------------------- detection


class NameDetector:
    """Find registry names in text.

    Multi-word names ("Thiên Tướng", "Hoả Tinh") are matched accent- and
    case-insensitively on the folded text. Single-word aliases ("Tướng",
    "Hỏa", "Nhật") are matched exactly on the NFC text, case- and
    accent-sensitive, so "Hóa" is not Hỏa Tinh and "sinh nhật" is not Thái
    Dương. Longer names are matched first and their spans blanked in both
    texts, so "Tử" never fires inside "Tử Tức". fold() preserves string
    length, which is what lets one span blank both texts.
    """

    _WORD = r"[A-Za-z0-9À-ɏḀ-ỿ]"

    def __init__(self, entries: dict[str, list[str]]):
        patterns: list[tuple[int, str, bool, re.Pattern]] = []
        for ident, names in entries.items():
            for name in names:
                name = nfc(name.strip())
                if not name:
                    continue
                multi = " " in name
                needle = fold(name) if multi else name
                flags = re.I if multi else 0
                pat = re.compile(rf"(?<!{self._WORD}){re.escape(needle)}(?!{self._WORD})", flags)
                patterns.append((len(needle), ident, multi, pat))
        patterns.sort(key=lambda t: -t[0])
        self.patterns = patterns

    def count(self, text: str) -> dict[str, int]:
        text = nfc(text)
        folded = fold(text)
        assert len(folded) == len(text)
        nfc_chars = list(text)
        fold_chars = list(folded)
        counts: dict[str, int] = {}
        for _, ident, multi, pat in self.patterns:
            haystack = "".join(fold_chars if multi else nfc_chars)
            spans = [(m.start(), m.end()) for m in pat.finditer(haystack)]
            if not spans:
                continue
            counts[ident] = counts.get(ident, 0) + len(spans)
            for s, e in spans:
                for i in range(s, e):
                    nfc_chars[i] = " "
                    fold_chars[i] = " "
        return counts


def star_detector(stars: dict[str, Star]) -> NameDetector:
    return NameDetector({s.id: [s.name] + s.aliases for s in stars.values() if s.detect})


def palace_detector(palaces: dict[str, Palace]) -> NameDetector:
    return NameDetector({p.id: [p.name] + p.aliases for p in palaces.values() if p.detect})
