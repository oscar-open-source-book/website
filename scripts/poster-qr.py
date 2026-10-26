#!/usr/bin/env python3
"""
poster-qr.py — 把二维码融进海报，而不是贴上去。

设计原则：
  1. 极性正确 —— 必须「浅底 + 深模块」。实测 cv2/微信/支付宝的检测器
     不认「深底 + 浅模块」（反转极性），所以底色是浅的、模块是深的。
  2. 色相取自海报 —— 深色端取画面夜色/墨色，浅色端取标题暖白/米金，
     两端都来自海报本身，不引入外来色。
  3. 位置自适应 —— 自动在候选角里挑最平坦的，并逐个尝试直到解码通过。
  4. 不留贴纸感 —— 圆角 + 细描边 + 无外投影，压在海报上像原设计的一枚印记。
  5. 交付前自检 —— cv2 解码，扫不出就换位置重试，全失败则非 0 退出。

用法：
  python3 poster-qr.py poster.png "https://example.com"

  # 显式指定配色（两个色都从海报里取）
  python3 poster-qr.py poster.png URL --dark '#16212A' --light '#F0EADA'

  python3 poster-qr.py --help
"""
import argparse
import statistics
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw


ANCHORS = {
    "bottom-right": ("right", "bottom"),
    "bottom-left":  ("left",  "bottom"),
    "top-right":    ("right", "top"),
    "top-left":     ("left",  "top"),
    # 底部中央：海报常把署名/副标题放在这条带上，两侧留白适合放码
    "footer-right": ("right", "footer"),
    "footer-left":  ("left",  "footer"),
}


def hex_to_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def sample_dark(im, box):
    """从区域里取「深色端」——画面本身的夜色/墨色。"""
    px = list(im.crop(box).convert("RGB").getdata())
    dark = sorted(px, key=_lum)[: max(1, len(px) // 12)]
    r = int(statistics.median(c[0] for c in dark))
    g = int(statistics.median(c[1] for c in dark))
    b = int(statistics.median(c[2] for c in dark))
    # 压到足够深，保证与浅底对比够
    mx = max(r, g, b)
    if mx > 60:
        k = 42 / mx
        r, g, b = int(r * k), int(g * k), int(b * k)
    return (max(0, r), max(0, g), max(0, b))


def sample_light(im, box):
    """从区域里取「浅色端」——画面本身的暖白/米金。"""
    px = list(im.crop(box).convert("RGB").getdata())
    light = sorted(px, key=_lum)[-max(1, len(px) // 8):]
    r = int(statistics.median(c[0] for c in light))
    g = int(statistics.median(c[1] for c in light))
    b = int(statistics.median(c[2] for c in light))
    # 抬到接近米白，同时保留一点点暖偏
    warm = max(0, r - b)
    if warm > 40:
        warm = 40
    return (
        min(255, max(225, r if r > 225 else 238)),
        min(255, max(218, g if g > 218 else 231)),
        min(255, max(205, (238 - warm))),
    )


def flatness(im, box):
    lum = [_lum(c) for c in im.crop(box).convert("RGB").getdata()]
    return statistics.pstdev(lum), statistics.mean(lum)


def accent_gold(im, box):
    """从画面里取「古铜金」——用于二维码面板描边，与树根/标题的暖光同源。"""
    px = list(im.crop(box).convert("RGB").getdata())
    golds = []
    for c in px:
        r, g, b = c
        if r >= g > b and r > b + 25 and (max(c) - min(c)) > 25:
            golds.append(c)
    if not golds:
        golds = [c for c in px if sum(c) > 200] or px
    r = int(statistics.median(c[0] for c in golds))
    g = int(statistics.median(c[1] for c in golds))
    b = int(statistics.median(c[2] for c in golds))
    # 提亮成明确的古铜金，保证在深色底上可见
    mx = max(r, g, b) or 1
    if mx < 150:
        k = 168 / mx
        r, g, b = min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k))
    return (r, g, b)


def anchor_xy(W, H, size, margin, anchor):
    """把锚点换成左上角坐标。footer-* 指底部条带（画面下方 12% 区域内）。"""
    h_side, v_side = ANCHORS[anchor]
    x = margin if h_side == "left" else W - size - margin
    if v_side == "top":
        y = margin
    elif v_side == "footer":
        y = H - int(H * 0.12) - size // 2
    else:  # bottom
        y = H - size - margin
    return max(0, x), max(0, y)


def ink_density(im, box):
    """区域内的「笔画密度」——高亮细纹理越多，越可能是文字/标题。

    文字的特征：大量接近亮色的细笔画与暗底混排，亮度标准差高，
    且高亮像素占比在 3%~35% 之间（纯图形不会有这种分布）。
    """
    lum = [_lum(c) for c in im.crop(box).convert("RGB").getdata()]
    if not lum:
        return 0.0
    lo, hi = min(lum), max(lum)
    if hi - lo < 1:
        return 0.0
    thr = lo + (hi - lo) * 0.72
    bright = sum(1 for v in lum if v > thr) / len(lum)
    # 3%~40% 的亮像素占比最像文字
    if 0.03 <= bright <= 0.40:
        return bright
    return 0.0


def build_qr(url, dark, light, target_size=300):
    """生成刚好落在 target_size 的二维码。

    两个硬约束（实测）：
      • border 必须 ≥1 —— border=0 缺静区，任何缩放都救不回来
      • 用整数 box_size 生成再缩放，比直接 resize 到任意尺寸可靠
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    modules = qr.modules_count + 2  # 含 border=1 静区
    # 取使总尺寸 ≤ target 的最大整数 box_size
    box = max(1, target_size // modules)
    qr2 = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=box, border=1)
    qr2.add_data(url)
    qr2.make(fit=True)
    img = qr2.make_image(fill_color=dark, back_color=light).convert("RGB")
    if img.size[0] != target_size:
        img = img.resize((target_size, target_size), Image.NEAREST)
    return img


def compose(im, qr_img, size, margin, anchor, radius, quiet, frame=None):
    """把二维码贴上去。

    frame=None 时只画圆角面板；给一个 RGB 则额外描一圈细边，
    让面板看起来像海报上原有的铭牌，而不是外来的白色贴纸。
    """
    W, H = im.size
    x, y = anchor_xy(W, H, size, margin, anchor)

    q = qr_img if qr_img.size == (size, size) else qr_img.resize((size, size), Image.NEAREST)
    total = size + quiet * 2

    panel = Image.new("RGB", (total, total), qr_img.getpixel((0, 0)))
    panel.paste(q, (quiet, quiet))

    base = im.copy()
    mask = Image.new("L", (total, total), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, total - 1, total - 1], radius=radius, fill=255)
    base.paste(panel, (x - quiet, y - quiet), mask)

    if frame:
        d = ImageDraw.Draw(base)
        d.rounded_rectangle(
            [x - quiet, y - quiet, x - quiet + total - 1, y - quiet + total - 1],
            radius=radius, outline=frame, width=2)
    return base, (x, y, size, size)


def decode_check(path, expect, scales=(0.5,)):
    """解码自检。

    不只测原图 —— 海报在手机上会整屏缩放显示，
    实际扫码时相当于缩小后的图。按 scales 逐个缩放再解码。
    """
    try:
        import cv2
    except ImportError:
        return None, "cv2 未安装，跳过解码自检"
    img = cv2.imread(str(path))
    if img is None:
        return False, "读图失败"

    det = cv2.QRCodeDetector()
    data, _, _ = det.detectAndDecode(img)
    if not data:
        return False, "原图未识别到二维码"
    if data.strip() != expect.strip():
        return False, f"内容不符：{data[:60]}"

    h, w = img.shape[:2]
    for sc in scales:
        small = cv2.resize(img, (max(1, int(w * sc)), max(1, int(h * sc))),
                           interpolation=cv2.INTER_AREA)
        d, _, _ = det.detectAndDecode(small)
        if d.strip() != expect.strip():
            return False, f"缩放到 {int(sc*100)}% 后扫不出（手机整屏显示时会失败）"
    return True, data


def main():
    ap = argparse.ArgumentParser(
        description="把二维码融进海报（取色 / 自适应位置 / 解码自检）")
    ap.add_argument("poster", help="海报图片路径")
    ap.add_argument("url", help="二维码指向的 URL")
    ap.add_argument("-o", "--out", default=None, help="输出路径")
    ap.add_argument("--dark", default=None,
                    help="模块颜色 #RRGGBB；不填则从海报深色端自动取")
    ap.add_argument("--light", default=None,
                    help="底色 #RRGGBB；不填则从海报浅色端自动取")
    ap.add_argument("--size", type=int, default=320,
                    help="二维码边长像素（默认 320；实测 320 在 50%% 缩放下仍可扫）")
    ap.add_argument("--margin", type=int, default=60, help="距海报边缘像素（默认 60）")
    ap.add_argument("--anchor", default="auto", choices=list(ANCHORS) + ["auto"],
                    help="落点；auto 自动挑最平坦的角并逐个试到可扫（默认 auto）")
    ap.add_argument("--radius", type=int, default=10, help="圆角半径（默认 10，0=直角）")
    ap.add_argument("--quiet", type=int, default=16, help="静区宽度（默认 16）")
    ap.add_argument("--frame", nargs="?", const="auto", default="auto",
                    help="面板描边颜色；auto=取海报古铜金，none=不描边")
    ap.add_argument("--scales", default="0.5",
                    help="自检时额外验证的缩放比，逗号分隔（默认 0.5；空=只测原图）")
    ap.add_argument("--no-verify", action="store_true", help="跳过解码自检")
    args = ap.parse_args()

    src = Path(args.poster)
    if not src.exists():
        sys.exit(f"❌ 海报不存在：{src}")
    im = Image.open(src).convert("RGB")
    W, H = im.size
    size, margin = args.size, args.margin

    # ── 决定候选顺序 ──
    if args.anchor == "auto":
        scored = []
        for a in ANCHORS:
            x, y = anchor_xy(W, H, size, margin, a)
            box = (x, y, x + size, y + size)
            sd, mean = flatness(im, box)
            ink = ink_density(im, box)
            # 文字区重罚 —— 宁可压暗画面也不遮标题
            score = sd + max(0, mean - 110) * 0.5 + ink * 400
            scored.append((score, a, sd, mean, ink))
        scored.sort()
        for score, a, sd, mean, ink in scored:
            flag = "  ⚠️疑似文字" if ink > 0.02 else ""
            print(f"  候选 {a:14} 标准差 {sd:5.1f}  均值 {mean:6.1f}  "
                  f"文字密度 {ink:.3f}  评分 {score:6.1f}{flag}")
        order = [s[1] for s in scored]
        print(f"→ 尝试顺序：{' → '.join(order)}")
    else:
        order = [args.anchor]

    out = Path(args.out) if args.out else src.with_name(src.stem + "-qr.png")
    last = ""
    for i, anchor in enumerate(order):
        x, y = anchor_xy(W, H, size, margin, anchor)
        box = (x, y, x + size, y + size)

        dark = hex_to_rgb(args.dark) if args.dark else sample_dark(im, box)
        light = hex_to_rgb(args.light) if args.light else sample_light(im, box)

        qr_img = build_qr(args.url, dark, light, size)
        if args.frame and args.frame.lower() != "none":
            if args.frame == "auto":
                frame = accent_gold(im, (x, y, x + size, y + size))
            else:
                frame = hex_to_rgb(args.frame)
        else:
            frame = None
        result, rect = compose(im, qr_img, size, margin, anchor,
                               args.radius, args.quiet, frame)
        result.save(out, quality=95)

        if args.no_verify:
            ok, msg = None, "已跳过"
        else:
            sc = tuple(float(v) for v in args.scales.split(",") if v.strip())
            ok, msg = decode_check(out, args.url, sc)
        dh = f"#{dark[0]:02X}{dark[1]:02X}{dark[2]:02X}"
        lh = f"#{light[0]:02X}{light[1]:02X}{light[2]:02X}"

        if ok is False:
            last = msg
            more = "（换下一个候选）" if i < len(order) - 1 else "（无更多候选）"
            print(f"  ✗ {anchor} {dh}/{lh} 解码失败：{msg}{more}")
            continue

        print(f"→ 落点 {anchor}  x={rect[0]} y={rect[1]}  {size}x{size}px")
        print(f"→ 模块 {dh}（{'指定' if args.dark else '取自海报深色端'}）")
        print(f"→ 底色 {lh}（{'指定' if args.light else '取自海报浅色端'}）")
        print(f"✅ 已生成 {out}")
        if ok:
            print(f"✅ 解码自检通过：{msg}")
        elif ok is None:
            print(f"⚠️  {msg}")
        return

    print(f"❌ 所有候选位置解码均失败（最后错误：{last}）", file=sys.stderr)
    print("   建议：加大 --size、加大 --quiet、或显式指定 --dark/--light",
          file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
