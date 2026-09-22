#!/usr/bin/env python3
"""Merge two cleaned Tu Vi Markdown books into a Custom GPT knowledge pack.

The script groups content by topic while preserving source separation inside
each generated Markdown file. It performs no summarization, no embedding, and
does not call external services.
"""

from __future__ import annotations

import argparse
import dataclasses
import re
import shutil
import sys
import unicodedata
from pathlib import Path


LOSS_WARN_PERCENT = 2.0
PACK_NAME = "SEISMIC Tu Vi"
KNOWLEDGE_TYPE = "gpt_knowledge"
LANGUAGE = "vi"

INDEX_FILE = "00_index.md"

DOC_SPECS = [
    (
        "01_general_theory.md",
        "general_theory",
        "Ly thuyet tong quan",
        "Nen tang am duong, ngu hanh, can chi, loi gioi thieu, dinh danh va phu luan tong quat.",
    ),
    (
        "02_chart_setup_and_core_rules.md",
        "chart_setup_and_core_rules",
        "Lap thanh va quy tac an sao",
        "Dinh cung, tim ban menh, an Menh, an Than, lap cuc, an sao va cac quy tac lap la so.",
    ),
    (
        "03_major_stars.md",
        "major_stars",
        "Chinh tinh",
        "Cac muc ve 14 chinh tinh va dac tinh cua tung sao.",
    ),
    (
        "04_auxiliary_stars.md",
        "auxiliary_stars",
        "Phu tinh",
        "Phu tinh, sat tinh, bai tinh, giai tinh va cac sao phu tro quan trong.",
    ),
    (
        "05_palaces.md",
        "palaces",
        "Muoi hai cung",
        "Luan doan cac cung Menh, Than, Phu Mau, Phuc Duc, Dien Trach, Quan Loc, No Boc, Thien Di, Tat Ach, Tai Bach, Tu Tuc, Phu The va Huynh De.",
    ),
    (
        "06_star_combinations.md",
        "star_combinations",
        "To hop sao va cach cuc",
        "Cach cuc, hoi hop, dong cung, giap cung, vo chinh dieu va cac bo sao phoi hop.",
    ),
    (
        "07_four_transformations_cycles_and_life_periods.md",
        "four_transformations_cycles_and_life_periods",
        "Tu Hoa va cac vong sao",
        "Tu Hoa, Loc Ton, Thai Tue, Trang Sinh, vong sao va cac chu ky doi nguoi.",
    ),
    (
        "08_thien_luong_method.md",
        "thien_luong_method",
        "Phuong phap nghiem ly Thien Luong",
        "Cac khai trien dac thu cua Thien Luong ve nghiem ly, tam hop tuoi, tinh dau va nhan sinh.",
    ),
    (
        "09_fortune_periods_and_limitation.md",
        "fortune_periods_and_limitation",
        "Van han",
        "Dai han, tieu han, luu nien, luu nguyet, luu nhat, han chet, dam tang va gioi han luan doan.",
    ),
    (
        "10_classical_verses_and_cautions.md",
        "classical_verses_and_cautions",
        "Phu quyet va can trong",
        "Phu giai, phu quyet, loi can trong, phe binh va cac ghi chu tranh lap luan qua muc.",
    ),
    (
        "11_case_studies.md",
        "case_studies",
        "La so va vi du",
        "Phu luc, la so mau, truong hop nghiem ly va cac vi du ung dung.",
    ),
    (
        "12_unsorted.md",
        "unsorted",
        "Chua phan loai",
        "Noi dung khong du tin hieu de phan loai chac chan.",
    ),
]


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*-?\s*\d{1,4}\s*-?\s*$")
SECTION_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)*)\.")


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
    "ta phu",
    "huu bat",
    "van xuong",
    "van khuc",
    "thien khoi",
    "thien viet",
    "thien ma",
    "kinh duong",
    "da la",
    "hoa tinh",
    "linh tinh",
    "dia khong",
    "dia kiep",
    "thien hinh",
    "thien rieu",
    "thien khoc",
    "thien hu",
    "tuan",
    "triet",
    "dao hoa",
    "hong loan",
    "thien hy",
    "long tri",
    "phuong cac",
    "tam thai",
    "bat toa",
    "co than",
    "qua tu",
    "hoa cai",
    "luu ha",
    "thien tru",
    "dau quan",
    "phuc duc",
    "quan phu",
    "tu phu",
    "truc phu",
    "tue pha",
    "long duc",
    "dieu khach",
    "thanh long",
    "tuong quan",
    "tau thu",
    "phi liem",
    "hy than",
    "benh phu",
    "phuc binh",
    "sat tinh",
    "bai tinh",
}

PALACE_TERMS = {
    "menh",
    "than",
    "phu mau",
    "phuc duc",
    "dien trach",
    "quan loc",
    "no boc",
    "thien di",
    "tat ach",
    "tai bach",
    "tu tuc",
    "phu the",
    "the thiep",
    "phu quan",
    "huynh de",
}

CORE_RULE_TERMS = {
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
}

THEORY_TERMS = {
    "nguyen ly",
    "60 hoa giap",
    "can chi",
    "ngu hanh",
    "nap am",
    "am duong",
    "dinh danh",
    "ban menh",
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
    "mo",
    "tuyet",
    "thai",
    "duong",
    "vong thai tue",
    "vong loc ton",
    "vong trang sinh",
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
    "nhap han",
    "han chet",
    "dam tang",
}

COMBO_TERMS = {
    "cach",
    "cuc",
    "dong cung",
    "hoi hop",
    "toa thu",
    "giap cung",
    "vo chinh dieu",
    "tam hop",
    "nhi hop",
    "tinh dau",
    "doi cung",
    "lien chau",
    "phan cuc",
    "thuong cach",
    "trung cach",
    "ha cach",
    "phi thuong cach",
}

THIEN_LUONG_METHOD_TERMS = {
    "thien luong",
    "nghiem ly",
    "tam hop tuoi",
    "tuoi",
    "hanh nghe",
    "dao song",
    "nhan qua",
    "luan hoi",
    "nghiep qua",
    "hanh phuc",
}

VERSE_CAUTION_TERMS = {
    "phu giai",
    "thai vi phu",
    "hoang kim phu",
    "tran doan",
    "phu rang",
    "quyet",
    "can trong",
    "phe binh",
    "chi trich",
    "khong chu truong",
}

CASE_TERMS = {
    "phu luc",
    "la so",
    "la so thu",
    "vi du",
    "truong hop",
    "nghiem chung",
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
class SourceBook:
    key: str
    label: str
    path: Path
    cleaned_text: str
    blocks: list["Block"]


@dataclasses.dataclass
class Block:
    order: int
    source_key: str
    source_label: str
    level: int
    title: str
    path: tuple[str, ...]
    text: str
    category: str = "unsorted"


@dataclasses.dataclass
class OutputDoc:
    filename: str
    category: str
    title: str
    description: str
    blocks_by_source: dict[str, list[Block]]


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def norm(value: str) -> str:
    value = strip_accents(value).lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def has_any(value: str, terms: set[str]) -> bool:
    padded = f" {value} "
    return any(f" {term} " in padded for term in terms)


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
    text = remove_frontmatter(text).replace("\ufeff", "")
    lines: list[str] = []
    previous_nonblank = ""
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped and PAGE_NUMBER_RE.match(stripped) and previous_nonblank:
            continue
        normalized = norm(stripped)
        if normalized in {
            "tu vi nghiem ly toan thu thien luong",
            "tu vi nghiem ly toan thu",
        } and previous_nonblank:
            continue
        for src, dst in OCR_FIXES.items():
            line = line.replace(src, dst)
        lines.append(line)
        if stripped:
            previous_nonblank = stripped
    cleaned = "\n".join(lines).strip() + "\n"
    return re.sub(r"\n{4,}", "\n\n\n", cleaned)


def parse_blocks(text: str, source_key: str, source_label: str) -> list[Block]:
    source_lines = text.splitlines()
    stack: list[tuple[int, str]] = []
    blocks: list[Block] = []
    start = 0
    current_level = 1
    current_title = "Mở đầu"
    current_path: tuple[str, ...] = (current_title,)
    order = 1

    def emit(end: int) -> None:
        nonlocal order
        chunk = "\n".join(source_lines[start:end]).strip()
        if not chunk:
            return
        blocks.append(
            Block(
                order=order,
                source_key=source_key,
                source_label=source_label,
                level=current_level,
                title=current_title,
                path=current_path,
                text=chunk + "\n",
            )
        )
        order += 1

    for idx, line in enumerate(source_lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        if idx > start:
            emit(idx)
        level = len(match.group(1))
        title = match.group(2).strip()
        stack = [(old_level, old_title) for old_level, old_title in stack if old_level < level]
        stack.append((level, title))
        current_level = level
        current_title = title
        current_path = tuple(title for _, title in stack)
        start = idx
    emit(len(source_lines))
    return blocks


def section_number(title: str) -> str:
    match = SECTION_NUMBER_RE.match(title.strip())
    return match.group(1) if match else ""


def top_context(block: Block) -> str:
    joined = norm(" ".join(block.path))
    if "phan 1" in joined or "lap thanh" in joined:
        return "tanbien_part1"
    if "phan 2" in joined or "luan doan 12 cung" in joined:
        return "tanbien_part2"
    if "phan 3" in joined or "luan doan van han" in joined:
        return "tanbien_part3"
    return "other"


def classify_tanbien(block: Block) -> str:
    title = norm(block.title)
    combined = norm(" ".join(block.path) + "\n" + block.text[:2000])
    number = section_number(block.title)
    context = top_context(block)

    if has_any(combined, VERSE_CAUTION_TERMS):
        return "classical_verses_and_cautions"
    if context == "other":
        return "general_theory"
    if context == "tanbien_part3" or has_any(combined, FORTUNE_TERMS):
        return "fortune_periods_and_limitation"
    if context == "tanbien_part1":
        if number.startswith(("8.3", "8.4", "8.5", "8.23")) or has_any(title, CYCLE_TERMS):
            return "four_transformations_cycles_and_life_periods"
        return "chart_setup_and_core_rules"
    if context == "tanbien_part2":
        if number.startswith("3."):
            if has_any(title, MAJOR_STARS):
                return "major_stars"
            return "auxiliary_stars"
        if number.startswith(("5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15")):
            return "palaces"
        if number.startswith(("17", "18", "19", "20", "23")) or has_any(combined, COMBO_TERMS):
            return "star_combinations"
        return "general_theory"
    return classify_generic(block)


def classify_thienluong(block: Block) -> str:
    title = norm(block.title)
    combined = norm(" ".join(block.path) + "\n" + block.text[:2500])

    if has_any(title, CASE_TERMS) or has_any(combined, CASE_TERMS):
        return "case_studies"
    if has_any(combined, VERSE_CAUTION_TERMS):
        return "classical_verses_and_cautions"
    if has_any(combined, FORTUNE_TERMS):
        return "fortune_periods_and_limitation"
    if has_any(combined, CYCLE_TERMS):
        return "four_transformations_cycles_and_life_periods"
    if has_any(combined, THIEN_LUONG_METHOD_TERMS):
        return "thien_luong_method"
    if has_any(title, PALACE_TERMS) and ("cung" in title or title in PALACE_TERMS):
        return "palaces"
    if has_any(title, MAJOR_STARS):
        return "major_stars"
    if has_any(title, AUXILIARY_TERMS):
        return "auxiliary_stars"
    if has_any(combined, COMBO_TERMS):
        return "star_combinations"
    if has_any(combined, CORE_RULE_TERMS):
        return "chart_setup_and_core_rules"
    if has_any(combined, THEORY_TERMS):
        return "general_theory"
    return "unsorted"


def classify_generic(block: Block) -> str:
    title = norm(block.title)
    combined = norm(" ".join(block.path) + "\n" + block.text[:2000])
    if has_any(combined, VERSE_CAUTION_TERMS):
        return "classical_verses_and_cautions"
    if has_any(combined, FORTUNE_TERMS):
        return "fortune_periods_and_limitation"
    if has_any(combined, CYCLE_TERMS):
        return "four_transformations_cycles_and_life_periods"
    if has_any(title, MAJOR_STARS):
        return "major_stars"
    if has_any(title, AUXILIARY_TERMS):
        return "auxiliary_stars"
    if has_any(title, PALACE_TERMS):
        return "palaces"
    if has_any(combined, CORE_RULE_TERMS):
        return "chart_setup_and_core_rules"
    if has_any(combined, COMBO_TERMS):
        return "star_combinations"
    if has_any(combined, THEORY_TERMS):
        return "general_theory"
    return "unsorted"


def classify_blocks(book: SourceBook) -> None:
    for block in book.blocks:
        if book.key == "tanbien":
            block.category = classify_tanbien(block)
        elif book.key == "thienluong":
            block.category = classify_thienluong(block)
        else:
            block.category = classify_generic(block)


def normalize_headings(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            level = min(len(match.group(1)) + 2, 6)
            lines.append("#" * level + " " + match.group(2).strip())
        else:
            lines.append(line)
    return "\n".join(lines).strip() + "\n"


def make_frontmatter(category: str) -> str:
    return "\n".join(
        [
            "---",
            f"knowledge_pack: {yaml_quote(PACK_NAME)}",
            "source_books:",
            '  - "Tu Vi Dau So Tan Bien"',
            '  - "Tu Vi Thien Luong"',
            f"knowledge_type: {yaml_quote(KNOWLEDGE_TYPE)}",
            f"category: {yaml_quote(category)}",
            f"language: {yaml_quote(LANGUAGE)}",
            "---",
            "",
        ]
    )


def render_source_section(label: str, blocks: list[Block]) -> tuple[str, int]:
    lines = [f"## {label}", ""]
    if not blocks:
        lines += ["_Không có nội dung được phân loại chắc chắn vào mục này từ nguồn này._", ""]
        return "\n".join(lines) + "\n", 0
    toc_seen: set[str] = set()
    lines += ["### Mục lục nguồn", ""]
    for block in blocks:
        if block.title in toc_seen:
            continue
        toc_seen.add(block.title)
        indent = "  " * max(0, min(block.level, 4) - 1)
        lines.append(f"{indent}- {block.title}")
    lines.append("")
    payload = "".join(block.text for block in blocks)
    lines.append(normalize_headings(payload))
    return "\n".join(lines).rstrip() + "\n\n", len(payload)


def render_cross_source_notes(doc: OutputDoc) -> str:
    tanbien_count = len(doc.blocks_by_source.get("tanbien", []))
    thienluong_count = len(doc.blocks_by_source.get("thienluong", []))
    notes = [
        "## Cross-source notes",
        "",
        "- Ghi chú này chỉ mô tả cấu trúc phân loại, không thêm diễn giải tử vi mới.",
    ]
    if tanbien_count and thienluong_count:
        notes.append("- Mục này có nội dung từ cả hai nguồn; mỗi nguồn được giữ riêng theo tiêu đề nguồn.")
    elif tanbien_count:
        notes.append("- Mục này hiện chỉ có nội dung được phân loại từ Tu Vi Dau So Tan Bien.")
    elif thienluong_count:
        notes.append("- Mục này hiện chỉ có nội dung được phân loại từ Tu Vi Thien Luong.")
    else:
        notes.append("- Không có nội dung nguồn nào được phân loại vào mục này.")
    return "\n".join(notes) + "\n"


def render_doc(doc: OutputDoc) -> tuple[str, int]:
    content = make_frontmatter(doc.category)
    content += f"# {doc.title}\n\n{doc.description}\n\n"
    payload_chars = 0
    for source_key, source_label in (
        ("tanbien", "Tu Vi Dau So Tan Bien"),
        ("thienluong", "Tu Vi Thien Luong"),
    ):
        section, count = render_source_section(source_label, doc.blocks_by_source.get(source_key, []))
        content += section
        payload_chars += count
    content += render_cross_source_notes(doc)
    return content, payload_chars


def build_docs(books: list[SourceBook]) -> list[OutputDoc]:
    docs = [
        OutputDoc(
            filename=filename,
            category=category,
            title=title,
            description=description,
            blocks_by_source={"tanbien": [], "thienluong": []},
        )
        for filename, category, title, description in DOC_SPECS
    ]
    by_category = {doc.category: doc for doc in docs}
    for book in books:
        classify_blocks(book)
        for block in book.blocks:
            doc = by_category.get(block.category, by_category["unsorted"])
            doc.blocks_by_source.setdefault(book.key, []).append(block)
    return docs


def load_book(path: Path, key: str, label: str) -> SourceBook:
    raw = path.read_text(encoding="utf-8")
    cleaned = clean_source(raw)
    blocks = parse_blocks(cleaned, key, label)
    return SourceBook(key=key, label=label, path=path, cleaned_text=cleaned, blocks=blocks)


def prepare_output(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def detected_major_topics(books: list[SourceBook]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()
    for book in books:
        for block in book.blocks:
            if block.level <= 2 and block.title not in seen:
                seen.add(block.title)
                topics.append(f"{book.label}: {block.title}")
    return topics


def source_coverage_summary(books: list[SourceBook], docs: list[OutputDoc]) -> list[str]:
    lines: list[str] = []
    for book in books:
        total_blocks = len(book.blocks)
        total_chars = len(book.cleaned_text)
        unsorted_blocks = len(next(doc for doc in docs if doc.category == "unsorted").blocks_by_source.get(book.key, []))
        lines.append(
            f"{book.label}: {total_blocks} sections, {total_chars} chars after cleaning, {unsorted_blocks} unsorted sections."
        )
    return lines


def write_index(
    output_dir: Path,
    docs: list[OutputDoc],
    books: list[SourceBook],
    report: dict[str, str],
) -> None:
    content = make_frontmatter("index")
    content += "# Index hợp nhất\n\n"
    content += "## Generated file list\n\n"
    for doc in docs:
        total_blocks = sum(len(blocks) for blocks in doc.blocks_by_source.values())
        content += f"- [{doc.filename}]({doc.filename}) - {doc.description} Sections: {total_blocks}.\n"
    content += "\n## Upload order recommendation for Custom GPT Knowledge\n\n"
    content += "1. 00_index.md\n"
    for idx, doc in enumerate(docs, start=2):
        content += f"{idx}. {doc.filename}\n"
    content += "\n## Detected major topics\n\n"
    for topic in detected_major_topics(books):
        content += f"- {topic}\n"
    content += "\n## Notes on unsorted content\n\n"
    unsorted_doc = next(doc for doc in docs if doc.category == "unsorted")
    for source_key, label in (("tanbien", "Tu Vi Dau So Tan Bien"), ("thienluong", "Tu Vi Thien Luong")):
        blocks = unsorted_doc.blocks_by_source.get(source_key, [])
        chars = sum(len(block.text) for block in blocks)
        content += f"- {label}: {len(blocks)} sections, {chars} chars in `12_unsorted.md`.\n"
    content += "\n## Source coverage summary\n\n"
    for line in source_coverage_summary(books, docs):
        content += f"- {line}\n"
    content += "\n## Build report\n\n"
    for key, value in report.items():
        content += f"- {key}: `{value}`\n"
    (output_dir / INDEX_FILE).write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def build(tanbien: Path, thienluong: Path, output_dir: Path) -> int:
    if not tanbien.exists():
        raise FileNotFoundError(f"Missing Tan Bien input: {tanbien}")
    if not thienluong.exists():
        raise FileNotFoundError(f"Missing Thien Luong input: {thienluong}")

    books = [
        load_book(tanbien, "tanbien", "Tu Vi Dau So Tan Bien"),
        load_book(thienluong, "thienluong", "Tu Vi Thien Luong"),
    ]
    docs = build_docs(books)
    prepare_output(output_dir)

    total_output_chars = 0
    for doc in docs:
        rendered, payload_chars = render_doc(doc)
        total_output_chars += payload_chars
        (output_dir / doc.filename).write_text(rendered, encoding="utf-8", newline="\n")

    tanbien_chars = len(books[0].cleaned_text)
    thienluong_chars = len(books[1].cleaned_text)
    total_input_chars = tanbien_chars + thienluong_chars
    loss_percent = max(0.0, (total_input_chars - total_output_chars) / total_input_chars * 100) if total_input_chars else 0.0
    unsorted_doc = next(doc for doc in docs if doc.category == "unsorted")
    unsorted_chars = sum(len(block.text) for blocks in unsorted_doc.blocks_by_source.values() for block in blocks)
    warnings: list[str] = []
    if loss_percent > LOSS_WARN_PERCENT:
        warnings.append(f"Content loss exceeds {LOSS_WARN_PERCENT:.0f}% threshold.")
    if not (10 <= len(docs) + 1 <= 15):
        warnings.append(f"File count outside target 10-15: {len(docs) + 1}.")
    if unsorted_chars:
        warnings.append("Some content is in 12_unsorted.md for manual review.")

    report = {
        "Tan Bien input chars": str(tanbien_chars),
        "Thien Luong input chars": str(thienluong_chars),
        "Total input chars": str(total_input_chars),
        "Total output chars": str(total_output_chars),
        "Loss %": f"{loss_percent:.4f}",
        "Files created": str(len(docs) + 1),
        "Unsorted chars": str(unsorted_chars),
        "Warnings": "; ".join(warnings) if warnings else "None",
    }
    write_index(output_dir, docs, books, report)

    print(f"Tan Bien input chars: {tanbien_chars}")
    print(f"Thien Luong input chars: {thienluong_chars}")
    print(f"Total input chars: {total_input_chars}")
    print(f"Total output chars: {total_output_chars}")
    print(f"Loss %: {loss_percent:.4f}")
    print(f"Files created: {len(docs) + 1}")
    print(f"Unsorted chars: {unsorted_chars}")
    print(f"Warnings: {report['Warnings']}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge two Tu Vi Markdown books into a Custom GPT knowledge pack.")
    parser.add_argument("--tanbien", required=True, type=Path, help="Tu Vi Dau So Tan Bien cleaned Markdown.")
    parser.add_argument("--thienluong", required=True, type=Path, help="Tu Vi Thien Luong cleaned Markdown.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return build(args.tanbien, args.thienluong, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
