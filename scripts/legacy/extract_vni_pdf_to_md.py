#!/usr/bin/env python3
"""Extract legacy VNI-style Vietnamese PDF text to Markdown.

This utility is intentionally local/offline and depends only on pdfplumber.
It preserves source order, removes repeated page headers/page numbers, and
converts obvious aligned text grids to Markdown tables.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pdfplumber


FOOTER_RE = re.compile(r"^\s*-?\s*\d{1,4}\s*-?\s*$")


def u(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def build_vni_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}

    def add(src: str, dst: str) -> None:
        mapping[u(src)] = u(dst)

    add(r"\u00d1", r"\u0110")
    add(r"\u00f1", r"\u0111")

    for src, dst in {
        r"\u00f6\u00f4\u00f9": r"\u01b0\u1edb",
        r"\u00f6\u00f4\u00f8": r"\u01b0\u1edd",
        r"\u00f6\u00f4\u00fb": r"\u01b0\u1edf",
        r"\u00f6\u00f4\u00f5": r"\u01b0\u1ee1",
        r"\u00f6\u00f4\u00ef": r"\u01b0\u1ee3",
        r"\u00f6\u00f4": r"\u01b0\u01a1",
        r"\u00d6\u00d4\u00d9": r"\u01af\u1eda",
        r"\u00d6\u00d4\u00d8": r"\u01af\u1edc",
        r"\u00d6\u00d4\u00db": r"\u01af\u1ede",
        r"\u00d6\u00d4\u00d5": r"\u01af\u1ee0",
        r"\u00d6\u00d4\u00cf": r"\u01af\u1ee2",
        r"\u00d6\u00d4": r"\u01af\u01a0",
        r"o\u00f8a": r"o\u00e0",
        r"O\u00d8A": r"O\u00c0",
        r"O\u00d8a": r"O\u00e0",
        r"o\u00f8A": r"o\u00c0",
        r"o\u00f9a": r"o\u00e1",
        r"O\u00d9A": r"O\u00c1",
        r"o\u00fba": r"o\u1ea3",
        r"O\u00dbA": r"O\u1ea2",
        r"o\u00f5a": r"o\u00e3",
        r"O\u00d5A": r"O\u00c3",
        r"o\u00efa": r"o\u1ea1",
        r"O\u00cfA": r"O\u1ea0",
    }.items():
        add(src, dst)

    vowel_groups = [
        ("a", {
            r"\u00e2": r"\u00e2", r"\u00e1": r"\u1ea5", r"\u00e0": r"\u1ea7",
            r"\u00e5": r"\u1ea9", r"\u00e3": r"\u1eab", r"\u00e4": r"\u1ead",
            r"\u00ea": r"\u0103", r"\u00e9": r"\u1eaf", r"\u00e8": r"\u1eb1",
            r"\u00fa": r"\u1eb3", r"\u00fc": r"\u1eb5", r"\u00eb": r"\u1eb7",
        }),
        ("A", {
            r"\u00c2": r"\u00c2", r"\u00c1": r"\u1ea4", r"\u00c0": r"\u1ea6",
            r"\u00c5": r"\u1ea8", r"\u00c3": r"\u1eaa", r"\u00c4": r"\u1eac",
            r"\u00ca": r"\u0102", r"\u00c9": r"\u1eae", r"\u00c8": r"\u1eb0",
            r"\u00da": r"\u1eb2", r"\u00dc": r"\u1eb4", r"\u00cb": r"\u1eb6",
        }),
        ("e", {
            r"\u00e2": r"\u00ea", r"\u00e1": r"\u1ebf", r"\u00e0": r"\u1ec1",
            r"\u00e5": r"\u1ec3", r"\u00e3": r"\u1ec5", r"\u00e4": r"\u1ec7",
        }),
        ("E", {
            r"\u00c2": r"\u00ca", r"\u00c1": r"\u1ebe", r"\u00c0": r"\u1ec0",
            r"\u00c5": r"\u1ec2", r"\u00c3": r"\u1ec4", r"\u00c4": r"\u1ec6",
        }),
        ("o", {
            r"\u00e2": r"\u00f4", r"\u00e1": r"\u1ed1", r"\u00e0": r"\u1ed3",
            r"\u00e5": r"\u1ed5", r"\u00e3": r"\u1ed7", r"\u00e4": r"\u1ed9",
        }),
        ("O", {
            r"\u00c2": r"\u00d4", r"\u00c1": r"\u1ed0", r"\u00c0": r"\u1ed2",
            r"\u00c5": r"\u1ed4", r"\u00c3": r"\u1ed6", r"\u00c4": r"\u1ed8",
        }),
    ]
    for base, marks in vowel_groups:
        for mark, replacement in marks.items():
            add(base + mark, replacement)

    for src, dst in {
        r"\u00f4\u00f9": r"\u1edb",
        r"\u00f4\u00f8": r"\u1edd",
        r"\u00f4\u00fb": r"\u1edf",
        r"\u00f4\u00f5": r"\u1ee1",
        r"\u00f4\u00ef": r"\u1ee3",
        r"\u00f4": r"\u01a1",
        r"\u00d4\u00d9": r"\u1eda",
        r"\u00d4\u00d8": r"\u1edc",
        r"\u00d4\u00db": r"\u1ede",
        r"\u00d4\u00d5": r"\u1ee0",
        r"\u00d4\u00cf": r"\u1ee2",
        r"\u00d4": r"\u01a0",
        r"\u00f6\u00f9": r"\u1ee9",
        r"\u00f6\u00f8": r"\u1eeb",
        r"\u00f6\u00fb": r"\u1eed",
        r"\u00f6\u00f5": r"\u1eef",
        r"\u00f6\u00ef": r"\u1ef1",
        r"\u00f6": r"\u01b0",
        r"\u00d6\u00d9": r"\u1ee8",
        r"\u00d6\u00d8": r"\u1eea",
        r"\u00d6\u00db": r"\u1eec",
        r"\u00d6\u00d5": r"\u1eee",
        r"\u00d6\u00cf": r"\u1ef0",
        r"\u00d6": r"\u01af",
    }.items():
        add(src, dst)

    plain_groups = [
        ("a", {r"\u00f9": r"\u00e1", r"\u00f8": r"\u00e0", r"\u00fb": r"\u1ea3", r"\u00f5": r"\u00e3", r"\u00ef": r"\u1ea1"}),
        ("A", {r"\u00d9": r"\u00c1", r"\u00d8": r"\u00c0", r"\u00db": r"\u1ea2", r"\u00d5": r"\u00c3", r"\u00cf": r"\u1ea0"}),
        ("e", {r"\u00f9": r"\u00e9", r"\u00f8": r"\u00e8", r"\u00fb": r"\u1ebb", r"\u00f5": r"\u1ebd", r"\u00ef": r"\u1eb9"}),
        ("E", {r"\u00d9": r"\u00c9", r"\u00d8": r"\u00c8", r"\u00db": r"\u1eba", r"\u00d5": r"\u1ebc", r"\u00cf": r"\u1eb8"}),
        ("o", {r"\u00f9": r"\u00f3", r"\u00f8": r"\u00f2", r"\u00fb": r"\u1ecf", r"\u00f5": r"\u00f5", r"\u00ef": r"\u1ecd"}),
        ("O", {r"\u00d9": r"\u00d3", r"\u00d8": r"\u00d2", r"\u00db": r"\u1ece", r"\u00d5": r"\u00d5", r"\u00cf": r"\u1ecc"}),
        ("u", {r"\u00f9": r"\u00fa", r"\u00f8": r"\u00f9", r"\u00fb": r"\u1ee7", r"\u00f5": r"\u0169", r"\u00ef": r"\u1ee5"}),
        ("U", {r"\u00d9": r"\u00da", r"\u00d8": r"\u00d9", r"\u00db": r"\u1ee6", r"\u00d5": r"\u0168", r"\u00cf": r"\u1ee4"}),
        ("y", {r"\u00f9": r"\u00fd", r"\u00f8": r"\u1ef3", r"\u00fb": r"\u1ef7", r"\u00f5": r"\u1ef9"}),
        ("Y", {r"\u00d9": r"\u00dd", r"\u00d8": r"\u1ef2", r"\u00db": r"\u1ef6", r"\u00d5": r"\u1ef8"}),
    ]
    for base, marks in plain_groups:
        for mark, replacement in marks.items():
            add(base + mark, replacement)

    for src, dst in {
        r"\u00ec": r"\u00ec",
        r"\u00cc": r"\u00cc",
        r"\u00ed": r"\u00ed",
        r"\u00cd": r"\u00cd",
        r"\u00e6": r"\u1ec9",
        r"\u00c6": r"\u1ec8",
        r"\u00f3": r"\u0129",
        r"\u00d3": r"\u0128",
        r"\u00f2": r"\u1ecb",
        r"\u00d2": r"\u1eca",
        r"\u00ee": r"\u1ef5",
        r"\u00ce": r"\u1ef4",
    }.items():
        add(src, dst)

    return mapping


VNI_MAPPING = build_vni_mapping()
VNI_KEYS = sorted(VNI_MAPPING, key=len, reverse=True)


def decode_legacy(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        for key in VNI_KEYS:
            if text.startswith(key, i):
                out.append(VNI_MAPPING[key])
                i += len(key)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def split_columns(line: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]


def is_tableish(line: str) -> bool:
    parts = split_columns(line)
    return len(parts) >= 2 and sum(1 for part in parts if len(part) <= 42) >= max(2, len(parts) - 1)


def table_to_md(block: list[str]) -> list[str]:
    rows = [split_columns(line) for line in block if split_columns(line)]
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    return [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
        *["| " + " | ".join(row) + " |" for row in rows[1:]],
    ]


def normalize_para(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_allcaps_heading(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    return len(letters) >= 4 and "".join(letters).upper() == "".join(letters)


def heading_level(line: str) -> tuple[int, str]:
    text = normalize_para(line)
    if not text:
        return 0, text
    if is_allcaps_heading(text) and len(text) <= 110:
        return 1, text
    if re.match(r"^(Quyển|Chương|Phần)\s+", text, re.IGNORECASE):
        return 1, text
    if re.match(r"^[IVXLCDM]+[\.-]\s+", text):
        return 2, text
    if re.match(r"^\d+(?:\.\d+)*[\.-]\s+", text):
        return 3, text
    leading = len(line) - len(line.lstrip(" "))
    if leading >= 24 and len(text) <= 90 and len(text.split()) <= 12 and not text.endswith("."):
        return 2, text
    return 0, text


def visible_lines(raw: str, header_regex: re.Pattern[str]) -> list[str]:
    decoded = decode_legacy(raw)
    lines: list[str] = []
    for line in decoded.splitlines():
        line = line.rstrip()
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if FOOTER_RE.match(stripped):
            continue
        if header_regex.match(stripped):
            continue
        lines.append(line)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def next_nonblank(lines: list[str], start: int) -> str:
    for idx in range(start, len(lines)):
        if lines[idx].strip():
            return lines[idx]
    return ""


def process_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    para: list[str] = []
    table: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        text = normalize_para(" ".join(part.strip() for part in para))
        if text:
            level, title = heading_level(text)
            out.append(("#" * level + " " + title) if level else text)
            out.append("")
        para = []

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        if len(table) >= 2:
            out.extend(table_to_md(table))
            out.append("")
        else:
            para.extend(table)
        table = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            if table and is_tableish(next_nonblank(lines, idx + 1)):
                idx += 1
                continue
            flush_table()
            flush_para()
            idx += 1
            continue
        level, title = heading_level(line)
        if level:
            flush_table()
            flush_para()
            out.append("#" * level + " " + title)
            out.append("")
        elif is_tableish(line):
            flush_para()
            table.append(line)
        else:
            flush_table()
            para.append(line)
        idx += 1
    flush_table()
    flush_para()
    return out


def page_text(page: pdfplumber.page.Page, page_index: int, crop_top: int, crop_bottom: int) -> str:
    cropped = page if page_index == 0 else page.crop((0, crop_top, page.width, page.height - crop_bottom))
    return cropped.extract_text(layout=True, x_density=7.25, y_density=13) or ""


def extract(pdf_path: Path, output_path: Path, header_pattern: str, crop_top: int, crop_bottom: int) -> None:
    header_regex = re.compile(header_pattern)
    all_md: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            md = process_lines(visible_lines(page_text(page, page_index, crop_top, crop_bottom), header_regex))
            if not md:
                continue
            while all_md and all_md[-1] == "":
                all_md.pop()
            if all_md:
                all_md.append("")
            all_md.extend(md)

    text = "\n".join(all_md).strip() + "\n"
    cleanup = {
        "Aán": u(r"\u1ea4n"),
        "Aâm": u(r"\u00c2m"),
        "Aâu": u(r"\u00c2u"),
        "Oâng": u(r"\u00d4ng"),
        "Oân": u(r"\u00d4n"),
        "OÛ": u(r"\u1ede"),
        "Yù": u(r"\u00dd"),
        "treâân": u(r"tr\u00ean"),
        "probabiliteù": u(r"probabilit\u00e9"),
        "musteùrieux": u(r"myst\u00e9rieux"),
    }
    for source, target in cleanup.items():
        text = text.replace(source, target)
    output_path.write_text(text, encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract VNI-encoded Vietnamese PDF to Markdown.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header-pattern", required=True)
    parser.add_argument("--crop-top", type=int, default=58)
    parser.add_argument("--crop-bottom", type=int, default=34)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    extract(args.input, args.output, args.header_pattern, args.crop_top, args.crop_bottom)
    text = args.output.read_text(encoding="utf-8")
    print(args.output)
    print(f"chars {len(text)} lines {text.count(chr(10)) + 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
