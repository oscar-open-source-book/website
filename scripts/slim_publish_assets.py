#!/usr/bin/env python3
"""
Slim Hugo publish assets before upload-pages-artifact.

This is intentionally conservative:
- keeps existing historical slides-src and .git data untouched
- reduces only local public/ copies after Hugo has generated them
- uses one shared vendored echarts.min.js instead of per-deck duplicates
- keeps behavior simple so small future updates do not need repo surgery
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
STATIC = ROOT / "static"


def dedupe_echarts() -> int:
    """Copy one echarts.min.js into public/vendor, rewrite slide HTML refs."""
    if not PUBLIC.exists():
        return 0

    vendor = PUBLIC / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    target = vendor / "echarts.min.js"
    source = None
    local_candidates = list((STATIC / "slides").rglob("echarts.min.js"))
    if local_candidates:
        source = local_candidates[0]
        shutil.copy2(source, target)

    if not target or not target.exists():
        return 0

    count = 0
    for html in PUBLIC.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "echarts.min.js" not in text:
            continue
        new_text = text.replace('src="../assets/echarts.min.js"', 'src="/vendor/echarts.min.js"')
        new_text = new_text.replace('src="../../assets/echarts.min.js"', 'src="/vendor/echarts.min.js"')
        if new_text != text:
            html.write_text(new_text, encoding="utf-8")
            count += 1
    return count


def remove_duplicate_echarts() -> int:
    removed = 0
    for path in list((PUBLIC / "slides").rglob("echarts.min.js")) if (PUBLIC / "slides").exists() else []:
        path.unlink(missing_ok=True)
        removed += 1
    return removed


def main() -> None:
    print(f"[slim] public exists: {PUBLIC.exists()}")
    if PUBLIC.exists():
        print(f"[slim] public size before: {sum(f.stat().st_size for f in PUBLIC.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MiB")

    deduped = dedupe_echarts()
    removed = remove_duplicate_echarts()
    if PUBLIC.exists():
        size_after = sum(f.stat().st_size for f in PUBLIC.rglob('*') if f.is_file()) / 1024 / 1024
        print(f"[slim] rewrote {deduped} HTML files; removed {removed} duplicate echarts copies")
        print(f"[slim] public size after: {size_after:.1f} MiB")


if __name__ == "__main__":
    main()
