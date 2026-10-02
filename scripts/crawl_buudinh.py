#!/usr/bin/env python3
"""Crawl toàn bộ bài của blog Bửu Đình (Blogger) qua feed JSON -> md + manifest.

Dùng: PYTHONIOENCODING=utf-8 python3 scripts/crawl_buudinh.py [--out DIR]
Chỉ cần Python 3. Chạy lại được (ghi đè theo id bài; bài không đổi giữ nguyên).
"""
import argparse, json, re, sys, time, urllib.request
from html.parser import HTMLParser
from pathlib import Path

BLOG = "https://tuviungdung.blogspot.com"
PAGE = 150
BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "blockquote"}


class ToMd(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.href, self.skip = [], None, 0

    def handle_starttag(self, t, a):
        a = dict(a)
        if t in ("script", "style"):
            self.skip += 1
        elif t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n\n" + "#" * min(int(t[1]) + 1, 6) + " ")
        elif t == "li":
            self.out.append("\n- ")
        elif t in ("b", "strong"):
            self.out.append("**")
        elif t == "img" and a.get("src"):
            self.out.append(f"\n![]({a['src']})\n")
        elif t == "a":
            self.href = a.get("href")
            self.out.append("[")
        elif t in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, t):
        if t in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif t in ("b", "strong"):
            self.out.append("**")
        elif t == "a":
            self.out.append(f"]({self.href})" if self.href else "]")
            self.href = None
        elif t in BLOCK:
            self.out.append("\n")

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)

    def text(self):
        s = "".join(self.out).replace("\xa0", " ")
        s = re.sub(r"\*\*\s*\*\*", "", s)
        s = re.sub(r"[ \t]+\n", "\n", s)
        return re.sub(r"\n{3,}", "\n\n", s).strip()


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tuvi-kb-crawler"}), timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def full_body(url):
    """Feed chỉ trả phần trước jump-break (#more); lấy cả bài từ trang."""
    page = get(url)
    m = re.search(r"<div class='post-body[^>]*>(.*?)<div class='post-footer", page, re.S)
    if not m:
        raise RuntimeError(f"không thấy post-body: {url}")
    time.sleep(1)
    return m.group(1)


def slug_of(url):
    return url.rsplit("/", 1)[-1].removesuffix(".html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output/buu-dinh")
    out = Path(ap.parse_args().out)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "posts").mkdir(parents=True, exist_ok=True)

    entries, start = [], 1
    while True:
        feed = json.loads(get(f"{BLOG}/feeds/posts/default?alt=json&max-results={PAGE}&start-index={start}"))["feed"]
        total = int(feed["openSearch$totalResults"]["$t"])
        got = feed.get("entry", [])
        entries += got
        start += len(got)
        print(f"fetched {len(entries)}/{total}", file=sys.stderr)
        if not got or len(entries) >= total:
            break
        time.sleep(1)

    manifest = []
    for e in entries:
        url = next(l["href"] for l in e["link"] if l["rel"] == "alternate")
        pid = e["id"]["$t"].rsplit("-", 1)[-1]
        title = e["title"]["$t"].strip()
        pub, upd = e["published"]["$t"], e["updated"]["$t"]
        html = e["content"]["$t"]
        if "#more" in html:
            html = full_body(url)
        (out / "raw" / f"{pid}.html").write_text(html, encoding="utf-8")
        md = ToMd()
        md.feed(html)
        body = md.text()
        labels = [c["term"] for c in e.get("category", [])]
        name = f"{pub[:10]}-{slug_of(url)}.md"
        head = f'---\nid: bd#{pid}\ntitle: "{title}"\nurl: {url}\npublished: {pub}\nupdated: {upd}\nlabels: {labels}\n---\n\n# {title}\n\n'
        (out / "posts" / name).write_text(head + body + "\n", encoding="utf-8")
        manifest.append({"id": pid, "title": title, "url": url, "published": pub, "updated": upd,
                         "file": f"posts/{name}", "chars": len(body)})

    manifest.sort(key=lambda m: m["published"])
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ok: {len(manifest)} bài, {sum(m['chars'] for m in manifest):,} ký tự -> {out}")


if __name__ == "__main__":
    main()
