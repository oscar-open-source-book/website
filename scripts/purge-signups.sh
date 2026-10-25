#!/usr/bin/env bash
#
# purge-signups.sh — 活动结束后清理报名数据
# ============================================
# 报名数据分两处存放，本脚本同时清理：
#   ① 私密库（8.211.12.147:/home/lee/oscar-signups/<event>.jsonl）
#   ② 公开 JSON（oscar-website/static/signups/<event>.json）
#
# 用法：
#   bash scripts/purge-signups.sh 2026-10-31          # 预览（不删）
#   bash scripts/purge-signups.sh 2026-10-31 --force  # 真的删
#   bash scripts/purge-signups.sh --list              # 列出所有报名数据
#
set -euo pipefail

REMOTE="8.211.12.147"
PRIVATE_DIR="/home/lee/oscar-signups"
PUBLIC_DIR="/home/lee/developing/oscar-website/static/signups"

EVENT="${1:-}"
FORCE=0
[[ "${2:-}" == "--force" ]] && FORCE=1

if [[ "$EVENT" == "--list" || -z "$EVENT" ]]; then
  echo "=== 私密库（$REMOTE:$PRIVATE_DIR）==="
  ssh -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE" \
    "ls -la $PRIVATE_DIR 2>/dev/null | grep -v '^total' || echo '  (空)'"
  echo
  echo "=== 公开 JSON（$PUBLIC_DIR）==="
  ls -la "$PUBLIC_DIR" 2>/dev/null | grep -v '^total' || echo "  (空)"
  echo
  echo "用法: bash scripts/purge-signups.sh <event> [--force]"
  exit 0
fi

PRIV_FILE="$PRIVATE_DIR/$EVENT.jsonl"
PUB_FILE="$PUBLIC_DIR/$EVENT.json"

echo "=== 待清理: $EVENT ==="
PRIV_LINES=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE" \
  "wc -l < $PRIV_FILE 2>/dev/null || echo 0" | tr -d ' ')
PRIV_SIZE=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$REMOTE" \
  "du -h $PRIV_FILE 2>/dev/null | cut -f1 || echo '-'" | tr -d ' ')

if [[ -f "$PUB_FILE" ]]; then
  PUB_COUNT=$(grep -c '"signup_no"' "$PUB_FILE" 2>/dev/null || echo 0)
else
  PUB_COUNT=0
fi

echo "  私密库: $PRIV_FILE"
echo "          行数 $PRIV_LINES / 大小 $PRIV_SIZE"
echo "  公开档: $PUB_FILE"
echo "          报名条数 $PUB_COUNT"

if [[ "$PRIV_LINES" == "0" && "$PUB_COUNT" == "0" ]]; then
  echo "  → 无需清理"
  exit 0
fi

if [[ $FORCE -eq 0 ]]; then
  echo
  echo "⚠️  预览模式，未删除。确认无误后加 --force 执行："
  echo "   bash scripts/purge-signups.sh $EVENT --force"
  exit 0
fi

echo
echo "=== 执行删除 ==="

# ① 私密库：先备份到本地 /tmp 再删（防误删，7 天后可人工清）
BACKUP="/home/lee/.hermes/backups/signups-$EVENT-$(date +%Y%m%d_%H%M%S).jsonl"
mkdir -p "$(dirname "$BACKUP")"
if ssh -o BatchMode=yes "$REMOTE" "cat $PRIV_FILE 2>/dev/null" > "$BACKUP" 2>/dev/null && [[ -s "$BACKUP" ]]; then
  echo "  ✅ 私密库已备份至 $BACKUP"
  ssh -o BatchMode=yes "$REMOTE" "rm -f $PRIV_FILE" && echo "  ✅ 私密库已删除"
else
  echo "  ⚠️  备份失败或文件为空，跳过删除私密库（请人工确认）"
fi

# ② 公开 JSON：清空 signups 数组，保留文件结构
if [[ -f "$PUB_FILE" ]]; then
  python3 - "$PUB_FILE" "$EVENT" <<'PY'
import json, sys
path, event = sys.argv[1], sys.argv[2]
with open(path, encoding='utf-8') as f:
    d = json.load(f)
d['signups'] = []
d['updated'] = None
with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"  ✅ 公开 JSON 已清空（{path}）")
PY
  cd /home/lee/developing/oscar-website
  git add "static/signups/$EVENT.json"
  git commit -q -m "chore(signups): 活动结束，清理 $EVENT 报名数据" 2>/dev/null \
    && git push origin main >/dev/null 2>&1 \
    && echo "  ✅ 公开 JSON 已提交推送"
fi

echo
echo "✅ $EVENT 报名数据清理完成"
[[ -f "$BACKUP" ]] && echo "   备份保留在: $BACKUP（确认无误后可删除）"
