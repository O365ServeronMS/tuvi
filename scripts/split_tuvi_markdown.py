#!/usr/bin/env python3
"""Split Tu Vi Dau So Tan Bien Markdown into AI knowledge-base files.

The splitter is intentionally conservative:
- source content is copied in source order into exactly one content file;
- generated YAML frontmatter and _index.md are excluded from preservation loss;
- only recurring page furniture and narrow OCR spacing defects are cleaned.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Iterable


CATEGORIES = (
    "stars",
    "auxiliary-stars",
    "palaces",
    "techniques",
    "combos",
    "unsorted",
)

MIN_FILE_CHARS = 5_000
MAX_FILE_CHARS = 80_000
TARGET_FILE_CHARS = 3_000
MAX_BLOCK_CHARS = 3_400
MIN_OUTPUT_FILES = 100
MIN_PAYLOAD_CHARS = 4_200
WARN_LOSS_PERCENT = 2.0

PAGE_FOOTER_RE = re.compile(r"^\s*-?\s*\d{1,4}\s*-?\s*$")
RUNNING_HEADER_RE = re.compile(
    r"^\s*(Vân Đằng Thái Thứ Lang|Tử Vi đẩu số tân biên)\s*$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SECTION_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.\s*")

PALACE_NAMES = {
    "mệnh",
    "mệnh viên",
    "thân",
    "phụ mẫu",
    "phúc đức",
    "điền trạch",
    "quan lộc",
    "nô bộc",
    "thiên di",
    "tật ách",
    "tài bạch",
    "tử tức",
    "thê thiếp",
    "phu quân",
    "phu thê",
    "huynh đệ",
}

PRIMARY_STARS = {
    "tử vi",
    "liêm trinh",
    "thiên đồng",
    "vũ khúc",
    "thái dương",
    "thiên cơ",
    "thiên phủ",
    "thái âm",
    "tham lang",
    "cự môn",
    "thiên tướng",
    "thiên lương",
    "thất sát",
    "phá quân",
}

AUXILIARY_STARS = {
    "kình dương",
    "đà la",
    "địa kiếp",
    "địa không",
    "hỏa tinh",
    "linh tinh",
    "tả phụ",
    "hữu bật",
    "văn xương",
    "văn khúc",
    "long trì",
    "phượng các",
    "thiên khôi",
    "thiên việt",
    "thiên khốc",
    "thiên hư",
    "tam thai",
    "bát tọa",
    "ân quang",
    "thiên quý",
    "thiên đức",
    "nguyệt đức",
    "thiên hình",
    "thiên riêu",
    "thiên y",
    "hồng loan",
    "thiên hỷ",
    "quốc ấn",
    "đường phù",
    "thiên giải",
    "địa giải",
    "giải thần",
    "thai phụ",
    "phong cáo",
    "thiên tài",
    "thiên thọ",
    "thiên thương",
    "thiên sứ",
    "thiên la",
    "địa võng",
    "hóa lộc",
    "hóa quyền",
    "hóa khoa",
    "hóa kỵ",
    "thiên quan",
    "thiên phúc",
    "cô thần",
    "quả tú",
    "đào hoa",
    "thiên mã",
    "kiếp sát",
    "phá toái",
    "hoa cái",
    "lưu hà",
    "thiên trù",
    "lưu niên văn tinh",
    "bác sỹ",
    "đẩu quân",
    "thiên không",
    "tuần",
    "triệt",
    "thái tuế",
    "thiếu dương",
    "thiếu âm",
    "quan phù",
    "tử phù",
    "trực phù",
    "tuế phá",
    "long đức",
    "phúc đức",
    "điếu khách",
    "lộc tồn",
    "tràng sinh",
    "mộc dục",
    "quan đới",
    "lâm quan",
    "đế vượng",
    "suy",
    "bệnh",
    "mộ",
    "tuyệt",
    "thai",
    "dưỡng",
    "đại hao",
    "tiểu hao",
    "tang môn",
    "bạch hổ",
    "lực sỹ",
    "thanh long",
    "tướng quân",
    "tấu thư",
    "phi liêm",
    "hỷ thần",
    "bệnh phù",
    "phục binh",
}

TECHNIQUE_TERMS = {
    "an sao",
    "định cung",
    "tìm bản mệnh",
    "phân âm dương",
    "định giờ",
    "an mệnh",
    "an thân",
    "lập cục",
    "định hướng chiếu",
    "tam chiếu",
    "xung chiếu",
    "nhị hợp",
    "khởi hạn",
    "đại hạn",
    "lưu đại hạn",
    "tiểu hạn",
    "lưu niên",
    "lưu nguyệt",
    "lưu nhật",
    "lưu thời",
    "ngũ hành",
    "thập can",
    "thập nhị chi",
    "luận đoán vận hạn",
    "phương pháp",
    "nhận định về hạn",
    "bản mệnh",
    "phân cục",
}

COMBO_TERMS = {
    "đồng cung",
    "hội hợp",
    "tọa thủ",
    "xung chiếu",
    "giáp cung",
    "vô chính diệu",
    "cách",
    "cục",
    "sát tinh",
    "khoa",
    "quyền",
    "lộc",
    "kỵ",
    "lộc mã",
    "không kiếp",
    "tuần",
    "triệt",
}

OBVIOUS_OCR_REPLACEMENTS = {
    "Qúy": "Quý",
    "qúy": "quý",
    "Qủa": "Quả",
    "qủa": "quả",
    "Lồc": "Lộc",
    "NhũNg": "Những",
    "NHŨNG": "NHỮNG",
    "B ạch": "Bạch",
    "Tài B ạch": "Tài Bạch",
    "H ữu": "Hữu",
    "Thái Tu ế": "Thái Tuế",
    "Ph ủ": "Phủ",
    "đ ếm": "đếm",
    "b ỏ": "bỏ",
}


@dataclasses.dataclass
class Block:
    order: int
    heading: str
    heading_path: tuple[str, ...]
    text: str
    category: str


@dataclasses.dataclass
class OutputFile:
    order: int
    category: str
    title: str
    path: Path
    blocks: list[Block]
    payload: str


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def normalize_key(text: str) -> str:
    text = text.lower().replace("đ", "d")
    text = strip_accents(text)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clean_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    lines: list[str] = []
    previous_nonblank = ""

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if RUNNING_HEADER_RE.match(stripped):
            continue
        if PAGE_FOOTER_RE.match(stripped) and previous_nonblank:
            continue
        for src, dst in OBVIOUS_OCR_REPLACEMENTS.items():
            line = line.replace(src, dst)
        lines.append(line)
        if stripped:
            previous_nonblank = stripped

    cleaned = "\n".join(lines).strip() + "\n"
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned


def remove_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :]


def parse_blocks(text: str) -> list[Block]:
    lines = text.splitlines()
    heading_stack: list[tuple[int, str]] = []
    blocks: list[Block] = []
    current_start = 0
    current_heading = "Tử Vi Đẩu Số Tân Biên"
    current_path: tuple[str, ...] = (current_heading,)
    order = 1

    def emit(end: int) -> None:
        nonlocal order
        chunk = "\n".join(lines[current_start:end]).strip()
        if not chunk:
            return
        blocks.append(
            Block(
                order=order,
                heading=current_heading,
                heading_path=current_path,
                text=chunk + "\n",
                category="unsorted",
            )
        )
        order += 1

    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        if idx > current_start:
            emit(idx)
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_stack = [(lvl, text) for lvl, text in heading_stack if lvl < level]
        heading_stack.append((level, title))
        current_start = idx
        current_heading = title
        current_path = tuple(text for _, text in heading_stack)

    emit(len(lines))
    return split_large_blocks(blocks)


def split_large_blocks(blocks: list[Block]) -> list[Block]:
    """Split oversized heading blocks at blank-line paragraph boundaries.

    This does not add continuation headings to payload content. The first part
    keeps the original Markdown heading; following parts keep only their source
    paragraphs while retaining heading metadata in frontmatter.
    """

    split_blocks: list[Block] = []
    next_order = 1
    for block in blocks:
        if len(block.text) <= MAX_BLOCK_CHARS:
            block.order = next_order
            split_blocks.append(block)
            next_order += 1
            continue

        paragraphs = re.split(r"(\n\s*\n)", block.text)
        parts: list[str] = []
        current = ""
        for piece in paragraphs:
            if not piece:
                continue
            if len(piece) > TARGET_FILE_CHARS:
                if current.strip():
                    parts.append(current.strip() + "\n")
                    current = ""
                parts.extend(split_long_piece(piece))
                continue
            if current and len(current) + len(piece) > TARGET_FILE_CHARS:
                parts.append(current.strip() + "\n")
                current = ""
            current += piece
        if current.strip():
            parts.append(current.strip() + "\n")

        for part in parts:
            split_blocks.append(
                Block(
                    order=next_order,
                    heading=block.heading,
                    heading_path=block.heading_path,
                    text=part,
                    category=block.category,
                )
            )
            next_order += 1
    return split_blocks


def split_long_piece(piece: str) -> list[str]:
    parts: list[str] = []
    current = ""
    lines = piece.splitlines(keepends=True)
    if len(lines) <= 1:
        return split_long_line(piece)
    for line in lines:
        if len(line) > TARGET_FILE_CHARS:
            if current.strip():
                parts.append(current.strip() + "\n")
                current = ""
            parts.extend(split_long_line(line))
            continue
        if current and len(current) + len(line) > TARGET_FILE_CHARS:
            parts.append(current.strip() + "\n")
            current = ""
        current += line
    if current.strip():
        parts.append(current.strip() + "\n")
    return parts


def split_long_line(line: str) -> list[str]:
    parts: list[str] = []
    words = line.split(" ")
    current = ""
    for word in words:
        addition = word if not current else " " + word
        if current and len(current) + len(addition) > TARGET_FILE_CHARS:
            parts.append(current.strip() + "\n")
            current = word
        else:
            current += addition
    if current.strip():
        parts.append(current.strip() + "\n")
    return parts


def clean_heading_for_match(heading: str) -> str:
    heading = SECTION_NUMBER_RE.sub("", heading).strip()
    heading = re.sub(r"\([^)]*\)", "", heading).strip()
    return normalize_for_match(heading)


def contains_any(haystack: str, needles: Iterable[str]) -> bool:
    return any(needle in haystack for needle in needles)


def classify_block(block: Block) -> str:
    path_text = " / ".join(block.heading_path)
    heading = clean_heading_for_match(block.heading)
    match_text = normalize_for_match(path_text + "\n" + block.text[:1200])

    if block.order <= 10 and (
        "lời nói đầu" in match_text
        or "sài gòn" in match_text
        or "vân đằng" in match_text
        or "tử vi đẩu số tân biên" in match_text
    ):
        return "unsorted"

    in_lap_thanh = "phần 1" in match_text or "lập thành" in match_text
    in_star_characteristics = "đặc tính các sao" in match_text
    in_palace_part = "luận đoán 12 cung" in match_text
    in_han_part = "vận hạn" in match_text

    if contains_any(match_text, PALACE_NAMES) and (
        in_palace_part or heading in PALACE_NAMES or "cung " in heading
    ):
        return "palaces"

    primary_hits = [star for star in PRIMARY_STARS if star in heading]
    auxiliary_hits = [star for star in AUXILIARY_STARS if star in heading]

    if primary_hits and (in_star_characteristics or len(primary_hits) == 1):
        return "stars"
    if auxiliary_hits and (in_lap_thanh or in_star_characteristics or heading.startswith("sao ") or "bộ sao" in heading):
        return "auxiliary-stars"

    if contains_any(heading, COMBO_TERMS) and not in_lap_thanh:
        return "combos"
    if contains_any(match_text, TECHNIQUE_TERMS) or in_han_part or in_lap_thanh:
        return "techniques"

    if len(primary_hits) + len(auxiliary_hits) >= 2:
        return "combos"
    if auxiliary_hits:
        return "auxiliary-stars"
    if primary_hits:
        return "stars"

    return "unsorted"


def categorize_blocks(blocks: list[Block]) -> None:
    for block in blocks:
        block.category = classify_block(block)


def pack_blocks(blocks: list[Block]) -> list[list[Block]]:
    packs: list[list[Block]] = []
    current: list[Block] = []
    current_size = 0

    for block in blocks:
        size = len(block.text)
        must_split = current and current_size + size > MAX_FILE_CHARS
        target_split = current and current_size >= TARGET_FILE_CHARS
        if must_split or target_split:
            packs.append(current)
            current = []
            current_size = 0
        current.append(block)
        current_size += size

    if current:
        packs.append(current)

    # Merge only very small packs. YAML frontmatter adds useful metadata, so a
    # 4KB payload generally becomes a target-sized Markdown file on disk.
    merged: list[list[Block]] = []
    for pack in packs:
        pack_size = sum(len(block.text) for block in pack)
        if merged and pack_size < 1_500:
            previous_size = sum(len(block.text) for block in merged[-1])
            if previous_size + pack_size <= MAX_FILE_CHARS:
                merged[-1].extend(pack)
                continue
        merged.append(pack)
    return merged


def build_output_files(blocks: list[Block], output_dir: Path) -> list[OutputFile]:
    entries: list[tuple[str, list[Block]]] = []
    for category in CATEGORIES:
        category_blocks = [block for block in blocks if block.category == category]
        for pack in pack_blocks(category_blocks):
            entries.append((category, pack))
    entries = rebalance_entries(entries)

    files: list[OutputFile] = []
    order = 1
    for category, pack in entries:
            title = pack[0].heading
            slug_base = normalize_key(title) or f"section-{order:03d}"
            filename = f"{order:03d}-{slug_base[:72]}.md"
            payload = "".join(block.text for block in pack).strip() + "\n"
            files.append(
                OutputFile(
                    order=order,
                    category=category,
                    title=title,
                    path=output_dir / category / filename,
                    blocks=pack,
                    payload=payload,
                )
            )
            order += 1
    return files


def rebalance_entries(entries: list[tuple[str, list[Block]]]) -> list[tuple[str, list[Block]]]:
    entries = [(category, list(pack)) for category, pack in entries]
    while True:
        candidates: list[tuple[int, int, int]] = []
        for idx, (category, pack) in enumerate(entries):
            size = sum(len(block.text) for block in pack)
            if size >= MIN_PAYLOAD_CHARS:
                continue
            for neighbor_idx in (idx - 1, idx + 1):
                if not (0 <= neighbor_idx < len(entries)):
                    continue
                neighbor_category, neighbor_pack = entries[neighbor_idx]
                if neighbor_category != category:
                    continue
                combined_size = size + sum(len(block.text) for block in neighbor_pack)
                if combined_size <= MAX_FILE_CHARS:
                    candidates.append((combined_size, idx, neighbor_idx))
        if not candidates:
            break
        _, idx, neighbor_idx = min(candidates)
        keep_idx, remove_idx = sorted((idx, neighbor_idx))
        category, keep_pack = entries[keep_idx]
        _, remove_pack = entries[remove_idx]
        entries[keep_idx] = (category, keep_pack + remove_pack)
        del entries[remove_idx]
    while len(entries) < MIN_OUTPUT_FILES:
        split_candidates = [
            (sum(len(block.text) for block in pack), idx)
            for idx, (_, pack) in enumerate(entries)
            if sum(len(block.text) for block in pack) >= 6_500
        ]
        if not split_candidates:
            break
        _, idx = max(split_candidates)
        category, pack = entries[idx]
        if len(pack) >= 2:
            midpoint = len(pack) // 2
            left = pack[:midpoint]
            right = pack[midpoint:]
        else:
            left_block, right_block = split_block_in_half(pack[0])
            left = [left_block]
            right = [right_block]
        entries[idx : idx + 1] = [(category, left), (category, right)]
    return entries


def split_block_in_half(block: Block) -> tuple[Block, Block]:
    text = block.text
    midpoint = len(text) // 2
    split_at = text.rfind("\n\n", 0, midpoint)
    if split_at < MIN_PAYLOAD_CHARS:
        split_at = text.find("\n\n", midpoint)
    if split_at == -1:
        split_at = midpoint
    left_text = text[:split_at].strip() + "\n"
    right_text = text[split_at:].strip() + "\n"
    left = dataclasses.replace(block, text=left_text)
    right = dataclasses.replace(block, text=right_text)
    return left, right


def frontmatter_for(output_file: OutputFile, source_name: str) -> str:
    titles = [block.heading for block in output_file.blocks]
    first_order = output_file.blocks[0].order
    last_order = output_file.blocks[-1].order
    sha = hashlib.sha256(output_file.payload.encode("utf-8")).hexdigest()
    created = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "---",
        f"title: {yaml_quote(output_file.title)}",
        f"category: {yaml_quote(output_file.category)}",
        f"source: {yaml_quote(source_name)}",
        f"order: {output_file.order}",
        f"source_block_start: {first_order}",
        f"source_block_end: {last_order}",
        f"content_sha256: {yaml_quote(sha)}",
        f"generated_at: {yaml_quote(created)}",
        "headings:",
    ]
    for title in titles:
        lines.append(f"  - {yaml_quote(title)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def write_files(files: list[OutputFile], output_dir: Path, source_name: str) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        (output_dir / category).mkdir(parents=True, exist_ok=True)

    for output_file in files:
        output_file.path.parent.mkdir(parents=True, exist_ok=True)
        output_file.path.write_text(
            frontmatter_for(output_file, source_name) + output_file.payload,
            encoding="utf-8",
            newline="\n",
        )


def write_index(
    files: list[OutputFile],
    output_dir: Path,
    source_path: Path,
    input_chars: int,
    output_chars: int,
    loss_percent: float,
) -> None:
    created = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    unsorted_count = sum(1 for file in files if file.category == "unsorted")
    lines = [
        "---",
        'title: "Tử Vi Đẩu Số Tân Biên Knowledge Base"',
        'category: "index"',
        f"source: {yaml_quote(str(source_path))}",
        f"generated_at: {yaml_quote(created)}",
        f"input_chars: {input_chars}",
        f"output_chars: {output_chars}",
        f"loss_percent: {loss_percent:.4f}",
        f"files_created: {len(files)}",
        f"unsorted_count: {unsorted_count}",
        "---",
        "",
        "# Tử Vi Đẩu Số Tân Biên Knowledge Base",
        "",
        f"- Source: `{source_path}`",
        f"- Input chars: `{input_chars}`",
        f"- Output chars: `{output_chars}`",
        f"- Loss: `{loss_percent:.4f}%`",
        f"- Files created: `{len(files)}`",
        f"- Unsorted files: `{unsorted_count}`",
        "",
    ]
    for category in CATEGORIES:
        category_files = [file for file in files if file.category == category]
        lines.append(f"## {category}")
        lines.append("")
        if not category_files:
            lines.append("- No files.")
            lines.append("")
            continue
        for file in category_files:
            rel = file.path.relative_to(output_dir).as_posix()
            lines.append(f"- [{file.title}]({rel})")
        lines.append("")
    (output_dir / "_index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def payload_output_chars(files: list[OutputFile]) -> int:
    return sum(len(file.payload) for file in files)


def compute_loss(input_chars: int, output_chars: int) -> float:
    if input_chars == 0:
        return 0.0
    return max(0.0, (input_chars - output_chars) / input_chars * 100)


def validate_files(files: list[OutputFile]) -> list[str]:
    warnings: list[str] = []
    if not (100 <= len(files) <= 300):
        warnings.append(f"files_created outside target range 100-300: {len(files)}")
    for file in files:
        try:
            size = file.path.stat().st_size
        except OSError:
            size = len(file.payload.encode("utf-8"))
        if size > MAX_FILE_CHARS:
            warnings.append(f"{file.path.name} exceeds {MAX_FILE_CHARS} bytes: {size}")
    return warnings


def build(input_path: Path, output_dir: Path) -> int:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    raw = input_path.read_text(encoding="utf-8")
    cleaned = clean_text(remove_frontmatter(raw))
    input_chars = len(cleaned)

    blocks = parse_blocks(cleaned)
    categorize_blocks(blocks)
    files = build_output_files(blocks, output_dir)
    output_chars = payload_output_chars(files)
    loss_percent = compute_loss(input_chars, output_chars)

    write_files(files, output_dir, input_path.name)
    write_index(files, output_dir, input_path, input_chars, output_chars, loss_percent)

    unsorted_count = sum(1 for file in files if file.category == "unsorted")
    print(f"input chars: {input_chars}")
    print(f"output chars: {output_chars}")
    print(f"loss %: {loss_percent:.4f}")
    print(f"files created: {len(files)}")
    print(f"unsorted count: {unsorted_count}")

    for warning in validate_files(files):
        print(f"WARNING: {warning}", file=sys.stderr)
    if loss_percent > WARN_LOSS_PERCENT:
        print(f"WARNING: loss exceeds {WARN_LOSS_PERCENT:.0f}% threshold", file=sys.stderr)
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split cleaned Tu Vi Markdown into categorized knowledge-base files."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input cleaned Markdown file.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory.")
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
