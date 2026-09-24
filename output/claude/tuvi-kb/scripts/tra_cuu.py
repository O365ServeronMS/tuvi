#!/usr/bin/env python3
"""Tra thẻ tuvi-kb cho một lá số đã được người dùng xác nhận.

Dùng:
    python scripts/tra_cuu.py la-so.json                    # in danh sách thẻ cần đọc
    python scripts/tra_cuu.py --pack la-so.json thư-mục-bài  # sinh gói ngữ cảnh pack/ (G3)
    python scripts/tra_cuu.py --kiem-pack la-so.json thư-mục-bài  # so tập thẻ gói với report()
    python scripts/tra_cuu.py --self-test                   # kiểm quy tắc an sao lưu theo ví dụ Tân Biên

Script chỉ chọn thẻ ứng viên, không luận giải. Mọi thẻ ở mức "một phần"
phải đọc mục Điều kiện trước khi dùng. Chỉ cần Python 3, không thư viện ngoài.
Định dạng file lá số: xem SKILL.md, mục "Bước 2".
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

import kb_the
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
    rows = read_table(KB / "00-index" / "stars.md")
    # id đăng ký trước tên/alias: tên "Quan Phủ" (quan-phu-loc-ton) bỏ dấu trùng id quan-phu (Quan Phù)
    for r in rows:
        star_alias[fold(r[0])] = r[0]
    for r in rows:
        sid, name, aliases, group = r[0], r[1], r[2], r[4]
        stars[sid] = name
        star_group[sid] = group
        for a in [name, *aliases.split(";")]:
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


def load_mieu(data: dict, star_alias: dict) -> dict[int, dict[str, str]]:
    """Mã miếu/hãm mỗi sao mỗi cung, theo địa chi (load_chart bỏ mã này nên tính riêng cho G3)."""
    mieu: dict[int, dict[str, str]] = {}
    for raw_branch, cell in data.get("cung", {}).items():
        bi = branch_index(raw_branch)
        if bi is None:
            continue
        d: dict[str, str] = {}
        for s in cell.get("sao", []):
            key = fold(s.split(":")[0].split("(")[0])
            sid = star_alias.get(key)
            if not sid or key.startswith("luu-") or key.startswith("l-"):
                continue
            if ":" in s:
                d[sid] = s.split(":", 1)[1].strip()
        mieu[bi] = d
    return mieu


def build_context(path: Path) -> dict:
    reg = load_registry()
    stars, star_alias, star_group, palaces, palace_alias = reg
    data, gender, chart, menh, than = load_chart(path, reg)
    return {
        "reg": reg, "stars": stars, "star_group": star_group, "palaces": palaces,
        "data": data, "gender": gender, "chart": chart, "menh": menh, "than": than,
        "star_cards": {c["stars"][0]: c for c in load_cards("10-stars")},
        "palace_cards": load_cards("20-palaces"),
        "combos": load_cards("30-combos"),
        "han_cards": load_cards("40-han"),
        "rules": load_cards("50-rules"),
        "phu": load_cards("60-phu"),
        "star_ids": set(stars),
        "palace_ids": set(palaces) | {"than-cung"},
        "mieu": load_mieu(data, star_alias),
    }


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


def nam_xem_list(data: dict) -> list[int]:
    """`nam_xem` là một năm (số nguyên) hoặc danh sách năm; trả danh sách năm tăng dần, không trùng."""
    v = data.get("nam_xem")
    ds = [v] if isinstance(v, int) else v if isinstance(v, list) else []
    return sorted({y for y in ds if isinstance(y, int) and not isinstance(y, bool)})


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
        # Gói (G7): chia cung thành 3 nhóm liên tục, chia file tại ranh giới thẻ
        (chia_nhom([5, 5, 5, 1, 1, 1, 9], 3), [2, 6]),
        (chia_nhom([4, 4], 3), [1]),
        ([(len(p.encode()) <= 60, p.count("### `")) for p in
          chia_file("# T\n" + "".join(f"### `{c}.md`\n" + "z" * 20 + "\n" for c in "abc"), 60)],
         [(True, 1)] * 3),
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


def select_palace(ctx: dict, i: int) -> dict:
    """Chọn thẻ ứng viên cho một cung. Dữ liệu có cấu trúc dùng chung cho report() và pack()."""
    chart, stars, palaces, star_group = ctx["chart"], ctx["stars"], ctx["palaces"], ctx["star_group"]
    gender, menh, than = ctx["gender"], ctx["menh"], ctx["than"]
    palace_cards, phu, combos = ctx["palace_cards"], ctx["phu"], ctx["combos"]
    star_ids, palace_ids = ctx["star_ids"], ctx["palace_ids"]

    def at(k):
        return set(chart[k]["stars"])

    cell = chart[i]
    pid = cell["palace"]
    self_s = at(i)
    th = tam_hop(i)
    x = xung(i)
    tp = self_s | at(th[0]) | at(th[1]) | at(x)
    n = nhi_hop(i)
    g = giap(i)
    around = tp | at(n) | at(g[0]) | at(g[1])
    borrowed = set()
    if not main_stars(self_s, star_group):
        borrowed = set(main_stars(at(x), star_group))
    dong = self_s | borrowed
    label = palaces[pid] + (" (Thân cư)" if i == than and i != menh else "")
    if i == than and i == menh:
        label = "Mệnh (Thân cư Mệnh)"

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
    hits.sort(key=lambda h: rank[h[0]])

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

    cb = []
    if i in (menh, than):
        cb = [c for c in combos if len(set(c["stars"]) & tp) >= 2 and set(c["stars"]) & dong]

    quanh = self_s | at(th[0]) | at(th[1]) | at(x) | at(n) | at(g[0]) | at(g[1]) | borrowed

    return {
        "i": i, "pid": pid, "label": label, "cell": cell, "self_s": self_s,
        "tam_hop": th, "xung": x, "nhi_hop": n, "giap": g, "borrowed": borrowed,
        "dong": dong, "tp": tp, "around": around, "quanh": quanh,
        "hits": hits, "phu": ph, "combos": cb,
    }


def report(path: Path) -> int:
    ctx = build_context(path)
    stars, palaces = ctx["stars"], ctx["palaces"]
    star_cards, han_cards, rules = ctx["star_cards"], ctx["han_cards"], ctx["rules"]
    data, gender, chart, menh, than = ctx["data"], ctx["gender"], ctx["chart"], ctx["menh"], ctx["than"]

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
        sel = select_palace(ctx, i)
        cell, th, x, n, g = sel["cell"], sel["tam_hop"], sel["xung"], sel["nhi_hop"], sel["giap"]
        borrowed = sel["borrowed"]
        w(f"\n## {sel['label']} — cung {BRANCH_NAMES[i]}\n")
        w(f"- Tọa thủ: {fmt_stars(cell['stars'], stars)}")
        if borrowed:
            w(f"- **Vô Chính Diệu** — mượn chính tinh xung chiếu: {fmt_stars(sorted(borrowed), stars)} "
              "(đọc `30-combos/vo-chinh-dieu.md`, `50-rules/menh-vo-chinh-dieu-dac-diem-va-cuu-giai.md`)")
        w(f"- Tam hợp: {BRANCH_NAMES[th[0]]} ({palaces[chart[th[0]]['palace']]}): {fmt_stars(chart[th[0]]['stars'], stars)}"
          f" | {BRANCH_NAMES[th[1]]} ({palaces[chart[th[1]]['palace']]}): {fmt_stars(chart[th[1]]['stars'], stars)}")
        w(f"- Xung chiếu: {BRANCH_NAMES[x]} ({palaces[chart[x]['palace']]}): {fmt_stars(chart[x]['stars'], stars)}")
        w(f"- Nhị hợp: {BRANCH_NAMES[n]} ({palaces[chart[n]['palace']]}): {fmt_stars(chart[n]['stars'], stars)}")
        w(f"- Giáp: {BRANCH_NAMES[g[0]]}: {fmt_stars(chart[g[0]]['stars'], stars)} | {BRANCH_NAMES[g[1]]}: {fmt_stars(chart[g[1]]['stars'], stars)}")

        w("\n**Thẻ sao (tọa thủ):** " + ", ".join(f"`{star_cards[s]['path']}`" for s in cell["stars"] if s in star_cards))

        w("\n**Thẻ cung:**")
        for lvl, c in sel["hits"]:
            w(f"- [{lvl}] `{c['path']}` — {c['title']}")
        if not sel["hits"]:
            w("- (không có thẻ cung khớp; chỉ dùng thẻ sao, ghi rõ trong bài là sách không có đoạn riêng)")

        if sel["phu"]:
            w("\n**Phú (ứng viên — kiểm câu phú khớp vị trí/sao thật):**")
            for c in sel["phu"]:
                w(f"- `{c['path']}` — {c['title']}")

        if sel["combos"]:
            w("\n**Cách cục (ứng viên — đối chiếu mục Điều kiện thành cách và Phá cách):**")
            for c in sel["combos"]:
                w(f"- `{c['path']}` — {c['title']} (sao có mặt: {fmt_stars(sorted(set(c['stars']) & sel['tp']), stars)})")

    # ---------- hạn ----------
    w("\n## Hạn\n")
    birth, years = data.get("nam_sinh"), nam_xem_list(data)
    if not (isinstance(birth, int) and years):
        w("Chưa có `nam_sinh` và `nam_xem` (năm âm lịch, số nguyên hoặc danh sách) — hỏi người dùng muốn xem hạn năm nào.")
    for year in years if isinstance(birth, int) else []:
        if len(years) > 1:
            w(f"\n### Năm {year}\n")
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


# ================================================================= G3: --pack

DROP_SECTIONS = {
    "palace-card": {"Nguyên văn", "Phú liên quan"},
    "star-card": {"Nguyên văn"},
    "phu-card": {"Nguyên văn", "Nguồn giải"},
    "combo-card": {"Nguyên văn"},
    "han-card": {"Nguyên văn"},
    "rule-card": {"Nguyên văn", "Ví dụ trong sách"},
}


def fmt_stars_mieu(ctx: dict, i: int, ids) -> str:
    stars, mieu = ctx["stars"], ctx["mieu"].get(i, {})
    parts = []
    for sid in ids:
        name = stars.get(sid, sid)
        code = mieu.get(sid)
        parts.append(f"{name} ({code})" if code else name)
    return ", ".join(parts) if parts else "(không có)"


def render_the(rel_path: str, level: str | None, ctx_the: dict | None,
                loc_bo_rows: list, seen: set) -> list[str]:
    """In một thẻ theo quy cách gói (G3). ctx_the=None: không lọc (combo/han/rule)."""
    if rel_path in seen:
        return []
    the = kb_the.doc_the(KB / rel_path)
    ctype = the.meta.get("type")
    all_dong = kb_the.sections_dong(the)
    if ctype in ("star-card", "palace-card", "phu-card") and ctx_the is not None:
        kept, removed = kb_the.filter_the(the, ctx_the)
        loc_bo_rows.extend(removed)
        if ctype == "phu-card" and not kept:
            return []  # bỏ cả thẻ (P1/P2)
    else:
        kept = all_dong
    seen.add(rel_path)
    drop = DROP_SECTIONS.get(ctype, {"Nguyên văn"})

    lines = [f"### `{rel_path}` — {the.title}" + (f" [{level}]" if level else "")]
    for name, sec_lines in the.sections:
        if name in drop or name == "(trước mục đầu)":
            continue
        lines.append(f"#### {name}")
        pre = all_dong.get(name, [])
        post = kept.get(name, [])
        if not pre:
            body = [l for l in sec_lines if l.strip()]
            lines.extend(body if body else ["(trống)"])
        elif not post:
            lines.append("(các dòng của mục này không khớp lá số — xem loc-bo.md)")
        else:
            lines.extend(f"- {d.raw}" for d in post)
    return lines


VCD_CARD = "30-combos/vo-chinh-dieu.md"


def build_palace_file(ctx: dict, sel: dict, loc_bo_rows: list) -> str:
    i = sel["i"]
    lines: list[str] = []
    seen: set = set()
    if i == ctx["than"] and i != ctx["menh"]:
        lines.append("(Thân cư cung này.)\n")
    lines.append(f"# {sel['label']} — cung {BRANCH_NAMES[i]}\n")
    lines.append(f"- Tọa thủ: {fmt_stars_mieu(ctx, i, sel['cell']['stars'])}")
    if sel["borrowed"]:
        lines.append(f"- Vô Chính Diệu — mượn chính tinh xung chiếu: {fmt_stars(sorted(sel['borrowed']), ctx['stars'])}")
    lines.append("")

    def ctx_the(level: str | None) -> dict:
        muc_khop = "đủ" if level and level.startswith("đủ") else level
        return {"gioi": ctx["gender"], "chi": i, "mieu": ctx["mieu"].get(i, {}),
                "quanh": sel["quanh"], "muc_khop": muc_khop}

    for star_id in sel["cell"]["stars"]:
        card = ctx["star_cards"].get(star_id)
        if not card:
            continue
        lines.extend(render_the(card["path"], "đủ", ctx_the("đủ"), loc_bo_rows, seen))
        lines.append("")

    for lvl, c in sel["hits"]:
        lines.extend(render_the(c["path"], lvl, ctx_the(lvl), loc_bo_rows, seen))
        lines.append("")

    if sel["borrowed"]:  # report() bảo đọc thẻ này cho mọi cung Vô Chính Diệu, không chỉ khi nó là cách cục Mệnh/Thân
        lines.extend(render_the(VCD_CARD, None, None, loc_bo_rows, seen))
        lines.append("")

    if sel["phu"]:
        lines.append("**Phú ứng viên (sau lọc P1, P2):**\n")
        for c in sel["phu"]:
            lines.extend(render_the(c["path"], None, ctx_the(None), loc_bo_rows, seen))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_00_nen(path: Path, ctx: dict) -> str:
    data, gender, chart, menh, than = ctx["data"], ctx["gender"], ctx["chart"], ctx["menh"], ctx["than"]
    stars = ctx["stars"]
    lines = [f"# Nền — lá số `{path.name}`\n"]
    lines.append(f"- Giới tính: {gender}")
    birth = data.get("nam_sinh")
    if isinstance(birth, int):
        bs, bb = can_chi(birth)
        lines.append(f"- Năm sinh (âm lịch): {STEM_NAMES[STEMS.index(bs)]} {BRANCH_NAMES[BRANCHES.index(bb)]} ({birth})")
    for year in nam_xem_list(data) if isinstance(birth, int) else []:
        ys, yb = can_chi(year)
        lines.append(f"- Năm xem hạn: {STEM_NAMES[STEMS.index(ys)]} {BRANCH_NAMES[BRANCHES.index(yb)]} ({year}); "
                      f"tuổi âm {year - birth + 1}")
    lines.append(f"- Mệnh tại {BRANCH_NAMES[menh]}; Thân tại {BRANCH_NAMES[than]}" +
                 (" (Thân cư Mệnh)" if than == menh else ""))
    lines.append("")
    lines.append("## Bảng 12 cung\n")
    lines.append("| Chi | Cung | Đại hạn | Tọa thủ (miếu/hãm) | Tam hợp | Xung chiếu | Nhị hợp | Giáp | Vô Chính Diệu |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for k in range(12):
        i = (menh + k) % 12
        sel = select_palace(ctx, i)
        cell, th, x, n, g = sel["cell"], sel["tam_hop"], sel["xung"], sel["nhi_hop"], sel["giap"]
        dh = cell["dai_han"]
        vcd = fmt_stars(sorted(sel["borrowed"]), stars) if sel["borrowed"] else "—"
        lines.append(
            f"| {BRANCH_NAMES[i]} | {sel['label']} | {dh if dh is not None else '—'} | "
            f"{fmt_stars_mieu(ctx, i, cell['stars'])} | "
            f"{BRANCH_NAMES[th[0]]}: {fmt_stars(chart[th[0]]['stars'], stars)}; "
            f"{BRANCH_NAMES[th[1]]}: {fmt_stars(chart[th[1]]['stars'], stars)} | "
            f"{BRANCH_NAMES[x]}: {fmt_stars(chart[x]['stars'], stars)} | "
            f"{BRANCH_NAMES[n]}: {fmt_stars(chart[n]['stars'], stars)} | "
            f"{BRANCH_NAMES[g[0]]}: {fmt_stars(chart[g[0]]['stars'], stars)}; "
            f"{BRANCH_NAMES[g[1]]}: {fmt_stars(chart[g[1]]['stars'], stars)} | {vcd} |")
    lines.append("")
    lines.append("## Mức khớp\n")
    lines.append("**đủ** = mọi sao của thẻ tọa thủ đồng cung; **hội chiếu** = mọi sao có mặt trong "
                  "cung + tam hợp + xung chiếu; **một phần** = thẻ liệt kê nhiều sao, chỉ một số có mặt — "
                  "PHẢI đọc mục Điều kiện, chỉ dùng gạch đầu dòng có điều kiện thật sự thỏa.\n")
    return "\n".join(lines) + "\n"


def build_cach_cuc(sel_menh: dict, sel_than: dict, loc_bo_rows: list) -> str:
    lines = ["# Cách cục ứng viên (Mệnh, Thân)\n"]
    seen: set = set()
    combos_all = list(sel_menh["combos"])
    seen_paths = {c["path"] for c in combos_all}
    if sel_than is not sel_menh:
        for c in sel_than["combos"]:
            if c["path"] not in seen_paths:
                combos_all.append(c)
                seen_paths.add(c["path"])
    if not combos_all:
        lines.append("(không có cách cục ứng viên)")
    for c in combos_all:
        lines.extend(render_the(c["path"], None, None, loc_bo_rows, seen))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_quy_tac(ctx: dict, loc_bo_rows: list) -> str:
    lines = ["# Quy tắc toàn lá số (50-rules)\n"]
    seen: set = set()
    for c in ctx["rules"]:
        lines.extend(render_the(c["path"], None, None, loc_bo_rows, seen))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_han(ctx: dict, loc_bo_rows: list, year: int) -> str | None:
    data, gender, chart, palaces = ctx["data"], ctx["gender"], ctx["chart"], ctx["palaces"]
    stars, han_cards = ctx["stars"], ctx["han_cards"]
    birth = data.get("nam_sinh")
    if not isinstance(birth, int):
        return None
    age = year - birth + 1
    bs, bb = can_chi(birth)
    ys, yb = can_chi(year)
    lines = [f"# Hạn năm {year}\n"]
    lines.append(f"- Sinh năm {STEM_NAMES[STEMS.index(bs)]} {BRANCH_NAMES[BRANCHES.index(bb)]}; "
                 f"xem năm {STEM_NAMES[STEMS.index(ys)]} {BRANCH_NAMES[BRANCHES.index(yb)]}; tuổi âm {age}.")
    dh = next((i for i in range(12) if isinstance(chart[i]["dai_han"], int)
               and chart[i]["dai_han"] <= age < chart[i]["dai_han"] + 10), None)
    th_i = tieu_han(bb, gender, yb)
    luu = luu_stars(ys, yb)
    lines.append("- Đại hạn: " + (f"cung {BRANCH_NAMES[dh]} ({palaces[chart[dh]['palace']]})" if dh is not None
                                  else "không xác định"))
    lines.append(f"- Tiểu hạn: cung {BRANCH_NAMES[th_i]} ({palaces[chart[th_i]['palace']]})")
    lines.append("- Sao lưu: " + "; ".join(f"{k} ở {BRANCH_NAMES[v]}" for k, v in luu.items()))
    seen: set = set()
    spots = [("Đại hạn", dh), ("Tiểu hạn", th_i), ("Lưu Thái Tuế", luu["luu-thai-tue"])]
    for name, i in spots:
        if i is None:
            continue
        present = set(chart[i]["stars"]) | {k for k, v in luu.items() if v == i}
        cards = [c for c in han_cards if set(c.get("stars", [])) & present]
        lines.append(f"\n## {name} — cung {BRANCH_NAMES[i]} ({palaces[chart[i]['palace']]}), "
                     f"sao: {fmt_stars(sorted(present), stars)}\n")
        for c in cards:
            lines.extend(render_the(c["path"], None, None, loc_bo_rows, seen))
            lines.append("")
    lines.append("\n## Thẻ hạn chung\n")
    for c in han_cards:
        if not c.get("stars"):
            lines.extend(render_the(c["path"], None, None, loc_bo_rows, seen))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


BYTE_MOI_TOKEN = 1.755      # đo thật ở G6 trên output của Read
NEN_SUB_AGENT = 15_000      # token nền mỗi sub-agent (system prompt, tool, agent md)
TRAN_GOI = 70_000           # token gói tối đa của một lượt (không tính nền)
TRAN_FILE = 45_000          # byte tối đa một file gói; Read cắt file lớn hơn
TOM_TAT_UOC = 6_000         # byte ước tính một file tom-tat-*.md (lượt đợt 1 viết, chưa có lúc dựng gói)


def chia_nhom(sizes: list[int], k: int) -> list[int]:
    """Điểm cắt chia `sizes` thành tối đa k nhóm liên tục, nhóm lớn nhất nhỏ nhất; hoà thì nhóm đều nhất."""
    n = len(sizes)
    k = max(1, min(k, n))
    best = None
    def thu(start: int, con: int, cuts: list[int]):
        nonlocal best
        if con == 1:
            cs = cuts + [n]
            nhom = [sum(sizes[x:y]) for x, y in zip([0] + cuts, cs)]
            key = (max(nhom), max(nhom) - min(nhom))
            if best is None or key < best[0]:
                best = (key, cuts)
            return
        for c in range(start + 1, n - con + 2):
            thu(c, con - 1, cuts + [c])
    thu(0, k, [])
    return best[1] if best else []


def chia_file(text: str, tran: int = TRAN_FILE) -> list[str]:
    """Chia text tại ranh giới thẻ (dòng mở bằng "### `") sao cho mỗi phần ≤ tran byte (trừ khi một thẻ đã lớn hơn)."""
    if len(text.encode("utf-8")) <= tran:
        return [text]
    khoi = text.split("\n### `")
    dau, the_list = khoi[0], ["### `" + t for t in khoi[1:]]
    tieu_de = dau.strip().split("\n", 1)[0]
    parts: list[str] = []
    cur = dau.rstrip() + "\n"
    for t in the_list:
        them = "\n" + t.rstrip() + "\n"
        if len((cur + them).encode("utf-8")) > tran and "### `" in cur:
            parts.append(cur)
            cur = f"{tieu_de} (tiếp, phần {len(parts) + 1})\n"
        cur += them
    parts.append(cur)
    return parts


def ghi_goi(pack_dir: Path, stem: str, text: str) -> list[str]:
    """Ghi file gói, chia thành <stem>-1.md, <stem>-2.md… nếu quá TRAN_FILE. Trả tên các file đã ghi."""
    parts = chia_file(text)
    names = [f"{stem}.md"] if len(parts) == 1 else [f"{stem}-{k}.md" for k in range(1, len(parts) + 1)]
    for name, part in zip(names, parts):
        (pack_dir / name).write_text(part, encoding="utf-8")
    return names


def build_phan_cong(files: dict[str, list[str]], con_lai_pids: list[str], years: list[int],
                    cung_sizes: list[int]) -> dict:
    """files: stem → tên file đã ghi (sau khi chia). Đợt 1: A, R song song; đợt 2: B, C, E và D (một năm)
    hoặc D1, D2… (mỗi năm xem một lượt, ghi phan-d-<năm>.md, tiêu đề ## 7.k.)."""
    nen = ["00-nen.md"]
    tom_tat = ["../tom-tat-a.md", "../tom-tat-r.md"]
    doc_a = nen + files["menh"] + files.get("than", []) + files["cach-cuc"]
    phan_cong = {
        "A": {"dot": 1, "doc": doc_a, "ghi": ["phan-a.md", "phan-a-cach-cuc.md", "tom-tat-a.md"]},
        "R": {"dot": 1, "doc": nen + files["quy-tac"], "ghi": ["phan-r.md", "tom-tat-r.md"]},
    }
    cuts = chia_nhom(cung_sizes, 3)
    bounds = list(zip([0] + cuts, cuts + [len(con_lai_pids)]))
    for luot, (x, y) in zip(("B", "C", "E"), bounds):
        doc = nen + tom_tat + [f for pid in con_lai_pids[x:y] for f in files[f"cung-{pid}"]]
        phan_cong[luot] = {"dot": 2, "doc": doc, "ghi": [f"phan-{luot.lower()}.md"], "so_bat_dau": x + 1}
    for k, year in enumerate(years, 1):
        if len(years) == 1:
            luot, ghi, tieu_de = "D", "phan-d.md", f"## 7. Hạn năm {year}"
        else:
            luot, ghi, tieu_de = f"D{k}", f"phan-d-{year}.md", f"## 7.{k}. Hạn năm {year}"
        phan_cong[luot] = {"dot": 2, "doc": nen + tom_tat + files[f"han-{year}"], "ghi": [ghi],
                           "nam": year, "tieu_de": tieu_de}
    return phan_cong


def write_loc_bo(path: Path, rows: list) -> None:
    lines = ["# Dòng bị lọc (không giao cho lượt nào đọc)\n", "| Thẻ | Mục | Lý do | Nội dung |", "|---|---|---|---|"]
    for r in rows:
        content = r.line.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{r.the}` | {r.section} | {r.reason} | {content[:200]} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_pack_report(pack_dir: Path, phan_cong: dict) -> None:
    sizes = {p.name: p.stat().st_size for p in sorted(pack_dir.glob("*.md"))}
    print(f"| File | Byte | Token ước tính (byte/{BYTE_MOI_TOKEN}) |")
    print("|---|---|---|")
    for name, b in sizes.items():
        warn = f" CẢNH BÁO: file > {TRAN_FILE} byte" if b > TRAN_FILE and name != "loc-bo.md" else ""
        print(f"| {name} | {b} | {round(b / BYTE_MOI_TOKEN)} |{warn}")
    print()
    for luot, info in phan_cong.items():
        total = sum(TOM_TAT_UOC if d.startswith("../") else sizes.get(d, 0) for d in info["doc"])
        tok = round(total / BYTE_MOI_TOKEN)
        warn = f"  CẢNH BÁO: gói vượt {TRAN_GOI} token" if tok > TRAN_GOI else ""
        n_tt = sum(d.startswith("../") for d in info["doc"])
        ghi_chu = f" (gồm {n_tt} tom-tat ước {TOM_TAT_UOC} byte/file)" if n_tt else ""
        print(f"Lượt {luot} (đợt {info['dot']}): {total} byte, ~{tok} token gói + {NEN_SUB_AGENT} nền"
              f"{ghi_chu}{warn}")


def pack(path: Path, out_dir: Path) -> int:
    ctx = build_context(path)
    pack_dir = out_dir / "pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    for old in list(pack_dir.glob("*.md")) + list(pack_dir.glob("*.json")):
        old.unlink()  # gói sinh tự động; xoá bản cũ để khỏi sót file đã đổi tên (quy-tac.md, trich.json)
    loc_bo_rows: list = []
    files: dict[str, list[str]] = {}

    menh, than = ctx["menh"], ctx["than"]
    sel_menh = select_palace(ctx, menh)
    sel_than = select_palace(ctx, than) if than != menh else sel_menh

    (pack_dir / "00-nen.md").write_text(build_00_nen(path, ctx), encoding="utf-8")
    files["menh"] = ghi_goi(pack_dir, "menh", build_palace_file(ctx, sel_menh, loc_bo_rows))
    if than != menh:
        files["than"] = ghi_goi(pack_dir, "than", build_palace_file(ctx, sel_than, loc_bo_rows))

    than_pid = ctx["chart"][than]["palace"]
    con_lai_pids = [pid for pid in PALACE_ORDER[1:] if pid != than_pid]
    for pid in con_lai_pids:
        i = (menh + PALACE_ORDER.index(pid)) % 12
        sel = select_palace(ctx, i)
        files[f"cung-{pid}"] = ghi_goi(pack_dir, f"cung-{pid}", build_palace_file(ctx, sel, loc_bo_rows))

    files["cach-cuc"] = ghi_goi(pack_dir, "cach-cuc", build_cach_cuc(sel_menh, sel_than, loc_bo_rows))
    files["quy-tac"] = ghi_goi(pack_dir, "quy-tac", build_quy_tac(ctx, loc_bo_rows))

    years = nam_xem_list(ctx["data"]) if isinstance(ctx["data"].get("nam_sinh"), int) else []
    for year in years:
        files[f"han-{year}"] = ghi_goi(pack_dir, f"han-{year}", build_han(ctx, loc_bo_rows, year))

    cung_sizes = [sum((pack_dir / f).stat().st_size for f in files[f"cung-{pid}"]) for pid in con_lai_pids]
    phan_cong = build_phan_cong(files, con_lai_pids, years, cung_sizes)
    (pack_dir / "phan-cong.json").write_text(json.dumps(phan_cong, ensure_ascii=False, indent=1), encoding="utf-8")
    write_loc_bo(pack_dir / "loc-bo.md", loc_bo_rows)

    print_pack_report(pack_dir, phan_cong)
    return 0


CARD_REF_RE = re.compile(r"`((?:10-stars|20-palaces|30-combos|40-han|50-rules|60-phu)/[^`]+\.md)`")


def kiem_pack(path: Path, out_dir: Path) -> int:
    """So tập thẻ report() với gói; mọi thẻ thiếu phải là phú đã ghi loc-bo.md; mọi file phan-cong.json có thật."""
    pack_dir = out_dir / "pack"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        report(path)
    report_paths = set(CARD_REF_RE.findall(buf.getvalue()))
    pack_text = "\n".join(p.read_text(encoding="utf-8") for p in pack_dir.glob("*.md") if p.name != "loc-bo.md")
    pack_paths = set(CARD_REF_RE.findall(pack_text))
    loc_bo = (pack_dir / "loc-bo.md").read_text(encoding="utf-8")
    phan_cong = json.loads((pack_dir / "phan-cong.json").read_text(encoding="utf-8"))

    loi = []
    for p in sorted(report_paths - pack_paths):
        if not (p.startswith("60-phu/") and f"`{p}`" in loc_bo):
            loi.append(f"thẻ report() có mà gói thiếu (không phải phú đã lọc): {p}")
    for p in sorted(pack_paths - report_paths):
        loi.append(f"thẻ trong gói mà report() không liệt kê: {p}")
    for luot, info in phan_cong.items():
        for d in info["doc"]:
            if not d.startswith("../") and not (pack_dir / d).is_file():
                loi.append(f"lượt {luot} được giao file không có: {d}")
    giao = {d for info in phan_cong.values() for d in info["doc"]}
    for p in sorted(pack_dir.glob("*.md")):
        if p.name != "loc-bo.md" and p.name not in giao:
            loi.append(f"file gói không giao cho lượt nào: {p.name}")
    for l in loi:
        print("SAI:", l)
    phu_loc = len([p for p in report_paths - pack_paths if p.startswith("60-phu/")])
    print(f"thẻ report(): {len(report_paths)}, thẻ gói: {len(pack_paths)}, phú đã lọc: {phu_loc}, lỗi: {len(loi)}")
    return 1 if loi else 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) == 3 and argv[0] == "--pack":
        return pack(Path(argv[1]), Path(argv[2]))
    if len(argv) == 3 and argv[0] == "--kiem-pack":
        return kiem_pack(Path(argv[1]), Path(argv[2]))
    if len(argv) != 1:
        print(__doc__)
        return 2
    return report(Path(argv[0]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
