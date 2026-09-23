#!/usr/bin/env python3
"""Đo token từ transcript Claude Code (jsonl), để so trước/sau khi giảm token.

Dùng:
    python3 scripts/do_token.py <file.jsonl | thư-mục> [...]

Truyền thư mục thì quét mọi *.jsonl bên dưới, kể cả subagents/. Mỗi
transcript in một dòng bảng; cuối cùng in dòng tổng.

Cách tính: xem docs/plan-giam-token.md mục G0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Hệ số quy đổi giá — kiểm lại bảng giá khi đổi model.
COST_INPUT = 1.0
COST_CACHE_READ = 0.1
COST_CACHE_WRITE = 1.25
COST_OUTPUT = 5.0


def find_jsonl(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.jsonl")))
        elif p.is_file():
            out.append(p)
    return out


def tool_result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def measure(path: Path) -> dict:
    usage_by_id: dict[str, dict] = {}
    tool_counts: dict[str, int] = {}
    bash_90source = 0
    tool_result_bytes = 0
    contexts: list[int] = []

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("type")
            if t == "assistant":
                msg = d.get("message", {})
                mid = msg.get("id")
                usage = msg.get("usage")
                if mid and usage:
                    usage_by_id[mid] = usage
                for c in msg.get("content", []) or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name", "?")
                        tool_counts[name] = tool_counts.get(name, 0) + 1
                        if name == "Bash" and "90-source" in str(c.get("input", "")):
                            bash_90source += 1
            elif t == "user":
                msg = d.get("message", {})
                content = msg.get("content")
                blocks = content if isinstance(content, list) else []
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        text = tool_result_text(b.get("content"))
                        tool_result_bytes += len(text.encode("utf-8"))

    cache_read = cache_write = output_tokens = input_tokens = 0
    for usage in usage_by_id.values():
        ir = usage.get("input_tokens", 0) or 0
        cr = usage.get("cache_read_input_tokens", 0) or 0
        cw = usage.get("cache_creation_input_tokens", 0) or 0
        ot = usage.get("output_tokens", 0) or 0
        input_tokens += ir
        cache_read += cr
        cache_write += cw
        output_tokens += ot
        contexts.append(ir + cr + cw)

    return {
        "path": path,
        "luot": len(usage_by_id),
        "input": input_tokens,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "output": output_tokens,
        "ngu_canh_max": max(contexts) if contexts else 0,
        "tool_counts": tool_counts,
        "bash_90source": bash_90source,
        "tool_result_bytes": tool_result_bytes,
    }


def quy_doi(m: dict) -> float:
    return (m["input"] * COST_INPUT + m["cache_read"] * COST_CACHE_READ
            + m["cache_write"] * COST_CACHE_WRITE + m["output"] * COST_OUTPUT)


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 2
    files = find_jsonl(argv)
    if not files:
        print("Không tìm thấy file .jsonl nào.", file=sys.stderr)
        return 1

    rows = [measure(p) for p in files]
    print("| transcript | lượt | input | cache_read | cache_write | output | ngữ cảnh lớn nhất | quy đổi | bash 90-source |")
    print("|---|---|---|---|---|---|---|---|---|")
    tot = {"luot": 0, "input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "bash_90source": 0}
    ngu_canh_max = 0
    for m in rows:
        print(f"| {m['path']} | {m['luot']} | {m['input']} | {m['cache_read']} | {m['cache_write']} | "
              f"{m['output']} | {m['ngu_canh_max']} | {quy_doi(m):.0f} | {m['bash_90source']} |")
        for k in tot:
            tot[k] += m[k]
        ngu_canh_max = max(ngu_canh_max, m["ngu_canh_max"])
    tong = {**tot, "path": "-", "ngu_canh_max": ngu_canh_max}
    print(f"| **tổng** | {tot['luot']} | {tot['input']} | {tot['cache_read']} | {tot['cache_write']} | "
          f"{tot['output']} | {ngu_canh_max} | {quy_doi(tong):.0f} | {tot['bash_90source']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
