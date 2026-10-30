# 「OSCAR·开源之书·共读」北京站 · 2026-10-31 最终海报提示词

> 生成日期：2026-10-30 ／ 修订：2026-10-31（放开中文限制）
> 活动页：https://osbook.opensourceway.blog/events/2026-10-31-beijing-reading-meetup/
> 报名页：https://osbook.opensourceway.blog/signup/2026-10-31/
> 二维码：`https://osbook.opensourceway.blog/images/events/2026-10-31-signup-qr.png`
> （900×900，41 模块，ERROR_CORRECT_H，border=4 静区 — 已上线，实测 200）

**修订说明**：此前「中文交给 AI 必错、一律后期叠加」是几个月前的经验，已过期。
ChatGPT Image 2 的中文渲染已可用，本版**把中文直接写进提示词**，
让 AI 一次出成品，而不是出底图再手工排版。

---

## 一、本次活动的全部确定信息（海报文案的唯一来源）

| 项 | 内容 |
|---|---|
| **品牌** | 「OSCAR·开源之书·共读」 |
| **主标语** | 三十五载的自发秩序 |
| **副标语** | 当生成的成本趋近于零，共识与信任靠什么建立？ |
| **时间** | 2026.10.31（周六）· 13:30 签到，14:00 开始 |
| **地点** | 智源大厦 · 北京市海淀区成府路 150 号楼 |
| **策划** | 王厚 |
| **署名** | 开源之道 · 适兕 × 窄廊 |
| **联合支持** | 「开源之法与经济」、CCF ODTC |
| **场地赞助** | 智源 |
| **咖啡/小食** | 王厚 / 振华 |

### 议程（海报若放议程，用这个压缩版）

```
13:30  签到 · Network
14:00  三十五载的自发秩序 —— Linux Kernel 35 周年报告解读
15:30  开源项目是否是 Public good？治理与法理视角的博弈
16:00  场域与权力：布迪厄能给开源分析什么？（唯真）
17:00  COSCon'26 阅读 BoF 策划探讨
17:15  拍照合影
18:00  简易晚餐 · Social
```

---

## 二、视觉方向：主推「书与地基」

**为什么是它**：这次议程从三节扩到五节，多了「场域与权力」。所以海报不该只讲「一个项目活了很久」，而该讲——**一段长时间被守住的协作，与它背后不可见的权力结构。**

书是可见的部分，地基是不可见但决定一切的部分。这正是「自发秩序」的视觉化。

### 版面结构（3:4 竖版，AI 直接出成品）

```
┌─────────────────────────┐
│  OSCAR · 开源之书 · 共读   │  顶部品牌（小字，字距拉开）
│                         │
│   ┌─────────────────┐   │
│   │  书 + 混凝土地基    │   │  画面主区（约 45%）
│   │  （暖光自左上斜射）  │   │
│   └─────────────────┘   │
│                         │
│   三十五载的自发秩序        │  主标题（最大）
│   当生成的成本趋近于零，      │  副标语
│   共识与信任靠什么建立？      │
│                         │
│   2026.10.31 周六         │
│   13:30 签到 · 14:00 开始  │
│   智源大厦（成府路 150 号楼） │
│                         │
│   ┌────┐  扫码报名        │  二维码区（后期贴真图）
│   └────┘                │
│                         │
│  开源之道 · 适兕 × 窄廊      │  署名
│  联合支持：「开源之法与经济」、 │
│  CCF ODTC               │
└─────────────────────────┘
```

---

## 三、主推提示词（方案 A · 书与地基）

```
Create a vertical event poster, 3:4 aspect ratio, print quality.

=== VISUAL ===
A used hardcover book lying flat on a thick rough concrete slab. The slab is
part of a building's foundation — weathered edges, visible aggregate, hairline
cracks, board-formed texture. The book is open to a page of dense printed text,
pages slightly yellowed, spine cracked from use. A single thin shaft of warm
late-afternoon light rakes across the page from the upper left, revealing paper
fiber texture and fine dust motes in the air.

The book and concrete occupy the upper 45% of the poster, the book slightly
off-center to the right. Below it the concrete continues into deep, calm shadow —
a quiet zone where typography sits. Keep that lower area uncluttered: no extra
objects, no decoration, no busy texture.

Mood: quiet, patient, institutional weight. Something built slowly that is still
holding. Not nostalgic, not celebratory. No people, no hands, no faces.

Palette: warm off-white paper #F5F0E8, cold gray concrete, one amber light
accent, deep near-black shadow, subtle deep Prussian blue #1B3B6B in the cool
shadows.

Style: photorealistic editorial photography, medium format, 50mm lens at f/2.8,
natural light only, no glossy post-processing, fine film grain.

=== TYPOGRAPHY (render exactly, Simplified Chinese) ===
Render all text below in correct Simplified Chinese. Use a refined Chinese serif
typeface (Source Han Serif / Noto Serif CJK style). Clean kerning, generous line
height, left-aligned in the lower half.

Top edge, small, wide letter-spacing, antique bronze #B4A078:
  OSCAR · 开源之书 · 共读

Main title, largest, deep ink #2C2A26:
  三十五载的自发秩序

Subtitle, medium, muted gray #6B6B6B:
  当生成的成本趋近于零，共识与信任靠什么建立？

Details, small, dark gray:
  2026.10.31 周六 · 13:30 签到 · 14:00 开始
  智源大厦 · 北京市海淀区成府路 150 号楼

Bottom left, small, antique bronze #B4A078:
  开源之道 · 适兕 × 窄廊

Bottom edge, smallest, gray:
  联合支持：「开源之法与经济」、CCF ODTC

Bottom right: leave a clean empty square (about one sixth of the poster width)
framed by a thin light line, no content inside — a QR code goes there later.

=== CONSTRAINTS ===
Correct Simplified Chinese characters are mandatory: no garbled glyphs, no
invented characters, no pseudo-Chinese strokes. No English except "OSCAR" and
"CCF ODTC". No watermark, no signature scribbles.

NEGATIVE: no gibberish characters, no broken glyphs, no Latin filler text,
no circuit boards, no binary code, no glowing blue tech effects, no graduation
caps, no handshake clichés, no globe, no lightbulb, no cartoon style,
no people, no faces, no hands.
```

### 备选 B · 窄廊（更贴「场域与权力」这一节）

把 VISUAL 段替换为：

```
A narrow corridor between two massive board-formed concrete walls, photographed
straight-on with perfect one-point perspective. The corridor is barely wide
enough for one person. At the far end, a small rectangle of warm daylight. The
walls show visible tie-holes and form lines. The floor is polished concrete,
reflecting a faint vertical stripe of that distant light. Utterly empty — no
people, no props, no signage. The corridor occupies the upper half; the lower
half is darker foreground floor, kept simple and even, reserved for typography.
```

TYPOGRAPHY 与 CONSTRAINTS 两段保持不变。

### 备选 C · 翻页的手（人的尺度，最温和）

```
Close-up of an adult's slightly weathered hands turning a page of an old
technical manual with a cracked spine. Shot from above at a slight angle. The
paper is thin and has been turned many times; the corner is soft with use. A
pencil lies just out of focus in the background. Warm desk-lamp light, strong
single source from upper left, deep falloff into shadow. Hands and page occupy
the upper two-thirds; the lower third is dark desk surface, smooth and even,
reserved for typography.
```

TYPOGRAPHY 与 CONSTRAINTS 两段保持不变。

---

## 四、出图后必做的三件事

即使中文已能生成，仍要**逐字核对**——这是这道工序唯一不能省的部分：

1. **核对所有中文**。重点是生僻字：「适兕」的「兕」、以及「窄廊」「共读」「桥接」。
   AI 常见错误：多一笔少一笔、「兕」写成形近字、引号被做成装饰符号。
2. **核对数字与时间**。13:30 / 14:00 / 2026.10.31 一个字都不能错。
3. **贴二维码并实扫**。见下。

### 二维码叠加规范

**AI 不生成二维码**——画出来的一定扫不出，必须后期贴真图：

- 素材：`https://osbook.opensourceway.blog/images/events/2026-10-31-signup-qr.png`
- **极性不可反转**：深码浅底
- **border ≥ 1**，实际用 4；缺静区任何缩放都救不回来
- **尺寸 ≥ 240px**（320 / 340 都验证过可用）
- 二维码四周留白，下方不压文字
- **贴完必须实际扫一次**再发

---

## 五、仍然不要出现的东西

- 齿轮、电路板、二进制、蓝色发光科技感
- 握手、地球仪、灯泡、博士帽这类廉价的「协作/创新」符号
- 人物面孔（会显得像某个人，而不是一场活动）
- 乱码汉字、伪汉字笔画、装饰性拉丁填充文字

---

## 六、已过期的旧规则（留档，避免再犯）

| 旧规则 | 现状 |
|---|---|
| 「中文交给 AI 必错，一律后期排版」 | ❌ 已过期。Image 2 中文可用，直接写进提示词 |
| 提示词里反复强调 no text | ❌ 已过期，反而会阻止它画字 |
| 出图后主要靠手工加文字 | ✅ 改为：AI 出成品 + 逐字核对 + 贴二维码 |

**唯一保留的硬约束**：二维码必须后期贴真图，AI 画的永远扫不出。
