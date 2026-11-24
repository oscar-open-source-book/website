"""2026 年度活动征集海报 · 第一集 — 文字层排版

设计意图：画面（旧木桌 + 三个不同材质的杯子 + 推开的空椅）由 AI 生成，
文字层由本脚本重排。**不让 AI 写文字** —— u1.6-lite 实测两次都拼错
URL（`nosbook.opsntourceway.blog`、`osbook.ownrsourceway.blog`）和
「适兕」（写成「适兄」），所以文字全部在这里逐字放置。

用法：
    python3 scripts/make-annual-poster-ep1.py
    然后再跑 scripts/poster-qr.py 贴二维码

依赖：~/.fonts/shs/SourceHanSerifSC-*.otf（思源宋体，见 docs/poster-series-2026-annual-call-ep1.md）
底图：/tmp/ep1b/ep1b.png（AI 出图，未入库；重出图后改 SRC 即可）
"""
import os
from PIL import Image, ImageDraw, ImageFont

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "static/images/events/2027-01-09-poster-ep1-base.jpg")

W, H = 1760, 2368
FONT = "/home/lee/.fonts/shs/SourceHanSerifSC-{}.otf"

# 品牌色
INK      = (245, 240, 232)   # 暖白（文字主色，深底上）
BRONZE   = (180, 160, 120)   # 古铜
GRAY     = (168, 163, 155)   # 中灰
DIM      = (138, 133, 125)   # 小字灰
BLUE     = (138, 170, 210)   # 浅普鲁士蓝（深底上提亮）

src = "/tmp/ep1b/ep1b.png"
im = Image.open(src).convert("RGB")

# ---------- 1. 只取画面部分（上半，桌面照片），下半自己造纯深底 ----------
# AI 版桌面约占上方 45%（2368*0.45 ≈ 1066），下方文字区重画
SPLIT = 1130
table = im.crop((0, 0, W, SPLIT))

canvas = Image.new("RGB", (W, H), (18, 16, 14))
canvas.paste(table, (0, 0))

# 桌面照片底部向深色过渡（避免硬边）
fade_h = 260
for i in range(fade_h):
    y = SPLIT - fade_h + i
    alpha = i / fade_h
    row = canvas.crop((0, y, W, y + 1))
    dark = Image.new("RGB", (W, 1), (18, 16, 14))
    blended = Image.blend(row, dark, alpha ** 1.6)
    canvas.paste(blended, (0, y))

d = ImageDraw.Draw(canvas)

def font(size, weight="Regular"):
    return ImageFont.truetype(FONT.format(weight), size)

def text(x, y, s, size, color, weight="Regular", tracking=0):
    """tracking: 字间距（像素），逐字绘制"""
    f = font(size, weight)
    if tracking == 0:
        d.text((x, y), s, font=f, fill=color)
        return d.textlength(s, font=f)
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=color)
        cx += d.textlength(ch, font=f) + tracking
    return cx - x

LEFT = 120

# ---------- 2. 文字层 ----------
y = 1232

# 系列标识
text(LEFT, y, "开源之书 · 共读 · 2026 年度", 30, BRONZE, "Medium", tracking=3)
y += 88

# 主问题（最大）
text(LEFT, y, "读书还值得吗", 156, INK, "SemiBold", tracking=8)
y += 214

# 副句
text(LEFT, y, "这个问题，我们留给下一个人来答", 46, GRAY, "Regular", tracking=2)
y += 96

# 分隔线
d.line([(LEFT, y), (LEFT + 560, y)], fill=(70, 66, 60), width=2)
y += 48

# 五年与空缺
text(LEFT, y, "2022 — 2026，五年，每年一月见一次", 40, DIM, "Regular", tracking=1)
y += 56
text(LEFT, y, "第七年的议程，还没人写", 40, DIM, "Regular", tracking=1)
y += 84

# 行动召唤
text(LEFT, y, "征集 2027 年的议题", 60, BLUE, "Medium", tracking=3)
y += 96

# 细节
text(LEFT, y, "2027.01.09 周六 · 北京（场地征集中）", 34, DIM, "Regular", tracking=0)
y += 52
text(LEFT, y, "osbook.opensourceway.blog/cfp", 34, DIM, "Regular", tracking=0)
y += 78

# 署名（左下）
text(LEFT, y, "开源之道 · 适兕 × 窄廊", 32, BRONZE, "Medium", tracking=2)

# ---------- 3. 右下二维码留白框 ----------
QR = 300
qx, qy = W - QR - 120, H - QR - 150
d.rectangle([qx, qy, qx + QR, qy + QR], outline=(60, 56, 50), width=2)

out = "/home/lee/developing/oscar-website/static/images/events/2027-01-09-poster-ep1.png"
canvas.save(out, "PNG", optimize=True)
print("✅", out, canvas.size)
import os
print("大小:", round(os.path.getsize(out)/1024/1024, 2), "MB")