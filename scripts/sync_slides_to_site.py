#!/usr/bin/env python3
"""
sync_slides_to_site.py — 把 kanban batch 生成的 slides-src/<deck>/pages/*.html
同步到 Hugo 站（static/slides/ + content/slides/<deck>.md）。

命名策略：
  - 现有 .md 的 slides_deck_id 可能是 src_id（带 YYYY-MM 前缀）或 canonical_id
  - 脚本只给「已有 .md 都覆盖不到」的 deck 生成新 .md，用 canonical_id 命名
  - 已存在的 .md 一律保留，不覆盖（避免破坏用户手动调整）

流程：
  1. 扫 slides-src/ 找有 pages/page_*.html 的 deck
  2. 按 canonical_id 去重（YYYY-MM 前缀归一化），取 slide 数最多的
  3. 过滤：跳过 slide 数 < 5 的 partial
  4. 复制：slides-src/<src_dir>/pages/*.html → static/slides/<target_id>/pages/*.html
     target_id 选择：
       - 如果已有 .md 的 slides_deck_id == src_id → 用 src_id
       - 如果已有 .md 的 slides_deck_id == canonical_id → 用 canonical_id
       - 否则用 canonical_id（新 deck）
  5. 生成 .md（仅当 target_id 无对应 .md 时）

用法：
  python3 scripts/sync_slides_to_site.py          # 全量同步
  python3 scripts/sync_slides_to_site.py --dry    # 只打印要做的
  python3 scripts/sync_slides_to_site.py --force  # 强制重生成已存在的 .md
"""
import json
import shutil
import sys
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "slides-src"
STATIC = ROOT / "static" / "slides"  # 统一用 static/slides/
CONTENT = ROOT / "content" / "slides"

MIN_SLIDES = 5  # 低于这个数不生成 .md（partial）


def deck_slide_count(deck_dir: Path) -> int:
    """数 pages/page_*.html 的数量"""
    pages_dir = deck_dir / "pages"
    if not pages_dir.is_dir():
        return 0
    return len(list(pages_dir.glob("page_*.html")))


def canonicalize_deck_id(deck_id: str) -> str:
    """
    规范化 deck_id：去掉 YYYY-MM 或 YYYY-M- 前缀。
    例：'2024-01-linus-troavlds-quotes' -> 'linus-troavlds-quotes'
    用于去重：同一 deck 的多个候选目录归一化后 key 相同。
    """
    return re.sub(r"^\d{4}-\d{1,2}-", "", deck_id)


def parse_deck_id_date(deck_id: str) -> str:
    """
    从 deck_id 前缀提取日期：
      '2024-04-protect-virtual-commons' -> '2024-04-01'
      '36-open-source-books-meaning'    -> today
    """
    m = re.match(r"^(\d{4})-(\d{2})-", deck_id)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    return date.today().isoformat()


def extract_title(deck_dir: Path) -> str:
    """
    从 outline.json 的 cover slide 提取 title，fallback 用 deck_id。
    """
    outline_path = deck_dir / "outline.json"
    if outline_path.exists():
        try:
            d = json.load(open(outline_path))
            pages = d.get("pages", [])
            for p in pages:
                if p.get("page_kind") == "cover":
                    t = p.get("title", "").strip()
                    if t:
                        return t
                elif p.get("title"):
                    return p["title"].strip()
        except Exception as e:
            print(f"  [warn] {deck_dir.name}: outline.json parse failed: {e}")
    return ""


def collect_existing_deck_ids() -> set:
    """收集所有已有 .md 的 slides_deck_id（避免命名冲突）"""
    ids = set()
    for f in CONTENT.glob("*.md"):
        if f.name == "_index.md":
            continue
        try:
            t = f.read_text(encoding="utf-8")
            m = re.search(r'slides_deck_id:\s*"([^"]+)"', t)
            if m:
                ids.add(m.group(1))
        except Exception:
            pass
    return ids


def pick_target_id(src_id: str, canonical_id: str, existing_ids: set) -> str:
    """
    决定目标 id（作为 static/slides/<id>/ 目录名和 content/slides/<id>.md 文件名）：
      1. 如果 src_id 已在 existing_ids → 用 src_id（保留现有命名）
      2. 如果 canonical_id 已在 existing_ids → 用 canonical_id（保留现有命名）
      3. 否则 → 用 canonical_id（新 deck，去重）
    """
    if src_id in existing_ids:
        return src_id
    if canonical_id in existing_ids:
        return canonical_id
    return canonical_id


def sync_deck(deck_dir: Path, existing_ids: set, dry_run: bool = False, force: bool = False) -> dict:
    """
    同步单个 deck。
    返回 {'src', 'deck_id', 'slides', 'html_copied', 'md_created'}
    """
    src_id = deck_dir.name
    canonical = canonicalize_deck_id(src_id)
    target_id = pick_target_id(src_id, canonical, existing_ids)
    slides = deck_slide_count(deck_dir)

    result = {
        "src": src_id, "deck_id": target_id, "slides": slides,
        "html_copied": 0, "md_created": False, "skipped": False,
    }

    if slides < MIN_SLIDES:
        result["skipped"] = True
        return result

    # 1. 复制 pages/, images/, assets/ 到 static/slides/<target_id>/
    static_deck = STATIC / target_id
    static_deck.mkdir(parents=True, exist_ok=True)
    for sub in ["pages", "images", "assets"]:
        src_sub = deck_dir / sub
        if not src_sub.is_dir():
            continue
        for f in src_sub.iterdir():
            if f.is_file():
                dst = static_deck / sub / f.name
                if not dst.exists():
                    if not dry_run:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dst)
                    result["html_copied"] += 1

    # 2. 生成 content/slides/<target_id>.md
    md_path = CONTENT / f"{target_id}.md"
    if md_path.exists() and not force:
        result["md_created"] = "exists"
        return result

    title = extract_title(deck_dir) or target_id
    deck_date = parse_deck_id_date(src_id)
    # weight: 用 -date 让 2024 年靠前；无日期前缀用 50
    m = re.match(r"^(\d{4})-(\d{2})-", src_id)
    if m:
        ym = int(f"{m.group(1)}{m.group(2)}")
        weight = max(1, 202609 - ym)
    else:
        weight = 50

    md_content = f"""---
title: "{title}"
date: {deck_date}
type: slides
slides_deck_id: "{target_id}"
slides_count: {slides}
weight: {weight}
---
"""

    if not dry_run:
        CONTENT.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md_content, encoding="utf-8")
        # 加入 existing_ids，避免后续 deck 用同 id
        existing_ids.add(target_id)
    result["md_created"] = True
    return result


def main():
    dry_run = "--dry" in sys.argv
    force = "--force" in sys.argv

    if not SRC.is_dir():
        print(f"ERROR: {SRC} not found")
        sys.exit(1)

    CONTENT.mkdir(parents=True, exist_ok=True)

    existing_ids = collect_existing_deck_ids()
    print(f"已有 .md 覆盖的 deck_id: {len(existing_ids)} 个\n")

    # 扫所有 deck 目录，按 canonical_id 去重（取 slide 数最多的）
    candidates = {}
    total_dirs = 0
    for d in SRC.iterdir():
        total_dirs += 1
        if not d.is_dir() or not (d / "pages").is_dir():
            continue
        n = deck_slide_count(d)
        cid = canonicalize_deck_id(d.name)
        if cid not in candidates or n > candidates[cid][1]:
            candidates[cid] = (d, n)

    decks = [v[0] for v in candidates.values()]
    print(f"扫到 {total_dirs} 个 slides-src 目录，去重后 {len(decks)} 个 deck（按 canonical_id）\n")

    synced = 0
    skipped_partial = 0
    skipped_empty = 0
    html_copied_total = 0
    md_created_total = 0
    md_exists_total = 0

    for deck_dir in sorted(decks, key=lambda d: canonicalize_deck_id(d.name)):
        r = sync_deck(deck_dir, existing_ids, dry_run=dry_run, force=force)
        if r["skipped"]:
            if r["slides"] == 0:
                skipped_empty += 1
            else:
                skipped_partial += 1
            print(f"  [skip] {r['src']}: {r['slides']} slides (partial)")
            continue

        synced += 1
        html_copied_total += r["html_copied"]
        if r["md_created"] is True:
            md_created_total += 1
        elif r["md_created"] == "exists":
            md_exists_total += 1

        md_status = {True: "NEW", False: "none", "exists": "exists"}.get(r["md_created"], str(r["md_created"]))
        suffix = f" (src={r['src']})" if r["src"] != r["deck_id"] else ""
        print(f"  [sync] {r['deck_id']}{suffix}: {r['slides']} slides, {r['html_copied']} files copied, md={md_status}")

    print(f"\n{'='*60}")
    print(f"{'[DRY RUN]' if dry_run else ''}同步完成：")
    print(f"  成功同步: {synced} 个 deck")
    print(f"  partial 跳过: {skipped_partial}")
    print(f"  空 pages 跳过: {skipped_empty}")
    print(f"  HTML/资源文件复制: {html_copied_total}")
    print(f"  新创建 .md: {md_created_total}")
    print(f"  已存在 .md: {md_exists_total}")


if __name__ == "__main__":
    main()
