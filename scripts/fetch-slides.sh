#!/usr/bin/env bash
#
# fetch-slides.sh — 构建时拉取幻灯片资源
# =========================================
# slides 已分离到 oscar-open-source-book/slides 仓库。
# 本脚本在 Hugo 构建前把 static/slides 拉回工作区。
#
# 设计要点：
#   1. 用 tarball 而非 git clone —— 不携带历史，下载量最小
#   2. 已存在则跳过（本地开发不用重复下载）
#   3. 校验关键文件，避免下载不完整导致构建产物残缺
#   4. 支持 GitHub Actions（GITHUB_TOKEN）和本地（gh auth token）
#
# 用法：
#   bash scripts/fetch-slides.sh           # 拉取（已存在则跳过）
#   bash scripts/fetch-slides.sh --force   # 强制重新拉取
#   SKIP_SLIDES=1 hugo build               # 跳过 slides（仅调试内容时）
#
set -euo pipefail

REPO="oscar-open-source-book/slides"
BRANCH="${SLIDES_BRANCH:-main}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$ROOT/static/slides"
MARKER="$TARGET/.slides-version"

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

if [[ "${SKIP_SLIDES:-0}" == "1" ]]; then
  echo "⏭  SKIP_SLIDES=1，跳过幻灯片拉取"
  exit 0
fi

# 已存在且非空 → 跳过（本地开发常见）
if [[ $FORCE -eq 0 && -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
  COUNT=$(find "$TARGET" -maxdepth 1 -mindepth 1 -type d | wc -l)
  echo "✅ static/slides 已存在（${COUNT} 个 deck），跳过下载"
  echo "   如需强制刷新：bash scripts/fetch-slides.sh --force"
  exit 0
fi

echo "📦 从 $REPO@$BRANCH 拉取幻灯片资源..."

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
CURL_OPTS=(-fsSL --retry 3 --retry-delay 5 --connect-timeout 20)

# GitHub Actions 内可用 GITHUB_TOKEN 提高速率限制
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  CURL_OPTS+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

if ! curl "${CURL_OPTS[@]}" -o "$TMP/slides.tar.gz" "$URL"; then
  echo "❌ 下载失败：$URL" >&2
  exit 1
fi

SIZE=$(du -h "$TMP/slides.tar.gz" | cut -f1)
echo "   已下载 $SIZE，正在解压..."

tar xzf "$TMP/slides.tar.gz" -C "$TMP"

# tarball 解出的顶层目录名形如 slides-main
SRC="$(find "$TMP" -maxdepth 1 -mindepth 1 -type d -name 'slides-*' | head -1)"
if [[ -z "$SRC" || ! -d "$SRC/static/slides" ]]; then
  echo "❌ 解压后未找到 static/slides，目录结构异常" >&2
  exit 1
fi

mkdir -p "$ROOT/static"
if [[ -d "$TARGET" ]]; then
  rm -rf "$TARGET"
fi
mv "$SRC/static/slides" "$TARGET"

DECK_COUNT=$(find "$TARGET" -maxdepth 1 -mindepth 1 -type d | wc -l)

# 完整性校验：至少 50 个 deck，且存在已知样例
if [[ "$DECK_COUNT" -lt 50 ]]; then
  echo "❌ 校验失败：只找到 ${DECK_COUNT} 个 deck（预期 ≥50）" >&2
  exit 1
fi

if [[ ! -d "$TARGET/2020-summary-and-new-rules/pages" ]]; then
  echo "❌ 校验失败：样例 deck 2020-summary-and-new-rules/pages 缺失" >&2
  exit 1
fi

echo "${REPO}@${BRANCH} $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$MARKER"

echo "✅ 完成：${DECK_COUNT} 个 deck 已就位（$(du -sh "$TARGET" | cut -f1)）"
