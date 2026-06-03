#!/usr/bin/env python3
"""Build large Markdown knowledge files for ChatGPT Custom GPT uploads.

The script reads one cleaned Tu Vi Markdown book, removes conservative page
furniture, applies only narrow OCR fixes, and routes source sections into a
small set of large Markdown files. It does not summarize, embed, or create any
database artifacts.
"""

from __future__ import annotations

import argparse
import dataclasses
import re
import shutil
import sys
import unicodedata
from pathlib import Path


BOOK = "Tu Vi Dau So Tan Bien"
KNOWLEDGE_TYPE = "gpt_knowledge"
LANGUAGE = "vi"
LOSS_WARN_PERCENT = 2.0

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*-?\s*\d{1,4}\s*-?\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")

FILE_SPECS = [
    (
        "01_general_theory.md",
        "general_theory",
        "Ly thuyet tong quan, loi noi dau, dinh danh, ngu hanh, can chi va cac phu luan nen tang.",
    ),
    (
        "02_chart_setup_and_techniques.md",
        "chart_setup_and_techniques",
        "Lap thanh la so, dinh cung, an Menh, an Than, lap cuc, an sao va cac ky thuat thiet lap.",
    ),
    (
        "03_major_stars.md",
        "major_stars",
        "Dac tinh va luan giai cac chinh tinh.",
    ),
    (
        "04_auxiliary_stars.md",
        "auxiliary_stars",
        "Phu tinh, sat tinh, bai tinh, giai tinh va cac sao phu tro.",
    ),
    (
        "05_palaces.md",
        "palaces",
        "Luan doan cac cung: Menh, Phu Mau, Phuc Duc, Dien Trach, Quan Loc, No Boc, Thien Di, Tat Ach, Tai Bach, Tu Tuc, Phu The, Huynh De.",
    ),
    (
        "06_star_combinations.md",
        "star_combinations",
        "Cach cuc, to hop sao, hoi hop, dong cung va cac nhan xet theo bo sao.",
    ),
    (
        "07_four_transformations_and_cycles.md",
        "four_transformations_and_cycles",
        "Tu Hoa, Loc Ton, Thai Tue, Trang Sinh va cac vong sao luu chuyen.",
    ),
    (
        "08_fortune_periods.md",
        "fortune_periods",
        "Dai han, tieu han, luu nien, luu nguyet, van han, han chet va dam tang.",
    ),
    (
        "09_classical_verses.md",
        "classical_verses",
        "Cac cau phu, phu giai, quyet doan va trich dan co dien neu tach duoc tu ngu canh.",
    ),
    (
        "10_unsorted.md",
        "unsorted",
        "Noi dung khong du tin hieu de phan loai chac chan.",
    ),
]

INDEX_FILENAME = "00_index.md"

MAJOR_STARS = {
    "tu vi",
    "thien co",
    "thai duong",
    "vu khuc",
    "thien dong",
    "liem trinh",
    "thien phu",
    "thai am",
    "tham lang",
    "cu mon",
    "thien tuong",
    "thien luong",
    "that sat",
    "pha quan",
}

AUXILIARY_TERMS = {
    "kinh duong",
    "da la",
    "dia kiep",
    "dia khong",
    "hoa tinh",
    "linh tinh",
    "ta phu",
    "huu bat",
    "van xuong",
    "van khuc",
    "long tri",
    "phuong cac",
    "thien khoi",
    "thien viet",
    "thien khoc",
    "thien hu",
    "tam thai",
    "bat toa",
    "an quang",
    "thien quy",
    "thien duc",
    "nguyet duc",
    "thien hinh",
    "thien rieu",
    "thien y",
    "hong loan",
    "thien hy",
    "quoc an",
    "duong phu",
    "thien giai",
    "dia giai",
    "giai than",
    "thai phu",
    "phong cao",
    "thien tai",
    "thien tho",
    "thien thuong",
    "thien su",
    "thien la",
    "dia vong",
    "co than",
    "qua tu",
    "dao hoa",
    "thien ma",
    "kiep sat",
    "pha toai",
    "hoa cai",
    "luu ha",
    "thien tru",
    "bac sy",
    "dau quan",
    "thien khong",
    "tuan",
    "triet",
    "sat tinh",
    "bai tinh",
}

PALACE_TERMS = {
    "menh",
    "menh vien",
    "phu mau",
    "phuc duc",
    "dien trach",
    "quan loc",
    "no boc",
    "thien di",
    "tat ach",
    "tai bach",
    "tu tuc",
    "the thiep",
    "phu quan",
    "phu the",
    "huynh de",
}

CYCLE_TERMS = {
    "tu hoa",
    "hoa loc",
    "hoa quyen",
    "hoa khoa",
    "hoa ky",
    "loc ton",
    "thai tue",
    "trang sinh",
    "moc duc",
    "quan doi",
    "lam quan",
    "de vuong",
    "suy",
    "benh",
    "tu",
    "mo",
    "tuyet",
    "thai",
    "duong",
    "luc sat",
}

TECHNIQUE_TERMS = {
    "lap thanh",
    "dinh cung",
    "tim ban menh",
    "phan am duong",
    "dinh gio",
    "an menh",
    "an than",
    "lap cuc",
    "an sao",
    "dinh huong chieu",
    "tam chieu",
    "xung chieu",
    "nhi hop",
    "ngu hanh",
    "thap can",
    "thap nhi chi",
}

FORTUNE_TERMS = {
    "khoi han",
    "dai han",
    "tieu han",
    "luu dai han",
    "luu nien",
    "luu nguyet",
    "luu nhat",
    "luu thoi",
    "van han",
    "han chet",
    "dam tang",
    "nhap han",
}

COMBO_TERMS = {
    "cach",
    "cuc",
    "dong cung",
    "hoi hop",
    "toa thu",
    "giap cung",
    "vo chinh dieu",
    "thuong cach",
    "trung cach",
    "ha cach",
    "phi thuong cach",
    "phan cuc",
    "hang nguoi",
    "hinh tuong",
    "bieu tuong",
}

VERSE_TERMS = {
    "phu giai",
    "thai vi phu",
    "hoang kim phu",
    "tran doan",
    "quyet",
    "phu rang",
}

OCR_FIXES = {
    "Qúy": "Quý",
    "qúy": "quý",
    "Qủa": "Quả",
    "qủa": "quả",
    "Lồc": "Lộc",
    "B ạch": "Bạch",
    "Tài B ạch": "Tài Bạch",
    "H ữu": "Hữu",
    "Thái Tu ế": "Thái Tuế",
    "Ph ủ": "Phủ",
    "b ỏ": "bỏ",
    "đ ếm": "đếm",
    "c ủa": "của",
    "m ệnh": "mệnh",
}


@dataclasses.dataclass
class Block:
    order: int
    level: int
    title: str
    path: tuple[str, ...]
    text: str
    category: str = "unsorted"


@dataclasses.dataclass
class OutputDoc:
    filename: str
    category: str
    description: str
    blocks: list[Block]


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def norm(value: str) -> str:
    value = strip_accents(value).lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def remove_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :]


def clean_source(text: str) -> str:
    """Remove page furniture and apply narrow OCR fixes."""
    text = remove_frontmatter(text).replace("\ufeff", "")
    raw_lines = text.splitlines()
    normalized_counts: dict[str, int] = {}
    for raw_line in raw_lines:
        key = norm(raw_line.strip())
        if key:
            normalized_counts[key] = normalized_counts.get(key, 0) + 1

    cleaned_lines: list[str] = []
    previous = ""
    for raw_line in raw_lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        normalized = norm(stripped)
        if normalized in {"van dang thai thu lang", "tu vi dau so tan bien"} and normalized_counts.get(normalized, 0) > 3:
            continue
        if stripped and PAGE_NUMBER_RE.match(stripped) and previous:
            continue
        for src, dst in OCR_FIXES.items():
            line = line.replace(src, dst)
        cleaned_lines.append(line)
        if stripped:
            previous = stripped
    cleaned = "\n".join(cleaned_lines).strip() + "\n"
    return re.sub(r"\n{4,}", "\n\n\n", cleaned)


def parse_blocks(text: str) -> list[Block]:
    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    blocks: list[Block] = []
    start = 0
    current_level = 1
    current_title = "Mo dau"
    current_path: tuple[str, ...] = (current_title,)
    order = 1

    def emit(end: int) -> None:
        nonlocal order
        chunk = "\n".join(lines[start:end]).strip()
        if not chunk:
            return
        blocks.append(
            Block(
                order=order,
                level=current_level,
                title=current_title,
                path=current_path,
                text=chunk + "\n",
            )
        )
        order += 1

    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        if idx > start:
            emit(idx)
        level = len(match.group(1))
        title = match.group(2).strip()
        headings = [(existing_level, existing_title) for existing_level, existing_title in headings if existing_level < level]
        headings.append((level, title))
        current_level = level
        current_title = title
        current_path = tuple(title for _, title in headings)
        start = idx
    emit(len(lines))
    return blocks


def section_number(title: str) -> str:
    match = re.match(r"^(\d+(?:\.\d+)*)\.", title.strip())
    return match.group(1) if match else ""


def top_part(block: Block) -> str:
    joined = " ".join(norm(item) for item in block.path)
    if "phan 1" in joined or "lap thanh" in joined:
        return "part1"
    if "phan 2" in joined or "luan doan 12 cung" in joined:
        return "part2"
    if "phan 3" in joined or "luan doan van han" in joined:
        return "part3"
    return "front"


def has_any(value: str, terms: set[str]) -> bool:
    padded = f" {value} "
    return any(f" {term} " in padded for term in terms)


def classify(block: Block) -> str:
    title = norm(block.title)
    path_text = norm(" / ".join(block.path))
    sample = norm(block.text[:1800])
    combined = f"{path_text} {sample}"
    part = top_part(block)
    number = section_number(block.title)

    if has_any(combined, VERSE_TERMS):
        return "classical_verses"

    if part == "front":
        return "general_theory"

    if part == "part3" or has_any(combined, FORTUNE_TERMS):
        return "fortune_periods"

    if part == "part1":
        if number.startswith("8.3") or number.startswith("8.4") or number.startswith("8.5") or number.startswith("8.23"):
            return "four_transformations_and_cycles"
        if has_any(title, CYCLE_TERMS) and not number.startswith("8.1") and not number.startswith("8.2"):
            return "four_transformations_and_cycles"
        return "chart_setup_and_techniques"

    if part == "part2":
        if number.startswith("3."):
            if has_any(title, MAJOR_STARS):
                return "major_stars"
            if has_any(title, AUXILIARY_TERMS) or has_any(title, CYCLE_TERMS):
                return "auxiliary_stars"
        if number.startswith(("5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15")):
            return "palaces"
        if number.startswith(("19", "20", "23")) or has_any(combined, COMBO_TERMS):
            return "star_combinations"
        if number.startswith(("1", "2", "16", "21", "22")):
            return "general_theory"
        if number.startswith(("17", "18")):
            return "star_combinations"

    if has_any(title, MAJOR_STARS):
        return "major_stars"
    if has_any(title, PALACE_TERMS):
        return "palaces"
    if has_any(combined, CYCLE_TERMS):
        return "four_transformations_and_cycles"
    if has_any(combined, TECHNIQUE_TERMS):
        return "chart_setup_and_techniques"
    if has_any(combined, COMBO_TERMS):
        return "star_combinations"
    return "unsorted"


def normalize_headings(text: str) -> str:
    """Keep wording, but avoid multiple file-level H1 headings in output docs."""
    normalized_lines: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            level = min(len(match.group(1)) + 1, 6)
            normalized_lines.append("#" * level + " " + match.group(2).strip())
        else:
            normalized_lines.append(line)
    return "\n".join(normalized_lines).strip() + "\n"


def build_toc(blocks: list[Block]) -> str:
    seen: set[str] = set()
    lines = ["## Table of Contents", ""]
    if not blocks:
        lines.append("- No source sections classified here.")
        return "\n".join(lines) + "\n\n"
    for block in blocks:
        title = block.title.strip()
        if title in seen:
            continue
        seen.add(title)
        indent = "  " * max(0, min(block.level, 4) - 1)
        lines.append(f"{indent}- {title}")
    return "\n".join(lines) + "\n\n"


def frontmatter(source_name: str, category: str) -> str:
    return "\n".join(
        [
            "---",
            f"book: {yaml_quote(BOOK)}",
            f"source_file: {yaml_quote(source_name)}",
            f"knowledge_type: {yaml_quote(KNOWLEDGE_TYPE)}",
            f"category: {yaml_quote(category)}",
            f"language: {yaml_quote(LANGUAGE)}",
            "---",
            "",
        ]
    )


def render_doc(doc: OutputDoc, source_name: str) -> tuple[str, int]:
    title = doc.filename.removesuffix(".md").replace("_", " ").title()
    payload = "".join(block.text for block in doc.blocks)
    body = normalize_headings(payload) if payload else ""
    content = (
        frontmatter(source_name, doc.category)
        + f"# {title}\n\n"
        + f"{doc.description}\n\n"
        + build_toc(doc.blocks)
        + body
    )
    return content, len(payload)


def build_docs(blocks: list[Block]) -> list[OutputDoc]:
    for block in blocks:
        block.category = classify(block)
    docs = [
        OutputDoc(filename=filename, category=category, description=description, blocks=[])
        for filename, category, description in FILE_SPECS
    ]
    by_category = {doc.category: doc for doc in docs}
    for block in blocks:
        by_category.get(block.category, by_category["unsorted"]).blocks.append(block)
    return docs


def write_index(
    output_dir: Path,
    docs: list[OutputDoc],
    source_name: str,
    major_sections: list[str],
    report: dict[str, str],
) -> None:
    lines = [
        frontmatter(source_name, "index").rstrip(),
        "",
        "# 00 Index",
        "",
        "## Generated Files",
        "",
    ]
    for doc in docs:
        count = len(doc.blocks)
        lines.append(f"- [{doc.filename}]({doc.filename}) - {doc.description} Sections: {count}.")
    lines.extend(["", "## Detected Major Sections", ""])
    for section in major_sections:
        lines.append(f"- {section}")
    lines.extend(
        [
            "",
            "## Upload Order Recommendation",
            "",
            "1. 00_index.md",
            "2. 01_general_theory.md",
            "3. 02_chart_setup_and_techniques.md",
            "4. 03_major_stars.md",
            "5. 04_auxiliary_stars.md",
            "6. 07_four_transformations_and_cycles.md",
            "7. 05_palaces.md",
            "8. 06_star_combinations.md",
            "9. 08_fortune_periods.md",
            "10. 09_classical_verses.md",
            "11. 10_unsorted.md",
            "",
            "## Build Report",
            "",
        ]
    )
    for key, value in report.items():
        lines.append(f"- {key}: `{value}`")
    (output_dir / INDEX_FILENAME).write_text("\n".join(lines).strip() + "\n", encoding="utf-8", newline="\n")


def source_major_sections(blocks: list[Block]) -> list[str]:
    sections: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        if block.level <= 2 and block.title not in seen:
            seen.add(block.title)
            sections.append(block.title)
    return sections


def safe_prepare_output(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def build(input_path: Path, output_dir: Path) -> int:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    raw = input_path.read_text(encoding="utf-8")
    cleaned = clean_source(raw)
    blocks = parse_blocks(cleaned)
    docs = build_docs(blocks)

    safe_prepare_output(output_dir)

    payload_chars = 0
    for doc in docs:
        content, doc_payload_chars = render_doc(doc, input_path.name)
        payload_chars += doc_payload_chars
        (output_dir / doc.filename).write_text(content, encoding="utf-8", newline="\n")

    input_chars = len(cleaned)
    loss_percent = max(0.0, (input_chars - payload_chars) / input_chars * 100) if input_chars else 0.0
    unsorted_chars = sum(len(block.text) for block in next(doc for doc in docs if doc.category == "unsorted").blocks)
    warnings: list[str] = []
    if loss_percent > LOSS_WARN_PERCENT:
        warnings.append(f"Content loss exceeds {LOSS_WARN_PERCENT:.0f}% threshold.")
    if not next(doc for doc in docs if doc.category == "unsorted").blocks:
        warnings.append("No unsorted sections were produced.")

    report = {
        "Input chars": str(input_chars),
        "Output chars": str(payload_chars),
        "Loss %": f"{loss_percent:.4f}",
        "Files created": str(len(docs) + 1),
        "Unsorted chars": str(unsorted_chars),
        "Warnings": "; ".join(warnings) if warnings else "None",
    }
    write_index(output_dir, docs, input_path.name, source_major_sections(blocks), report)

    print(f"Input chars: {input_chars}")
    print(f"Output chars: {payload_chars}")
    print(f"Loss %: {loss_percent:.4f}")
    print(f"Files created: {len(docs) + 1}")
    print(f"Unsorted chars: {unsorted_chars}")
    print(f"Warnings: {report['Warnings']}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Custom GPT knowledge Markdown files from Tu Vi source Markdown.")
    parser.add_argument("--input", required=True, type=Path, help="Input cleaned Markdown file.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for generated Markdown files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return build(args.input, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
