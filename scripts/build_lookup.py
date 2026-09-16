#!/usr/bin/env python3
"""Sinh output/tuvi-kb/00-index/lookup.md tu frontmatter cua moi the.

Doc tat ca the trong 10-stars .. 60-phu, xuat:
  - bang sao -> the sao
  - bang (cung, bo sao) -> the cung
  - bang cach cuc -> the combo
  - danh sach rule, han, phu, sap theo tag (hoac sao neu khong co tag)

Neu lookup.md vuot INDEX_WARN_BYTES (60 KB), bang cung duoc tach rieng ra
00-index/lookup-palaces.md va lookup.md chi con dong tro toi file do.

Chi dung thu vien chuan + tuvi_kb_common (khong doc them thu vien ngoai).
Chay lai script nay sau moi lan them/sua the; khong sua tay lookup*.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuvi_kb_common import (  # noqa: E402
    INDEX_DIR,
    KB_DIR,
    FrontmatterError,
    load_palaces,
    load_stars,
    parse_frontmatter,
)

CARD_DIRS = {
    "10-stars": "star-card",
    "20-palaces": "palace-card",
    "30-combos": "combo-card",
    "40-han": "han-card",
    "50-rules": "rule-card",
    "60-phu": "phu-card",
}

INDEX_WARN_BYTES = 60 * 1024

HEADER = (
    "# Tra cứu thẻ tuvi-kb\n\n"
    "Sinh tự động bởi `scripts/build_lookup.py` từ frontmatter mọi thẻ trong "
    "`10-stars/` đến `60-phu/`. Không sửa tay; chạy lại script sau khi thêm hoặc "
    "sửa thẻ.\n\n"
)


def rel(path: Path) -> str:
    return str(path.relative_to(KB_DIR)).replace("\\", "/")


def title_of(body: str) -> str:
    for line in body.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def load_cards() -> list[dict]:
    cards: list[dict] = []
    for dirname, ctype in CARD_DIRS.items():
        d = KB_DIR / dirname
        if not d.exists():
            continue
        for path in sorted(d.rglob("*.md")):
            if path.name.startswith("_"):
                continue
            try:
                meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            except FrontmatterError:
                continue
            cards.append(
                {
                    "type": ctype,
                    "path": path,
                    "rel": rel(path),
                    "id": str(meta.get("id") or ""),
                    "title": title_of(body),
                    "stars": [str(s) for s in (meta.get("stars") or [])],
                    "palace": [str(p) for p in (meta.get("palace") or [])],
                    "positions": [str(p) for p in (meta.get("positions") or [])],
                    "tags": [str(t) for t in (meta.get("tags") or [])],
                }
            )
    return cards


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in row) + " |")
    return "\n".join(lines) + "\n"


def build_star_section(stars: dict, cards: list[dict]) -> str:
    by_star = {c["stars"][0]: c for c in cards if c["type"] == "star-card" and c["stars"]}
    rows = []
    for sid in sorted(stars):
        card = by_star.get(sid)
        link = f"`10-stars/{sid}.md`" if card else "(chưa có thẻ)"
        rows.append([sid, stars[sid].name, link])
    return "## Sao → thẻ sao\n\n" + md_table(["id", "tên", "thẻ"], rows)


def build_palace_section(cards: list[dict]) -> str:
    palace_cards = [c for c in cards if c["type"] == "palace-card"]
    rows = [
        [c["path"].parent.name, "+".join(c["stars"]), f"`{c['rel']}`"]
        for c in sorted(palace_cards, key=lambda c: (c["path"].parent.name, c["path"].stem))
    ]
    return "## (Cung, bộ sao) → thẻ cung\n\n" + md_table(["cung", "bộ sao", "thẻ"], rows)


def build_combo_section(cards: list[dict]) -> str:
    combo_cards = [c for c in cards if c["type"] == "combo-card"]
    rows = [
        [c["path"].stem, c["title"], "+".join(c["stars"]), f"`{c['rel']}`"]
        for c in sorted(combo_cards, key=lambda c: c["path"].stem)
    ]
    return "## Cách cục → thẻ combo\n\n" + md_table(["id", "tên", "sao", "thẻ"], rows)


def build_tagged_list(cards: list[dict], ctype: str, heading: str) -> str:
    """Danh sách gọn (bullet, không phải bảng) sắp theo tag đầu tiên rồi id.

    Dùng bullet thay vì bảng để giữ 60-phu (325 thẻ) dưới ngưỡng cảnh báo
    kích thước khi phải tách ra file riêng.
    """
    wanted = [c for c in cards if c["type"] == ctype]

    def sort_key(c: dict):
        return (c["tags"][0] if c["tags"] else "~", c["path"].stem)

    lines = [f"## {heading}\n"]
    for c in sorted(wanted, key=sort_key):
        tags = ", ".join(c["tags"]) if c["tags"] else ("+".join(c["stars"] + c["positions"]) or "-")
        lines.append(f"- `{c['path'].stem}` ({tags}) → `{c['rel']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    stars = load_stars()
    load_palaces()  # chỉ để phát hiện lỗi sổ cung sớm; không dùng trực tiếp
    cards = load_cards()

    star_section = build_star_section(stars, cards)
    palace_section = build_palace_section(cards)
    combo_section = build_combo_section(cards)
    rule_section = build_tagged_list(cards, "rule-card", "Quy tắc (50-rules) theo tag")
    han_section = build_tagged_list(cards, "han-card", "Hạn (40-han) theo tag/sao")
    phu_section = build_tagged_list(cards, "phu-card", "Phú (60-phu) theo tag")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    lookup_path = INDEX_DIR / "lookup.md"
    overflow_paths = {
        "palace": INDEX_DIR / "lookup-palaces.md",
        "phu": INDEX_DIR / "lookup-phu.md",
    }
    overflow_sections = {"palace": (palace_section, "(Cung, bộ sao) → thẻ cung"),
                          "phu": (phu_section, "Phú (60-phu) theo tag")}

    sections = {"star": star_section, "palace": palace_section, "combo": combo_section,
                "rule": rule_section, "han": han_section, "phu": phu_section}
    order = ["star", "palace", "combo", "rule", "han", "phu"]
    # Ưu tiên tách bảng cung trước (lớn nhất, đúng như runbook nêu), rồi đến
    # danh sách phú nếu vẫn còn vượt ngưỡng sau khi tách cung.
    offload_order = ["palace", "phu"]
    offloaded: list[str] = []

    def assemble() -> str:
        parts = [HEADER]
        for key in order:
            if key in offloaded:
                _, heading = overflow_sections[key]
                parts.append(f"## {heading}\n\nBảng/danh sách này để riêng vì quá lớn: xem `00-index/{overflow_paths[key].name}`.\n")
            else:
                parts.append(sections[key])
        return "\n".join(parts)

    full = assemble()
    for key in offload_order:
        if len(full.encode("utf-8")) <= INDEX_WARN_BYTES:
            break
        offloaded.append(key)
        content, heading = overflow_sections[key]
        doc = HEADER.replace("Tra cứu thẻ tuvi-kb", f"Tra cứu thẻ tuvi-kb — {heading}") + content
        overflow_paths[key].write_text(doc, encoding="utf-8")
        full = assemble()

    for key, path in overflow_paths.items():
        if key not in offloaded and path.exists():
            path.unlink()

    lookup_path.write_text(full, encoding="utf-8")
    print(f"the doc: {len(cards)}")
    print(f"lookup.md: {len(full.encode('utf-8'))} byte")
    for key in offloaded:
        p = overflow_paths[key]
        print(f"{p.name}: {p.stat().st_size} byte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
