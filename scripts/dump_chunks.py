#!/usr/bin/env python3
"""Dump source chunks (frontmatter stripped) into one scratch file for reading.

Usage:
  python scripts/dump_chunks.py OUT.md tb#0039 td#0050 tl#0044        # by id prefix
  python scripts/dump_chunks.py OUT.md 'tan-bien/004[4-9]-*' 'tran-doan/0064-*'   # by glob under 90-source
  python scripts/dump_chunks.py --list tb                              # list ids + titles of a book
  python scripts/dump_chunks.py --grep 'Tử Tức'                        # ids of chunks containing text

Each chunk is written as:  ##### <chunk id>  followed by its body. Read the
file with the Read tool, then quote from it verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tuvi_kb_common import BOOK_BY_CODE, SOURCE_DIR, parse_frontmatter  # noqa: E402


def all_chunks():
    for p in sorted(SOURCE_DIR.rglob("*.md")):
        meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        yield p, meta, body


def select(specs: list[str]):
    chosen = []
    for spec in specs:
        if "#" in spec:  # id or id prefix, e.g. tb#0039 or tb#0039-...-p03
            code, rest = spec.split("#", 1)
            book = BOOK_BY_CODE[code].slug
            for p in sorted((SOURCE_DIR / book).glob("*.md")):
                if p.stem.startswith(rest):
                    chosen.append(p)
        else:  # glob relative to 90-source
            chosen.extend(sorted(SOURCE_DIR.glob(spec)))
    seen, out = set(), []
    for p in chosen:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", help="output file (scratchpad path recommended)")
    ap.add_argument("specs", nargs="*", help="chunk id prefixes (tb#0039) or globs (tan-bien/004*)")
    ap.add_argument("--list", metavar="CODE", help="list chunk ids and titles of a book (tb, tl, td, npl)")
    ap.add_argument("--grep", metavar="TEXT", help="print ids of chunks whose body contains TEXT")
    args = ap.parse_args(argv)

    if args.list:
        book = BOOK_BY_CODE[args.list].slug
        for p in sorted((SOURCE_DIR / book).glob("*.md")):
            meta, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
            print(f"{meta['id']:<60} {meta['chars']:>5}  {meta['title'][:70]}  [{','.join(meta.get('stars_in_title', []))}]")
        return 0
    if args.grep:
        for p, meta, body in all_chunks():
            if args.grep in body:
                print(meta["id"])
        return 0
    if not args.out or not args.specs:
        ap.error("cần OUT và ít nhất một spec, hoặc --list / --grep")

    paths = select(args.specs)
    with open(args.out, "w", encoding="utf-8") as fh:
        for p in paths:
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            fh.write(f"##### {meta['id']}\n{body.strip()}\n\n")
    total = sum(p.stat().st_size for p in paths)
    print(f"{len(paths)} chunks, ~{total // 1024} KB -> {args.out}")
    for p in paths:
        print("  ", p.stem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
