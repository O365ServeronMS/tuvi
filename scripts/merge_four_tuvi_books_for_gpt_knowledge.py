#!/usr/bin/env python3
"""Merge four cleaned Tu Vi books into a Custom GPT knowledge pack.

The script keeps every source separate under source headings, groups sections by
topic with conservative keyword heuristics, and writes large Markdown files that
can be uploaded manually to ChatGPT Custom GPT Knowledge.
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

SOURCE_ORDER = (
    ("tanbien", "Tu Vi Dau So Tan Bien"),
    ("thienluong", "Tu Vi Thien Luong"),
    ("trandoan", "Tu Vi Dau So Toan Thu Tran Doan"),
    ("nguyenphatloc", "Tu Vi Tong Hop Nguyen Phat Loc"),
)

DOC_SPECS = [
    (
        "01_general_theory_and_foundations.md",
        "general_theory_and_foundations",
        "Ly thuyet tong quan va nen tang",
        "Nen tang am duong, ngu hanh, can chi, dinh nghia, loi gioi thieu va cac phan ly thuyet tong quat.",
    ),
    (
        "02_chart_setup_an_sao_and_core_rules.md",
        "chart_setup_an_sao_and_core_rules",
        "Lap la so, an sao va quy tac cot loi",
        "Lap thanh, dinh cung, an Menh, an Than, lap Cuc, an sao, mieu vuong dac ham va cac quy tac lap la so.",
    ),
    (
        "03_major_stars.md",
        "major_stars",
        "Chinh tinh",
        "Cac muc lien quan den 14 chinh tinh va y nghia cua tung sao.",
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
        "Cac cung",
        "Cac muc ve Menh, Than va muoi hai cung trong la so.",
    ),
    (
        "06_star_combinations_and_cach_cuc.md",
        "star_combinations_and_cach_cuc",
        "To hop sao va cach cuc",
        "Cach cuc, bo sao, hoi hop, dong cung, giap cung, xung chieu va vo chinh dieu.",
    ),
    (
        "07_four_transformations_and_cycles.md",
        "four_transformations_and_cycles",
        "Tu Hoa va cac vong sao",
        "Tu Hoa, Loc Ton, Thai Tue, Trang Sinh va cac chu ky can chi, ngu hanh.",
    ),
    (
        "08_life_periods_fortune_and_limitation.md",
        "life_periods_fortune_and_limitation",
        "Van han",
        "Dai han, tieu han, luu nien, van han va gioi han luan doan.",
    ),
    (
        "09_tran_doan_quan_thu_classical_rules.md",
        "tran_doan_toan_thu_classical_rules",
        "Tran Doan va Toan Thu",
        "Noi dung rieng cua Tu Vi Dau So Toan Thu, quan thu, phu chu va quy tac co dien.",
    ),
    (
        "10_tan_bien_method.md",
        "tan_bien_method",
        "Phuong phap Tan Bien",
        "Noi dung rieng cua Tu Vi Dau So Tan Bien ve phuong phap, cau truc sach va cach trien khai.",
    ),
    (
        "11_thien_luong_method.md",
        "thien_luong_method",
        "Phuong phap Thien Luong",
        "Noi dung nghiem ly, tam hop tuoi, nhan sinh va phuong phap dac thu cua Thien Luong.",
    ),
    (
        "12_nguyen_phat_loc_synthesis_method.md",
        "nguyen_phat_loc_synthesis_method",
        "Phuong phap tong hop Nguyen Phat Loc",
        "Noi dung tong hop, Tu Vi Ham So, biet so sua so va cach trien khai cua Nguyen Phat Loc.",
    ),
    (
        "13_classical_verses_phu_doan_and_cautions.md",
        "classical_verses_phu_doan_and_cautions",
        "Phu doan, phu quyet va can trong",
        "Phu, quyet, tho van, loi can trong, phe binh va cac ghi chu tranh lap luan qua muc.",
    ),
    (
        "14_case_studies_and_examples.md",
        "case_studies_and_examples",
        "La so, vi du va nghiem chung",
        "Phu luc, la so mau, vi du, truong hop nghiem ly va cac doan ung dung.",
    ),
    (
        "15_cross_source_comparison_notes.md",
        "cross_source_comparison_notes",
        "Ghi chu doi chieu cau truc",
        "Ghi chu trung lap va do phu theo nguon; chi mo ta cau truc, khong them dien giai tu vi moi.",
    ),
    (
        "16_unsorted.md",
        "unsorted",
        "Chua phan loai",
        "Noi dung khong du tin hieu de phan loai chac chan.",
    ),
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*-?\s*\d{1,4}\s*-?\s*$")


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
class SourceBook:
    key: str
    label: str
    path: Path
    raw_chars: int
    cleaned_text: str
    blocks: list[Block]


@dataclasses.dataclass
class OutputDoc:
    filename: str
    category: str
    title: str
    description: str
    blocks_by_source: dict[str, list[Block]]
    generated_notes: str = ""


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
    """Remove repeated page furniture while keeping book content intact."""
    text = remove_frontmatter(text).replace("\ufeff", "")
    cleaned_lines: list[str] = []
    previous_nonblank = ""
    repeated_headers = {
        "tu vi nghiem ly toan thu thien luong",
        "tu vi nghiem ly toan thu",
        "tu vi tong hop nguyen phat loc",
        "tu vi dau so tan bien",
        "tu vi dau so toan thu",
    }
    website_noise = {"dantocking com"}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        normalized = norm(stripped)
        if stripped and PAGE_NUMBER_RE.match(stripped) and previous_nonblank:
            continue
        if normalized in repeated_headers and previous_nonblank:
            continue
        if normalized in website_noise:
            continue
        cleaned_lines.append(line)
        if stripped:
            previous_nonblank = stripped
    cleaned = "\n".join(cleaned_lines).strip() + "\n"
    return re.sub(r"\n{4,}", "\n\n\n", cleaned)


def parse_blocks(text: str, source_key: str, source_label: str) -> list[Block]:
    """Split on every Markdown heading, preserving consecutive heading lines."""
    lines = text.splitlines()
    headings: list[tuple[int, int, str, tuple[str, ...]]] = []
    stack: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        stack = [(old_level, old_title) for old_level, old_title in stack if old_level < level]
        stack.append((level, title))
        headings.append((idx, level, title, tuple(item_title for _, item_title in stack)))

    blocks: list[Block] = []
    order = 1
    if not headings:
        return [
            Block(
                order=1,
                source_key=source_key,
                source_label=source_label,
                level=1,
                title="Mở đầu",
                path=("Mở đầu",),
                text=text.strip() + "\n",
            )
        ]

    first_idx = headings[0][0]
    if first_idx > 0:
        chunk = "\n".join(lines[:first_idx]).strip()
        if chunk:
            blocks.append(
                Block(order, source_key, source_label, 1, "Mở đầu", ("Mở đầu",), chunk + "\n")
            )
            order += 1

    for pos, (start, level, title, path) in enumerate(headings):
        end = headings[pos + 1][0] if pos + 1 < len(headings) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()
        if not chunk:
            continue
        blocks.append(
            Block(
                order=order,
                source_key=source_key,
                source_label=source_label,
                level=level,
                title=title,
                path=path,
                text=chunk + "\n",
            )
        )
        order += 1
    return blocks


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
    "loc ton",
    "thien ma",
    "hoa loc",
    "hoa quyen",
    "hoa khoa",
    "hoa ky",
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
    "thai tue",
    "trang sinh",
    "dao hoa",
    "hong loan",
    "thien hy",
    "long tri",
    "phuong cac",
    "tam thai",
    "bat toa",
    "thien quan",
    "thien phuc",
    "co than",
    "qua tu",
    "thien khong",
    "kiep sat",
    "hoa cai",
    "phuc binh",
    "quan phu",
    "bach ho",
    "tang mon",
    "dieu khach",
    "benh phu",
    "thien duc",
    "nguyet duc",
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
    "cuc",
    "menh cuc",
    "mieu",
    "vuong",
    "dac dia",
    "ham dia",
    "tam hop",
    "xung chieu",
    "nhi hop",
    "giap cung",
}

THEORY_TERMS = {
    "loi noi dau",
    "loi gioi thieu",
    "dan",
    "nguyen ly",
    "khoa tu vi",
    "am duong",
    "ngu hanh",
    "can chi",
    "nap am",
    "60 hoa giap",
    "ban menh",
    "nhan van",
    "dinh nghia",
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
    "vong thai tue",
    "vong loc ton",
    "vong trang sinh",
}

FORTUNE_TERMS = {
    "dai han",
    "tieu han",
    "luu nien",
    "luu dai han",
    "luu nguyet",
    "luu nhat",
    "van han",
    "han chet",
    "dam tang",
    "khoi han",
    "nhap han",
}

COMBO_TERMS = {
    "cach",
    "cach cuc",
    "bo sao",
    "dong cung",
    "hoi hop",
    "tam hop",
    "xung chieu",
    "nhi hop",
    "giap cung",
    "vo chinh dieu",
    "toa thu",
    "lien chau",
    "phan cuc",
    "thuong cach",
    "trung cach",
    "ha cach",
}

VERSE_CAUTION_TERMS = {
    "phu",
    "phu doan",
    "phu quyet",
    "thai vi phu",
    "hoang kim phu",
    "thi",
    "tho",
    "quyet",
    "ca",
    "can trong",
    "phe binh",
    "khong chu truong",
    "sach da dan",
}

CASE_TERMS = {
    "phu luc",
    "la so",
    "la so thu",
    "vi du",
    "truong hop",
    "nghiem chung",
}

TAN_BIEN_TERMS = {"tan bien", "van dang thai thu lang"}
THIEN_LUONG_TERMS = {"thien luong", "nghiem ly", "tam hop tuoi", "cu thien luong"}
TRAN_DOAN_TERMS = {"tran doan", "toan thu", "hi di", "vu tai luc", "quan thu"}
NGUYEN_PHAT_LOC_TERMS = {
    "nguyen phat loc",
    "tu vi tong hop",
    "tu vi ham so",
    "biet so sua so",
    "biet minh sua minh",
    "phuong phap tong hop",
}


def classify_block(block: Block) -> str:
    title = norm(block.title)
    path_text = norm(" ".join(block.path))
    sample = norm(block.text[:2500])
    combined = f"{path_text} {sample}"

    if block.source_key == "trandoan" and (
        has_any(combined, TRAN_DOAN_TERMS) or block.order <= 40
    ):
        return "tran_doan_toan_thu_classical_rules"
    if block.source_key == "tanbien" and (has_any(combined, TAN_BIEN_TERMS) or block.order <= 12):
        return "tan_bien_method"
    if block.source_key == "thienluong" and (has_any(combined, THIEN_LUONG_TERMS) or block.order <= 20):
        return "thien_luong_method"
    if block.source_key == "nguyenphatloc" and (
        has_any(combined, NGUYEN_PHAT_LOC_TERMS) or block.order <= 25
    ):
        return "nguyen_phat_loc_synthesis_method"

    # Case-study routing must be title/path driven. Terms like "la so" occur
    # throughout theory prose and would otherwise swallow whole topical chapters.
    if has_any(f"{path_text} {title}", CASE_TERMS):
        return "case_studies_and_examples"
    if has_any(combined, VERSE_CAUTION_TERMS) and block.source_key == "trandoan":
        return "classical_verses_phu_doan_and_cautions"
    if has_any(title, MAJOR_STARS):
        return "major_stars"
    if has_any(title, AUXILIARY_TERMS):
        return "auxiliary_stars"
    if has_any(title, PALACE_TERMS) and ("cung" in title or title in PALACE_TERMS):
        return "palaces"
    if has_any(combined, FORTUNE_TERMS):
        return "life_periods_fortune_and_limitation"
    if has_any(combined, CYCLE_TERMS):
        return "four_transformations_and_cycles"
    if has_any(combined, CORE_RULE_TERMS):
        return "chart_setup_an_sao_and_core_rules"
    if has_any(combined, COMBO_TERMS):
        return "star_combinations_and_cach_cuc"
    if has_any(combined, VERSE_CAUTION_TERMS):
        return "classical_verses_phu_doan_and_cautions"
    if has_any(combined, THEORY_TERMS):
        return "general_theory_and_foundations"
    return "unsorted"


def load_book(path: Path, key: str, label: str) -> SourceBook:
    raw = path.read_text(encoding="utf-8")
    cleaned = clean_source(raw)
    blocks = parse_blocks(cleaned, key, label)
    book = SourceBook(key, label, path, len(raw), cleaned, blocks)
    for block in book.blocks:
        block.category = classify_block(block)
    return book


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
    lines = [
        "---",
        f"knowledge_pack: {yaml_quote(PACK_NAME)}",
        "source_books:",
    ]
    for _, label in SOURCE_ORDER:
        lines.append(f"  - {yaml_quote(label)}")
    lines += [
        f"knowledge_type: {yaml_quote(KNOWLEDGE_TYPE)}",
        f"category: {yaml_quote(category)}",
        f"language: {yaml_quote(LANGUAGE)}",
        "---",
        "",
    ]
    return "\n".join(lines)


def anchor_for(text: str) -> str:
    base = norm(text).replace(" ", "-")
    return base or "section"


def render_toc(doc: OutputDoc) -> str:
    lines = ["## Mục lục", ""]
    for source_key, label in SOURCE_ORDER:
        blocks = doc.blocks_by_source.get(source_key, [])
        if not blocks:
            continue
        lines.append(f"- [{label}](#{anchor_for(label)})")
        for block in blocks[:80]:
            lines.append(f"  - {block.title}")
        if len(blocks) > 80:
            lines.append(f"  - ... {len(blocks) - 80} mục khác")
    if doc.generated_notes:
        lines.append("- [Cross-source structural notes](#cross-source-structural-notes)")
    lines.append("")
    return "\n".join(lines)


def render_source_section(label: str, blocks: list[Block]) -> tuple[str, int]:
    lines = [f"## {label}", ""]
    if not blocks:
        lines.append("_Không có nội dung được phân loại chắc chắn vào mục này từ nguồn này._")
        lines.append("")
        return "\n".join(lines), 0
    lines.append("### Mục lục nguồn")
    lines.append("")
    for block in blocks[:120]:
        lines.append(f"- {block.title}")
    if len(blocks) > 120:
        lines.append(f"- ... {len(blocks) - 120} mục khác")
    lines.append("")
    payload = "".join(block.text for block in blocks)
    lines.append(normalize_headings(payload).rstrip())
    lines.append("")
    return "\n".join(lines), len(payload)


def render_doc(doc: OutputDoc) -> tuple[str, int]:
    content = make_frontmatter(doc.category)
    content += f"# {doc.title}\n\n{doc.description}\n\n"
    content += render_toc(doc)
    payload_chars = 0
    for source_key, label in SOURCE_ORDER:
        section, count = render_source_section(label, doc.blocks_by_source.get(source_key, []))
        content += section
        payload_chars += count
    if doc.generated_notes:
        content += "## Cross-source structural notes\n\n"
        content += doc.generated_notes.rstrip() + "\n"
    return content.rstrip() + "\n", payload_chars


def build_docs(books: list[SourceBook]) -> list[OutputDoc]:
    docs = [
        OutputDoc(
            filename,
            category,
            title,
            description,
            {source_key: [] for source_key, _ in SOURCE_ORDER},
        )
        for filename, category, title, description in DOC_SPECS
    ]
    by_category = {doc.category: doc for doc in docs}
    for book in books:
        for block in book.blocks:
            by_category.get(block.category, by_category["unsorted"]).blocks_by_source[book.key].append(block)

    comparison = by_category["cross_source_comparison_notes"]
    comparison.generated_notes = make_comparison_notes(docs)
    return docs


def make_comparison_notes(docs: list[OutputDoc]) -> str:
    lines = [
        "- Các ghi chú dưới đây chỉ mô tả cấu trúc phân bổ nội dung giữa nguồn sách.",
        "- Không có diễn giải tử vi mới, không hòa giải các khác biệt giáo lý giữa nguồn.",
        "",
        "| Category | Tan Bien | Thien Luong | Tran Doan | Nguyen Phat Loc |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for doc in docs:
        if doc.category in {"cross_source_comparison_notes", "unsorted"}:
            continue
        counts = [
            sum(len(block.text) for block in doc.blocks_by_source.get(source_key, []))
            for source_key, _ in SOURCE_ORDER
        ]
        lines.append(
            f"| {doc.title} | {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} |"
        )
    return "\n".join(lines) + "\n"


def prepare_output(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def dominant_source_warnings(docs: list[OutputDoc]) -> list[str]:
    warnings: list[str] = []
    for doc in docs:
        if doc.category in {"cross_source_comparison_notes", "unsorted"}:
            continue
        counts = {
            label: sum(len(block.text) for block in doc.blocks_by_source.get(source_key, []))
            for source_key, label in SOURCE_ORDER
        }
        total = sum(counts.values())
        if total < 10000:
            continue
        label, count = max(counts.items(), key=lambda item: item[1])
        if count / total >= 0.75:
            warnings.append(f"{doc.filename} dominated by {label} ({count}/{total} chars).")
    return warnings


def detected_major_topics(books: list[SourceBook]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()
    for book in books:
        for block in book.blocks:
            if block.level <= 2:
                item = f"{book.label}: {block.title}"
                if item not in seen:
                    topics.append(item)
                    seen.add(item)
            if len(topics) >= 250:
                return topics
    return topics


def source_coverage_by_category(docs: list[OutputDoc]) -> str:
    lines = [
        "| File | Category | Tan Bien | Thien Luong | Tran Doan | Nguyen Phat Loc |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for doc in docs:
        counts = [
            sum(len(block.text) for block in doc.blocks_by_source.get(source_key, []))
            for source_key, _ in SOURCE_ORDER
        ]
        lines.append(
            f"| {doc.filename} | {doc.category} | {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} |"
        )
    return "\n".join(lines) + "\n"


def write_index(
    output_dir: Path,
    docs: list[OutputDoc],
    books: list[SourceBook],
    report: dict[str, str],
    warnings: list[str],
) -> None:
    content = make_frontmatter("index")
    content += "# Index hợp nhất\n\n"
    content += "## Generated file list\n\n"
    content += "- [00_index.md](00_index.md) - Index, coverage report, upload order, warnings and Custom GPT instruction summary.\n"
    for doc in docs:
        total_blocks = sum(len(blocks) for blocks in doc.blocks_by_source.values())
        content += f"- [{doc.filename}]({doc.filename}) - {doc.description} Sections: {total_blocks}.\n"

    content += "\n## Recommended upload order for ChatGPT Custom GPT Knowledge\n\n"
    content += "1. 00_index.md\n"
    for idx, doc in enumerate(docs, start=2):
        content += f"{idx}. {doc.filename}\n"

    content += "\n## Detected major topics\n\n"
    for topic in detected_major_topics(books):
        content += f"- {topic}\n"

    content += "\n## Detected source coverage by category\n\n"
    content += source_coverage_by_category(docs)

    content += "\n## Notes on unsorted content\n\n"
    unsorted_doc = next(doc for doc in docs if doc.category == "unsorted")
    for source_key, label in SOURCE_ORDER:
        blocks = unsorted_doc.blocks_by_source.get(source_key, [])
        chars = sum(len(block.text) for block in blocks)
        content += f"- {label}: {len(blocks)} sections, {chars} chars in `16_unsorted.md`.\n"

    content += "\n## Source coverage summary\n\n"
    for book in books:
        content += f"- {book.label}: {len(book.blocks)} sections, {len(book.cleaned_text)} cleaned chars.\n"

    content += "\n## Dominant-source warnings\n\n"
    if warnings:
        for warning in warnings:
            content += f"- {warning}\n"
    else:
        content += "- None.\n"

    content += "\n## Suggested Custom GPT instruction summary\n\n"
    content += (
        "Use this knowledge pack as a source-preserving Tu Vi reference. When answering, cite which source section is being used, "
        "keep book opinions separate when they differ, do not invent new interpretations, and prefer `00_index.md` to locate the relevant topic file before consulting detailed sections.\n"
    )

    content += "\n## Build report\n\n"
    for key, value in report.items():
        content += f"- {key}: `{value}`\n"

    (output_dir / "00_index.md").write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def build(
    tanbien: Path,
    thienluong: Path,
    trandoan: Path,
    nguyenphatloc: Path,
    output_dir: Path,
) -> int:
    input_paths = {
        "tanbien": tanbien,
        "thienluong": thienluong,
        "trandoan": trandoan,
        "nguyenphatloc": nguyenphatloc,
    }
    for key, path in input_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {key} input: {path}")

    books = [
        load_book(tanbien, "tanbien", "Tu Vi Dau So Tan Bien"),
        load_book(thienluong, "thienluong", "Tu Vi Thien Luong"),
        load_book(trandoan, "trandoan", "Tu Vi Dau So Toan Thu Tran Doan"),
        load_book(nguyenphatloc, "nguyenphatloc", "Tu Vi Tong Hop Nguyen Phat Loc"),
    ]
    docs = build_docs(books)
    prepare_output(output_dir)

    total_output_payload_chars = 0
    for doc in docs:
        rendered, payload_chars = render_doc(doc)
        total_output_payload_chars += payload_chars
        (output_dir / doc.filename).write_text(rendered, encoding="utf-8", newline="\n")

    total_input_chars = sum(len(book.cleaned_text) for book in books)
    loss_percent = (
        max(0.0, (total_input_chars - total_output_payload_chars) / total_input_chars * 100)
        if total_input_chars
        else 0.0
    )
    unsorted_doc = next(doc for doc in docs if doc.category == "unsorted")
    unsorted_chars = sum(
        len(block.text) for blocks in unsorted_doc.blocks_by_source.values() for block in blocks
    )
    warnings = dominant_source_warnings(docs)
    if loss_percent > LOSS_WARN_PERCENT:
        warnings.append(f"Content loss exceeds {LOSS_WARN_PERCENT:.0f}% threshold.")
    if not (12 <= len(docs) + 1 <= 18):
        warnings.append(f"File count outside target 12-18: {len(docs) + 1}.")
    if unsorted_chars:
        warnings.append("Some content is in 16_unsorted.md for manual review.")

    report = {
        "Tan Bien input chars": str(len(books[0].cleaned_text)),
        "Thien Luong input chars": str(len(books[1].cleaned_text)),
        "Tran Doan input chars": str(len(books[2].cleaned_text)),
        "Nguyen Phat Loc input chars": str(len(books[3].cleaned_text)),
        "Total input chars": str(total_input_chars),
        "Total output chars": str(total_output_payload_chars),
        "Loss %": f"{loss_percent:.4f}",
        "Files created": str(len(docs) + 1),
        "Unsorted chars": str(unsorted_chars),
        "Warnings": "; ".join(warnings) if warnings else "None",
    }
    write_index(output_dir, docs, books, report, warnings)

    print(f"Tan Bien input chars: {report['Tan Bien input chars']}")
    print(f"Thien Luong input chars: {report['Thien Luong input chars']}")
    print(f"Tran Doan input chars: {report['Tran Doan input chars']}")
    print(f"Nguyen Phat Loc input chars: {report['Nguyen Phat Loc input chars']}")
    print(f"Total input chars: {report['Total input chars']}")
    print(f"Total output chars: {report['Total output chars']}")
    print(f"Loss %: {report['Loss %']}")
    print(f"Files created: {report['Files created']}")
    print(f"Unsorted chars: {report['Unsorted chars']}")
    print(f"Warnings: {report['Warnings']}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge four cleaned Tu Vi Markdown books into a Custom GPT knowledge pack."
    )
    parser.add_argument("--tanbien", required=True, type=Path, help="Tu Vi Dau So Tan Bien cleaned Markdown.")
    parser.add_argument("--thienluong", required=True, type=Path, help="Tu Vi Thien Luong cleaned Markdown.")
    parser.add_argument("--trandoan", required=True, type=Path, help="Tu Vi Dau So Toan Thu Tran Doan cleaned Markdown.")
    parser.add_argument("--nguyenphatloc", required=True, type=Path, help="Tu Vi Tong Hop Nguyen Phat Loc cleaned Markdown.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return build(
            args.tanbien,
            args.thienluong,
            args.trandoan,
            args.nguyenphatloc,
            args.output,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
