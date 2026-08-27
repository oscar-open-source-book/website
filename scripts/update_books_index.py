#!/usr/bin/env python3
"""osbook books _index.md 动态更新脚本。
在 oscar-open-source-book/website 目录下执行。
只更新数字（书名数量、类别数），保留原有文字排列顺序。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent.parent  # repo root
BOOKS_DIR = HERE / "content" / "books"
INDEX = BOOKS_DIR / "_index.md"

books = sorted(BOOKS_DIR.glob("*.md"))
books = [f for f in books if f.name not in ("_index.md", "category-overview.md")]
count = len(books)

cats = set()
for f in books:
    text = f.read_text(encoding="utf-8")
    parts = text.split("---")
    if len(parts) < 2:
        continue
    for line in parts[1].split("\n"):
        if line.startswith("category:"):
            cats.add(line.split(":", 1)[1].strip().strip('"'))

# "其他" 是隐式兜底类别，不列入显式命名类别
named_cats = {c for c in cats if c != "其他"}
cat_count = len(named_cats)

text = INDEX.read_text(encoding="utf-8")
text = re.sub(r"共收录 \*\*\d+\*\* 本", f"共收录 **{count}** 本", text)
text = re.sub(r"涵盖 \*\*\d+\*\* 个类别", f"涵盖 **{cat_count}** 个类别", text)
text = re.sub(r"\d+个分类", f"{cat_count}个分类", text)

INDEX.write_text(text, encoding="utf-8")
print(f"✅ books: {count}, named categories: {cat_count} ({', '.join(sorted(named_cats))})")