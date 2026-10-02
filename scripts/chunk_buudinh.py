#!/usr/bin/env python3
"""Lọc, làm sạch, chia khúc các bài Bửu Đình đã crawl -> 90-source/buu-dinh/.

Đầu vào: output/buu-dinh/manifest.json + posts/*.md (do crawl_buudinh.py sinh).
Đầu ra:  output/claude/tuvi-kb/90-source/buu-dinh/NNNN-<slug>[-pNN].md, id `bd#NNNN-...`
         (NNNN = số thứ tự bài trong manifest xếp theo ngày đăng) và
         output/buu-dinh/chunking-report.json, output/buu-dinh/selected.json.

Làm sạch chỉ đổi hình thức (bỏ ảnh/liên kết, nối dòng cứng, tiêu đề); KHÔNG sửa chính tả
hay đổi chữ của tác giả, để trích dẫn còn đúng nguyên văn bài đăng.
Dùng: PYTHONIOENCODING=utf-8 python3 scripts/chunk_buudinh.py [--dry-run] [--self-test]
"""
from __future__ import annotations

import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawl_buudinh import ToMd
from tuvi_kb_common import (ROOT, SOURCE_DIR, dump_frontmatter, fold, load_palaces, load_stars,
                            nfc, palace_detector, star_detector)

BD_DIR = ROOT / "output" / "buu-dinh"
OUT_DIR = SOURCE_DIR / "buu-dinh"
MIN_POST = 1500          # bài ngắn hơn: chỉ là lời dẫn/video/bị khóa
TARGET, MAX_CHUNK, MIN_CHUNK = 3500, 6000, 700

THEORY = re.compile(
    r"\b(tu vi|thien phu|thien co|thai duong|thai am|vu khuc|thien dong|liem trinh|tham lang|cu mon|thien tuong|"
    r"thien luong|that sat|pha quan|tuan|triet|tu hoa|hoa ky|khong kiep|linh hoa|hinh|dieu|dao hoa|hong loan|"
    r"thien hi|khoi viet|xuong khuc|kinh da|loc ton|thai tue|bach ho|thanh long|dai hao|tuong binh|phuc binh|"
    r"quoc an|phuong cac|duong phu|la vong|hoa cai|co gia|qua tu|pha toai|tang mon|thien ma|tam tai|cach|bo|nhom|"
    r"han|cung|phu|nhi hop|luc hoi|menh|sao|an sao|song loc|quyen loc|ky kiep|tam khong|tam am|hu vo|trai phep|"
    r"khai tru|qua bao|dong luong|co luong|cu nhat|cu co|cu dong|tham vu|tu sat|am duong|tu phu|liem|"
    r"vo chinh dieu|phi tinh|phi hinh|phi hong|phi khoi|song hi|loc ma|nghiep|ach|chinh tinh|dac ham|mieu|"
    r"the xung|dau quan|ly thuyet|mat troi|nhung hieu lam|sai lam|phoi hop|loc|tai bach|quan loc|dien trach|"
    r"tat ach|no boc|thien di|phuc duc|phu the|tu tuc|luu ha|luc si|tau thu|tuong quan|thien hinh)\b")
NOT_THEORY = re.compile(
    r"video|flash|gemini|trang thu nghiem|chao ca nha|mua ten mien|canh bao in lau|tuyen chon hoc vien|"
    r"cau chuc|cam nghi|niem vui|ky niem|gioi thieu va huong dan|huong dan su dung|f8 hay|ba nam nhin lai|xin chao")
# Tiêu đề không khớp từ khóa nhưng đã đọc và là bài lý thuyết (chỉ số trong manifest).
INCLUDE_IDX = {55, 92, 125, 134, 150, 151, 282, 494}


def select(manifest: list[dict]) -> list[dict]:
    rows = []
    for i, m in enumerate(manifest):
        t = fold(m["title"]).lower()
        if m["chars"] < MIN_POST:
            why = "ngắn"
        elif NOT_THEORY.search(t):
            why = "video/quảng bá/Gemini"
        elif i in INCLUDE_IDX or THEORY.search(t):
            why = ""
        else:
            why = "không phải bài lý thuyết (kể chuyện, thơ, tiểu sử, hỏi đáp, lá số người nổi tiếng)"
        rows.append({"idx": i, "title": m["title"], "chars": m["chars"], "file": m["file"], "keep": not why, "reason": why})
    return rows


# ------------------------------------------------------------------- làm sạch

IMG_LINK = re.compile(r"\[\s*!\[[^\]]*\]\([^)]*\)\s*\]\([^)]*\)")
IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")
DANGLING = re.compile(r"^\s*\]\([^)]*\)\s*$|\[\s*\]\([^)]*\)", re.M)
LINK = re.compile(r"\[([^\]\n]+)\]\([^)]*\)")
LIST_RE = re.compile(r"^(- |\d+[.)] |#{2,6} )")


def is_heading_para(p: str) -> bool:
    if re.match(r"^(\*\*)?Nhóm [^\n]{2,55}$", p):
        return True
    if "\n" in p or len(p) > 90 or p.endswith((".", ",", ";")) and not p.startswith("**"):
        return False
    if p.startswith("**") and p.endswith("**") and p.count("**") == 2:
        return True
    letters = [c for c in p if c.isalpha()]
    return len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) >= 0.85



VN_CHARS = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.I)
EN_WORDS = re.compile(r"\b(the|and|of|is|are|with|that|this|from|which|have|has|been|will|can|not|they|their|it|by|for|be)\b", re.I)
EN_WORDS2 = re.compile(r"\b(the|and|of|is|are|with|that|this|from|which|in|to|on|a|an|how|there|could|would|only|new|such|more|but|or|you|we|your|our|if|when|than|then|so)\b")
ADMIN_STRONG = re.compile(
    r"(?i)box\.net|add sender|\S+@\S+\.\w+|tên miền|tuviungdung|ymail|gmail|blogspot|"
    r"(tải|download).{0,40}(phần mềm|v3\.\d)|(phần mềm|v3\.\d).{0,40}(tải|download)")
ADMIN_WEAK = re.compile(
    r"(?i)\bblog\b.{0,80}(cảm ơn|ghé qua|chúc|hình nền|ẩn danh|bạn đọc)|"
    r"(cảm ơn|ghé qua|hình nền|ẩn danh).{0,80}\bblog\b|^(cảm ơn|chào) (bạn|cháu|các bạn|anh|chị)\b")
JUNK_LINE = re.compile(r"^\s*([.\-_=~*·•]\s*){4,}$", re.M)
BARE_URL = re.compile(r"https?://\S+")
HTML_TAG = re.compile(r"</?(s|i|b|u|em|span|font|br|div|p|strike)\b[^>]*>", re.I)
WINGDINGS = re.compile(r"^[üØ§·]\s+", re.M)


def drop_reason(p: str) -> str | None:
    body = p.lstrip("# ").strip()
    words = len(body.split())
    n_en = len(EN_WORDS.findall(body))
    n_en2 = len(EN_WORDS2.findall(body))
    if len(body) >= 25 and words >= 5 and not VN_CHARS.search(body) and n_en2 >= 2:
        return "en"
    if len(body) >= 25 and n_en >= 3 and (not VN_CHARS.search(body) or n_en / max(words, 1) >= 0.08):
        return "en"
    if len(body) < 500 and ADMIN_STRONG.search(body):
        return "admin"
    if ADMIN_WEAK.search(body):
        return "admin-weak"
    return None


DROPPED: list[tuple[str, str, str]] = []  # (post, lý do, đoạn đầu)

COMMENT_MARKS = ("Trackbacks (", "comment-rss", "comment-form-wrapper", 'id="comment-list"', "Comments (",
                 'class="comment-item', 'class="comment-content', 'class="vcard', "ypfusercard")
COMMENTS_CUT: list[tuple[str, int]] = []  # (bài, số ký tự HTML bị cắt)


def body_without_comments(pid: str, title: str) -> str:
    """Bài import từ Yahoo 360 mang theo cả khối bình luận trong thân bài; cắt ở dấu hiệu đầu tiên."""
    html = (BD_DIR / "raw" / f"{pid}.html").read_text(encoding="utf-8")
    cut = min((i for i in (html.find(m) for m in COMMENT_MARKS) if i >= 0), default=-1)
    if cut >= 0:
        COMMENTS_CUT.append((title, len(html) - cut))
        html = html[:cut]
    md = ToMd()
    md.feed(html)
    return md.text()


def clean_post(body: str, title: str) -> str:
    t = nfc(body.replace("\r", "")).replace("​", "")
    t = re.sub(r"[\u0300-\u036f]", "", t)  # dấu thanh rời không ghép được (lỗi gõ của bài gốc)
    t = re.sub(r"^# .*\n", "", t.strip(), count=1)
    t = IMG_LINK.sub("", t)
    t = IMG.sub("", t)
    t = DANGLING.sub("", t)
    t = LINK.sub(r"\1", t)
    t = re.sub(r"^\s*[\[\]]\s*$", "", t, flags=re.M)
    t = HTML_TAG.sub("", t)
    t = BARE_URL.sub("", t)
    t = JUNK_LINE.sub("", t)
    t = WINGDINGS.sub("- ", t)
    paras = [p.strip() for p in re.split(r"\n\s*\n", t)]
    out: list[str] = []
    for p in paras:
        if not p:
            continue
        why = drop_reason(p)
        if why:
            DROPPED.append((title, why, p[:100]))
            continue
        if p.startswith("#"):
            head, _, rest = re.sub(r"^#+\s*", "", p.replace("**", "").strip()).partition("\n")
            out.append("## " + head.strip())
            if rest.strip():
                out.append(rest.strip())
            continue
        if is_heading_para(p):
            out.append("## " + p.replace("**", "").strip().rstrip(":").strip())
            continue
        lines = []
        for ln in p.replace("**", "").split("\n"):
            ln = ln.strip()
            if not ln:
                continue
            if drop_reason(ln) == "en":
                DROPPED.append((title, "en-dòng", ln[:100]))
                continue
            lines.append(ln)
        if not lines:
            continue
        joined = ""
        for ln in lines:
            if joined and not LIST_RE.match(ln):
                joined += " " + ln
            else:
                joined += ("\n" if joined else "") + ln
        joined = re.sub(r"[ \t]{2,}", " ", joined)
        joined = re.sub(r"\s+([,.;:!?])", r"\1", joined)
        if joined.strip():
            out.append(joined.strip())
    while out and out[-1].startswith("## ") and not VN_CHARS.search(out[-1]) and DROPPED and DROPPED[-1][0] == title:
        DROPPED.append((title, "heading-mồ-côi", out.pop()[:100]))
    keep = []
    for i, q in enumerate(out):
        if q.startswith("## ") and not VN_CHARS.search(q) and (i + 1 == len(out) or out[i + 1].startswith("## ")) \
                and any(d[0] == title and d[1] in ("en", "en-dòng") for d in DROPPED):
            DROPPED.append((title, "heading-mồ-côi", q[:100]))
            continue
        keep.append(q)
    out = keep
    if out and out[0].lstrip("# ").strip().lower() == title.strip().lower():
        out = out[1:]
    return "\n\n".join(out)


# ------------------------------------------------------------------ chia khúc


def split_sections(text: str, title: str) -> list[tuple[str, str]]:
    secs, cur_t, cur = [], title, []
    for p in text.split("\n\n"):
        if p.startswith("## "):
            if cur:
                secs.append((cur_t, "\n\n".join(cur)))
            cur_t, cur = p[3:].strip(), [p]
        else:
            cur.append(p)
    if cur:
        secs.append((cur_t, "\n\n".join(cur)))
    return secs


def split_big(title: str, text: str) -> list[tuple[str, str]]:
    if len(text) <= MAX_CHUNK:
        return [(title, text)]
    parts, cur = [], ""
    for p in text.split("\n\n"):
        while len(p) > MAX_CHUNK:  # đoạn quá dài: cắt ở cuối câu
            cut = p.rfind(". ", 0, MAX_CHUNK - 200)
            cut = cut + 1 if cut > 0 else MAX_CHUNK
            if cur:
                parts.append(cur); cur = ""
            parts.append(p[:cut].strip()); p = p[cut:].strip()
        if cur and len(cur) + len(p) > TARGET:
            parts.append(cur); cur = ""
        cur = (cur + "\n\n" + p).strip()
    if cur:
        parts.append(cur)
    return [(title, x) for x in parts]


def chunk_post(title: str, text: str) -> list[tuple[str, str]]:
    units: list[tuple[str, str]] = []
    for t, s in split_sections(text, title):
        units += split_big(t, s)
    chunks: list[tuple[str, str]] = []
    cur_t, cur = "", ""
    for t, s in units:
        if cur and len(cur) + len(s) > MAX_CHUNK or (cur and len(cur) >= TARGET):
            chunks.append((cur_t, cur)); cur_t, cur = "", ""
        if not cur:
            cur_t = t
        cur = (cur + "\n\n" + s).strip()
    if cur:
        if chunks and len(cur) < MIN_CHUNK and len(chunks[-1][1]) + len(cur) <= MAX_CHUNK + 1000:
            chunks[-1] = (chunks[-1][0], chunks[-1][1] + "\n\n" + cur)
        else:
            chunks.append((cur_t, cur))
    return chunks


def slug_of(title: str, n: int = 48) -> str:
    from tuvi_kb_common import normalize_key
    s = normalize_key(title)
    if len(s) > n:
        cut = s.rfind("-", 0, n)
        s = s[: cut if cut > 12 else n]
    return s or "bai"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    manifest = json.loads((BD_DIR / "manifest.json").read_text(encoding="utf-8"))
    rows = select(manifest)
    (BD_DIR / "selected.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    sdet, pdet = star_detector(load_stars()), palace_detector(load_palaces())

    if not a.dry_run:
        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        OUT_DIR.mkdir(parents=True)
    n_chunks, sizes, empty = 0, [], []
    for r in rows:
        if not r["keep"]:
            continue
        m = manifest[r["idx"]]
        raw = body_without_comments(m["id"], m["title"])
        text = clean_post(raw, m["title"])
        if len(text) < MIN_POST // 2:
            empty.append(m["title"]); continue
        chunks = chunk_post(m["title"], text)
        base = slug_of(m["title"])
        for k, (ct, body) in enumerate(chunks, 1):
            cid = f"bd#{r['idx']:04d}-{base}" + (f"-p{k:02d}" if len(chunks) > 1 else "")
            meta = {
                "id": cid, "book": "buu-dinh", "book_code": "bd",
                "book_title": "Tử Vi Ứng Dụng (blog Bửu Đình)",
                "title": (ct.strip() or m["title"])[:120], "heading_path": [m["title"]] + ([ct] if ct and ct != m["title"] else []),
                "level": 1, "ordinal": r["idx"], "part": k, "parts": len(chunks),
                "source_file": f"output/buu-dinh/{m['file']}", "source_url": m["url"], "published": m["published"][:10],
                "chars": len(body),
                "stars_detected": list(dict(sorted(sdet.count(body).items(), key=lambda kv: (-kv[1], kv[0]))))[:20],
                "stars_in_title": sorted(sdet.count(ct)),
                "palaces_detected": list(dict(sorted(pdet.count(body).items(), key=lambda kv: (-kv[1], kv[0]))))[:6],
                "non_luan": False,
            }
            if not a.dry_run:
                (OUT_DIR / (cid.split("#", 1)[1] + ".md")).write_text(dump_frontmatter(meta) + "\n" + body + "\n", encoding="utf-8")
            n_chunks += 1; sizes.append(len(body))
    sizes.sort()
    rep = {"posts_total": len(rows), "posts_kept": sum(r["keep"] for r in rows) - len(empty),
           "posts_dropped": sum(not r["keep"] for r in rows) + len(empty), "empty_after_clean": empty,
           "chunks": n_chunks, "size_min": sizes[0], "size_median": sizes[len(sizes) // 2],
           "size_p90": sizes[9 * len(sizes) // 10], "size_max": sizes[-1], "chunks_over_max": sum(s > MAX_CHUNK for s in sizes)}
    if not a.dry_run:
        import collections
        cnt = collections.Counter(d[1] for d in DROPPED)
        rep["dropped_paragraphs"] = dict(cnt)
        rep["posts_with_comments_cut"] = len(COMMENTS_CUT)
        rep["comment_html_chars_cut"] = sum(c for _, c in COMMENTS_CUT)
        (BD_DIR / "dropped-paragraphs.json").write_text(
            json.dumps([{"post": a_, "reason": b_, "text": c_} for a_, b_, c_ in DROPPED], ensure_ascii=False, indent=1), encoding="utf-8")
        (BD_DIR / "chunking-report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


def self_test() -> int:
    raw = "# T\n\n[\n![](http://x/a.gif)\n](http://x/b.gif)\n\n**NHẬN XÉT**:\n\ndòng một\ncủa đoạn **đậm** và [liên kết](http://u).\n\n- ý a\n- ý b\n"
    out = clean_post(raw, "T")
    assert "gif" not in out and "http" not in out and "**" not in out, out
    assert "## NHẬN XÉT" in out, out
    assert "dòng một của đoạn đậm và liên kết." in out, out
    assert "- ý a\n- ý b" in out, out
    long = "\n\n".join(f"## M{i}\n\n" + "x" * 2000 for i in range(5))
    cs = chunk_post("T", clean_post(long, "T"))
    assert all(len(c) <= MAX_CHUNK for _, c in cs) and len(cs) >= 3, [len(c) for _, c in cs]
    print("self-test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
