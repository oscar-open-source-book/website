#!/usr/bin/env python3
"""重建 CFP 议题 ↔ 活动页的关联映射（data/cfp_links.json）。

做两件事：
  1. 把 cfp-data/proposals.json 的 64 条议题，与 content/events/*.md 正文里
     出现的议题串做归一化包含匹配；
  2. 输出双向映射，供 CFP 页（议题 → 已分享于哪一站）与活动页
     （{{< cfp-origin >}} 显示本场议题来源）使用。

匹配策略：标题与书名归一化（去空白/标点/大小写）后，
等值或长度≥10 的双向包含。刻意偏保守——宁可漏，不可错配。

用法：
    python3 scripts/build-cfp-links.py            # 重建并写盘
    python3 scripts/build-cfp-links.py --dry-run  # 只打印统计
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVENTS = REPO / "content" / "events"
OUT = REPO / "data" / "cfp_links.json"
CFP_LOCAL = Path.home() / "developing" / "cfp-data" / "proposals.json"


def norm(s: str) -> str:
    s = s.lower()
    return re.sub(r'[\s\-—－_·、，,。.：:；;（）()【】\[\]"“”‘’\'’]', "", s)


def load_proposals() -> list:
    if CFP_LOCAL.exists():
        raw = json.loads(CFP_LOCAL.read_text())
    else:
        url = "https://raw.githubusercontent.com/oscar-open-source-book/cfp-data/main/proposals.json"
        raw = json.loads(subprocess.check_output(["curl", "-sSL", url]))
    return raw["proposals"] if isinstance(raw, dict) else raw


def candidates(body: str) -> set:
    """活动页里可能承载议题的串：书名 + 表格议程单元。"""
    books = re.findall(r"《([^》]{2,60})》", body)
    rows = []
    for line in body.split("\n"):
        if line.count("|") >= 2 and not re.match(r"^\s*\|[:\-\s|]+\|\s*$", line):
            cells = [c.strip().strip("*") for c in line.split("|") if c.strip()]
            rows.extend([c for c in cells if 6 <= len(c) <= 90])
    return set(books) | set(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    proposals = load_proposals()
    cfp_idx = [(norm(p["title"]), p) for p in proposals if len(norm(p["title"])) >= 6]

    event_to_cfp, cfp_to_events = {}, {}
    total_events = 0

    for f in sorted(EVENTS.glob("*.md")):
        total_events += 1
        txt = f.read_text()
        dm = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", txt, re.M)
        if not dm:
            continue
        body = txt.split("---", 2)[2] if txt.count("---") >= 2 else ""
        matched = set()
        for cand in candidates(body):
            nc = norm(cand)
            if len(nc) < 6:
                continue
            for nt, p in cfp_idx:
                if nc == nt or (len(nc) >= 10 and (nc in nt or nt in nc)):
                    matched.add(p["id"])
                    break
        if not matched:
            continue
        event_to_cfp[f.stem] = {"date": dm.group(1), "ids": sorted(matched)}
        for pid in matched:
            cfp_to_events.setdefault(pid, []).append(
                {"slug": f.stem, "date": dm.group(1)}
            )

    print(f"活动页 {total_events} 个，其中 {len(event_to_cfp)} 个能追溯到 CFP")
    print(f"议题 {len(proposals)} 条，其中 {len(cfp_to_events)} 条已落地分享")
    print(f"关联边 {sum(len(v['ids']) for v in event_to_cfp.values())} 条")

    if args.dry_run:
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_from": "cfp-data/proposals.json + content/events/*.md",
                "method": "normalized title/book containment match",
                "event_to_cfp": event_to_cfp,
                "cfp_to_events": cfp_to_events,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"写入 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
