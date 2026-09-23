#!/usr/bin/env python3
"""Tra thẻ tuvi-kb cho một lá số đã được người dùng xác nhận.

Dùng:
    python scripts/tra_cuu.py la-so.json            # in danh sách thẻ cần đọc
    python scripts/tra_cuu.py --self-test           # kiểm quy tắc an sao lưu theo ví dụ Tân Biên

Script chỉ chọn thẻ ứng viên, không luận giải. Mọi thẻ ở mức "một phần"
phải đọc mục Điều kiện trước khi dùng. Chỉ cần Python 3, không thư viện ngoài.
Định dạng file lá số: xem SKILL.md, mục "Bước 2".
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from kb_the import parse_card  # noqa: E402  (parse_card sống ở kb_the.py từ G1)

KB = Path(__file__).resolve().parent.parent

BRANCHES = ["ty", "suu", "dan", "mao", "thin", "ti", "ngo", "mui", "than", "dau", "tuat", "hoi"]
BRANCH_NAMES = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
STEMS = ["giap", "at", "binh", "dinh", "mau", "ky", "canh", "tan", "nham", "quy"]
STEM_NAMES = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
# Thứ tự an 12 cung theo chiều thuận kể từ Mệnh (Tân Biên, Lập thành, mục 5 An Mệnh).
PALACE_ORDER = ["menh", "phu-mau", "phuc-duc", "dien-trach", "quan-loc", "no-boc",
                "thien-di", "tat-ach", "tai-bach", "tu-tuc", "phu-the", "huynh-de"]
THAN_ALLOWED = {"menh", "phu-the", "quan-loc", "thien-di", "tai-bach", "phuc-duc"}
BRANCH_GROUPS = {"tu-mo": {"thin", "tuat", "suu", "mui"}, "tu-sinh": {"dan", "than", "ti", "hoi"},
                 "tu-chinh": {"ty", "ngo", "mao", "dau"}}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.replace("Đ", "D").replace("đ", "d"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def read_table(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("| ") and not line.startswith("| id ") and not line.startswith("|---"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def load_registry():
    stars, star_alias, star_group = {}, {}, {}
    for r in read_table(KB / "00-index" / "stars.md"):
        sid, name, aliases, group = r[0], r[1], r[2], r[4]
        stars[sid] = name
        star_group[sid] = group
        for a in [sid, name, *aliases.split(";")]:
            if a.strip():
                star_alias.setdefault(fold(a), sid)
    palaces, palace_alias = {}, {}
    for r in read_table(KB / "00-index" / "palaces.md"):
        pid, name, aliases = r[0], r[1], r[2]
        palaces[pid] = name
        for a in [pid, name, *aliases.split(";")]:
            if a.strip():
                palace_alias.setdefault(fold(a), pid)
    return stars, star_alias, star_group, palaces, palace_alias


def load_cards(folder: str) -> list[dict]:
    return [parse_card(p) for p in sorted((KB / folder).rglob("*.md"))]


# ---------- vị trí trên địa bàn ----------

def tam_hop(i: int) -> list[int]:
    return [(i + 4) % 12, (i + 8) % 12]


def xung(i: int) -> int:
    return (i + 6) % 12


def nhi_hop(i: int) -> int:
    return (1 - i) % 12


def giap(i: int) -> list[int]:
    return [(i - 1) % 12, (i + 1) % 12]


# ---------- sao lưu và tiểu hạn (Tân Biên, Phần 3 mục 4; Lập thành 10.3) ----------

LOC_TON = {"giap": "dan", "at": "mao", "binh": "ti", "mau": "ti", "dinh": "ngo", "ky": "ngo",
           "canh": "than", "tan": "dau", "nham": "hoi", "quy": "ty"}


def branch_index(raw: str) -> int | None:
    """Nhận id ASCII (ty=Tý, ti=Tỵ) hoặc tên có dấu. Không dùng fold vì Tý và Tỵ cùng thành 'ty'."""
    raw = unicodedata.normalize("NFC", str(raw).strip())
    for i, name in enumerate(BRANCH_NAMES):
        if raw.lower() == name.lower():
            return i
    if raw.lower() == "tị":
        return 5
    return BRANCHES.index(raw.lower()) if raw.lower() in BRANCHES else None


def can_chi(lunar_year: int) -> tuple[str, str]:
    return STEMS[(lunar_year - 4) % 10], BRANCHES[(lunar_year - 4) % 12]


def luu_stars(stem: str, branch: str) -> dict[str, int]:
    b = BRANCHES.index(branch)
    loc = BRANCHES.index(LOC_TON[stem])
    ma_by_group = {0: "dan", 2: "than", 1: "hoi", 3: "ti"}  # Thân Tý Thìn, Dần Ngọ Tuất, Tỵ Dậu Sửu, Hợi Mão Mùi
    return {
        "luu-thai-tue": b,
        "luu-tang-mon": (b + 2) % 12,
        "luu-bach-ho": (b + 8) % 12,
        "luu-thien-khoc": (6 - b) % 12,
        "luu-thien-hu": (6 + b) % 12,
        "luu-loc-ton": loc,
        "luu-kinh-duong": (loc + 1) % 12,
        "luu-da-la": (loc - 1) % 12,
        "luu-thien-ma": BRANCHES.index(ma_by_group[b % 4]),
    }


def tieu_han(birth_branch: str, gender: str, year_branch: str) -> int:
    start = {0: "tuat", 2: "thin", 1: "mui", 3: "suu"}[BRANCHES.index(birth_branch) % 4]
    step = 1 if gender == "nam" else -1
    diff = (BRANCHES.index(year_branch) - BRANCHES.index(birth_branch)) % 12
    return (BRANCHES.index(start) + step * diff) % 12


def self_test() -> int:
    n = lambda x: BRANCH_NAMES[x]
    checks = [
        # Tân Biên 4.1: tiểu hạn năm Mùi → Lưu Thái Tuế Mùi, Tang Môn Dậu, Bạch Hổ Mão
        ([n(luu_stars("at", "mui")[k]) for k in ("luu-thai-tue", "luu-tang-mon", "luu-bach-ho")], ["Mùi", "Dậu", "Mão"]),
        # 4.2: năm Mùi → Lưu Khốc Hợi, Lưu Hư Sửu
        ([n(luu_stars("at", "mui")[k]) for k in ("luu-thien-khoc", "luu-thien-hu")], ["Hợi", "Sửu"]),
        # 4.3: năm Ất Mùi → Lưu Lộc Mão, Kình Thìn, Đà Dần
        ([n(luu_stars("at", "mui")[k]) for k in ("luu-loc-ton", "luu-kinh-duong", "luu-da-la")], ["Mão", "Thìn", "Dần"]),
        # 4.4: năm Tý → Lưu Mã Dần
        (n(luu_stars("giap", "ty")["luu-thien-ma"]), "Dần"),
        # 10.3: nam sinh Tý khởi Tý ở Tuất, Dần ở Tý; nữ sinh Ngọ khởi Ngọ ở Thìn, Thân ở Dần
        (n(tieu_han("ty", "nam", "dan")), "Tý"),
        (n(tieu_han("ngo", "nu", "than")), "Dần"),
        # 9.1: nhị hợp Sửu-Tý, Dần-Hợi, Tỵ-Thân
        ([n(nhi_hop(1)), n(nhi_hop(2)), n(nhi_hop(5))], ["Tý", "Hợi", "Thân"]),
    ]
    bad = [(got, want) for got, want in checks if got != want]
    for got, want in bad:
        print(f"SAI: được {got}, sách ghi {want}")
    print(f"self-test: {len(checks) - len(bad)}/{len(checks)} đúng")
    return 1 if bad else 0


# ---------- đọc và kiểm lá số ----------

def load_chart(path: Path, reg):
    stars, star_alias, star_group, palaces, palace_alias = reg
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    gender = fold(str(data.get("gioi_tinh", "")))
    if gender not in ("nam", "nu"):
        errors.append("gioi_tinh phải là 'nam' hoặc 'nu'")
    chart = {}
    for raw_branch, cell in data.get("cung", {}).items():
        bi = branch_index(raw_branch)
        if bi is None:
            errors.append(f"địa chi không hợp lệ: {raw_branch} (dùng: {', '.join(BRANCHES)}; ty=Tý, ti=Tỵ)")
            continue
        pid = palace_alias.get(fold(cell.get("ten", "")))
        if pid not in PALACE_ORDER:
            errors.append(f"cung {raw_branch}: tên cung '{cell.get('ten')}' không có trong palaces.md")
        sids = []
        for s in cell.get("sao", []):
            key = fold(s.split(":")[0].split("(")[0])
            sid = star_alias.get(key)
            if key.startswith("luu-") or key.startswith("l-"):
                continue  # sao lưu do script tự an theo năm xem
            if not sid:
                errors.append(f"cung {raw_branch}: không nhận ra sao '{s}' (tra 00-index/stars.md, ghi id)")
            else:
                sids.append(sid)
        chart[bi] = {"palace": pid, "stars": sids, "dai_han": cell.get("dai_han")}
    if len(chart) != 12:
        errors.append(f"cần đủ 12 cung, mới có {len(chart)}")
    menh = branch_index(data.get("menh", ""))
    than = branch_index(data.get("than", ""))
    if menh is None or than is None:
        errors.append("thiếu 'menh' hoặc 'than' (địa chi)")
    if len(chart) == 12 and menh is not None and than is not None:
        for k, pid in enumerate(PALACE_ORDER):
            got = chart[(menh + k) % 12]["palace"]
            if got != pid:
                errors.append(f"cung {BRANCH_NAMES[(menh + k) % 12]} ghi '{got}', theo thứ tự an cung phải là '{pid}' "
                              "(12 cung an theo chiều thuận từ Mệnh) — kiểm lại ảnh")
        if chart[than]["palace"] not in THAN_ALLOWED:
            errors.append(f"Thân ở cung {chart[than]['palace']}: Thân chỉ cư Mệnh, Phu Thê, Quan Lộc, Thiên Di, Tài Bạch, Phúc Đức")
    if errors:
        print("LÁ SỐ CHƯA HỢP LỆ:\n- " + "\n- ".join(errors), file=sys.stderr)
        sys.exit(1)
    return data, gender, chart, menh, than


# ---------- chọn thẻ ----------

def main_stars(ids, star_group):
    return [s for s in ids if star_group.get(s) == "chinh-tinh"]


TUAN_TRIET = {"tuan", "triet"}


def gop_tuan_triet(ids, card: bool):
    """Thẻ ghi "Tuần, Triệt án ngữ" (có cả tuan, triet) chỉ cần cung có một trong hai.
    Gộp thành một khoá: thẻ phải có đủ cả hai mới gộp; cung có một trong hai là có khoá."""
    ids = set(ids)
    if card:
        return (ids - TUAN_TRIET) | {"tuan-triet"} if TUAN_TRIET <= ids else ids
    return ids | {"tuan-triet"} if ids & TUAN_TRIET else ids


def fmt_stars(ids, stars):
    return ", ".join(stars.get(s, s) for s in ids) or "(không có)"


def report(path: Path) -> int:
    reg = load_registry()
    stars, _, star_group, palaces, _ = reg
    data, gender, chart, menh, than = load_chart(path, reg)
    star_cards = {c["stars"][0]: c for c in load_cards("10-stars")}
    palace_cards = load_cards("20-palaces")
    combos = load_cards("30-combos")
    han_cards = load_cards("40-han")
    rules = load_cards("50-rules")
    phu = load_cards("60-phu")
    star_ids, palace_ids = set(stars), set(palaces) | {"than-cung"}

    def at(i):
        return set(chart[i]["stars"])

    out = []
    w = out.append
    w(f"# Thẻ cần đọc cho lá số `{path.name}`\n")
    w("Mức khớp: **đủ** = mọi sao của thẻ tọa thủ đồng cung; **hội chiếu** = mọi sao có mặt trong "
      "cung + tam hợp + xung chiếu; **một phần** = thẻ liệt kê nhiều sao, chỉ một số có mặt — "
      "PHẢI đọc mục Điều kiện của thẻ, chỉ dùng gạch đầu dòng có điều kiện thật sự thỏa.\n")

    order = [menh] + ([than] if than != menh else []) + [(menh + k) % 12 for k in range(1, 12) if (menh + k) % 12 != than]
    for i in order:
        cell = chart[i]
        pid = cell["palace"]
        self_s = at(i)
        th = tam_hop(i)
        x = xung(i)
        tp = self_s | at(th[0]) | at(th[1]) | at(x)
        around = tp | at(nhi_hop(i)) | at(giap(i)[0]) | at(giap(i)[1])
        borrowed = set()
        if not main_stars(self_s, star_group):
            borrowed = set(main_stars(at(x), star_group))
        dong = self_s | borrowed
        label = palaces[pid] + (" (Thân cư)" if i == than and i != menh else "")
        if i == than and i == menh:
            label = "Mệnh (Thân cư Mệnh)"
        w(f"\n## {label} — cung {BRANCH_NAMES[i]}\n")
        w(f"- Tọa thủ: {fmt_stars(cell['stars'], stars)}")
        if borrowed:
            w(f"- **Vô Chính Diệu** — mượn chính tinh xung chiếu: {fmt_stars(sorted(borrowed), stars)} "
              "(đọc `30-combos/vo-chinh-dieu.md`, `50-rules/menh-vo-chinh-dieu-dac-diem-va-cuu-giai.md`)")
        w(f"- Tam hợp: {BRANCH_NAMES[th[0]]} ({palaces[chart[th[0]]['palace']]}): {fmt_stars(chart[th[0]]['stars'], stars)}"
          f" | {BRANCH_NAMES[th[1]]} ({palaces[chart[th[1]]['palace']]}): {fmt_stars(chart[th[1]]['stars'], stars)}")
        w(f"- Xung chiếu: {BRANCH_NAMES[x]} ({palaces[chart[x]['palace']]}): {fmt_stars(chart[x]['stars'], stars)}")
        n = nhi_hop(i)
        w(f"- Nhị hợp: {BRANCH_NAMES[n]} ({palaces[chart[n]['palace']]}): {fmt_stars(chart[n]['stars'], stars)}")
        g = giap(i)
        w(f"- Giáp: {BRANCH_NAMES[g[0]]}: {fmt_stars(chart[g[0]]['stars'], stars)} | {BRANCH_NAMES[g[1]]}: {fmt_stars(chart[g[1]]['stars'], stars)}")

        w("\n**Thẻ sao (tọa thủ):** " + ", ".join(f"`{star_cards[s]['path']}`" for s in cell["stars"] if s in star_cards))

        targets = {pid}
        if i == than:
            targets.add("than")
        hits = []
        dong_k, tp_k = gop_tuan_triet(dong, card=False), gop_tuan_triet(tp, card=False)
        for c in palace_cards:
            if not targets & set(c.get("palace", [])):
                continue
            if c.get("positions") and BRANCHES[i] not in c["positions"]:
                continue
            if c.get("gender", "any") not in ("any", gender):
                continue
            s = gop_tuan_triet(c.get("stars", []), card=True)
            if not s:
                continue
            if s <= dong_k:
                hits.append(("đủ, mượn xung chiếu" if s & borrowed else "đủ", c))
            elif s <= tp_k and s & dong_k:
                hits.append(("hội chiếu", c))
            elif len(s) >= 3 and s & dong_k:
                hits.append(("một phần", c))
        rank = {"đủ": 0, "đủ, mượn xung chiếu": 0, "hội chiếu": 1, "một phần": 2}
        w("\n**Thẻ cung:**")
        for lvl, c in sorted(hits, key=lambda h: rank[h[0]]):
            w(f"- [{lvl}] `{c['path']}` — {c['title']}")
        if not hits:
            w("- (không có thẻ cung khớp; chỉ dùng thẻ sao, ghi rõ trong bài là sách không có đoạn riêng)")

        ph = []
        for c in phu:
            tags = set(c.get("tags", []))
            p_tags = {("than" if t == "than-cung" else t) for t in tags & palace_ids}
            b_tags = tags & set(BRANCHES)
            for grp, members in BRANCH_GROUPS.items():
                if grp in tags:
                    b_tags |= members
            s = tags & star_ids
            if not s or (p_tags and not p_tags & targets) or (b_tags and BRANCHES[i] not in b_tags):
                continue
            if s <= around and s & dong:
                ph.append(c)
        if ph:
            w("\n**Phú (ứng viên — kiểm câu phú khớp vị trí/sao thật):**")
            for c in ph:
                w(f"- `{c['path']}` — {c['title']}")

        if i in (menh, than):
            cb = [c for c in combos if len(set(c["stars"]) & tp) >= 2 and set(c["stars"]) & dong]
            if cb:
                w("\n**Cách cục (ứng viên — đối chiếu mục Điều kiện thành cách và Phá cách):**")
                for c in cb:
                    w(f"- `{c['path']}` — {c['title']} (sao có mặt: {fmt_stars(sorted(set(c['stars']) & tp), stars)})")

    # ---------- hạn ----------
    w("\n## Hạn\n")
    birth, year = data.get("nam_sinh"), data.get("nam_xem")
    if not (isinstance(birth, int) and isinstance(year, int)):
        w("Chưa có `nam_sinh` và `nam_xem` (năm âm lịch, số nguyên) — hỏi người dùng muốn xem hạn năm nào.")
    else:
        age = year - birth + 1
        bs, bb = can_chi(birth)
        ys, yb = can_chi(year)
        w(f"- Sinh năm {STEM_NAMES[STEMS.index(bs)]} {BRANCH_NAMES[BRANCHES.index(bb)]}; "
          f"xem năm {STEM_NAMES[STEMS.index(ys)]} {BRANCH_NAMES[BRANCHES.index(yb)]}; tuổi âm {age}.")
        dh = next((i for i in range(12) if isinstance(chart[i]["dai_han"], int)
                   and chart[i]["dai_han"] <= age < chart[i]["dai_han"] + 10), None)
        th_i = tieu_han(bb, gender, yb)
        luu = luu_stars(ys, yb)
        w(f"- Đại hạn: " + (f"cung {BRANCH_NAMES[dh]} ({palaces[chart[dh]['palace']]})" if dh is not None
                           else "không xác định (thiếu số đại hạn trong lá số)"))
        w(f"- Tiểu hạn (theo Tân Biên 10.3): cung {BRANCH_NAMES[th_i]} ({palaces[chart[th_i]['palace']]}) "
          "— nếu ảnh lá số ghi tiểu hạn khác, hỏi lại người dùng.")
        w("- Sao lưu: " + "; ".join(f"{k} ở {BRANCH_NAMES[v]}" for k, v in luu.items()))
        w("- Lưu đại hạn (Tân Biên 10.2) script không tính; nếu cần, tính tay theo `90-source/tan-bien/0014-luu-dai-han.md`.")
        spots = [("Đại hạn", dh), ("Tiểu hạn", th_i), ("Lưu Thái Tuế", luu["luu-thai-tue"])]
        for name, i in spots:
            if i is None:
                continue
            present = at(i) | {k for k, v in luu.items() if v == i}
            cards = [c for c in han_cards if set(c.get("stars", [])) & present]
            w(f"\n**{name} — cung {BRANCH_NAMES[i]} ({palaces[chart[i]['palace']]})**, sao: "
              f"{fmt_stars(sorted(present), stars)}")
            for c in cards:
                w(f"- `{c['path']}` — {c['title']}")
        w("\n**Thẻ hạn chung (luôn đọc):**")
        for c in han_cards:
            if not c.get("stars"):
                w(f"- `{c['path']}` — {c['title']}")

    w("\n## Quy tắc toàn lá số (50-rules) — chọn thẻ có Điều kiện khớp lá số\n")
    for c in rules:
        w(f"- `{c['path']}` — {c['title']}")
    print("\n".join(out))
    return 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) != 1:
        print(__doc__)
        return 2
    return report(Path(argv[0]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
