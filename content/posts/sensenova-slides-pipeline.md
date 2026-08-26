---
image:
  filename: "posts/sensenova-slides-pipeline.png"
title: "开源之书的 slides 展示：从 Markdown 到可翻页 HTML Deck 的自动化流水线"
date: 2026-08-27T06:08:14+08:00
draft: true
editable: true
---

# 开源之书的 slides 展示：从 Markdown 到可翻页 HTML Deck 的自动化流水线

## 1. 痛点：为什么做 slides 这么难

写 slide 是所有内容生产方式里最反人性的一种。原因不在于"难写"，而在于它把三个互不相容的世界强行塞进一个流程：

**设计工具管视觉，编辑器管内容，浏览器管预览。** 每改一处要切换工具，每保存一次要重新导出。一个 40 页的 deck，从设计封面到导出 PDF，传统流程平均耗时 4-6 小时。

更致命的是结构性问题——**PPT 不可 Git、不可 CI、不可复用**。版本管理靠"最终版_v3_真的最终版.pptx"，协作靠文件来回传，复用靠"从旧 deck 复制一页然后改"。

开源之书的讲者面临更具体的问题。一位作者一年要做 6-8 场分享，每场 40 页 slides。如果用 Keynote / PowerPoint 从头做，就是 40-60 小时的纯体力劳动。这不是时间管理问题，是**工作流结构性缺陷**。

SenseNova U1.5 Lite 提供了一条不同的路径。它的文生图能力和多模态理解，加上 sn-ppt-standard 流水线，把 slide 写作降级为"写 Markdown + 写提示词"的纯文本工作。视觉设计、图片生成、排版渲染、静态站点发布全部交给确定性工具。

这不是一个炫技项目。它已经真实运行了 **279 张 HTML slides**、覆盖了 **77 本书籍** 的记录、支撑了 **27 场线下活动** 的展示。下面我拆解这条流水线的每一层。

## 2. 方案概览：一个文件贯穿全流程

核心思想是"单一事实源"——一个 `.md` 文件，从写作到上线不再切工具：

```
┌─────────────────────────────────────────────────┐
│ writer 写 Markdown                              │
│                                                   │
│   content/                                       │
│   └── books/                                     │
│       └── xx-your-book.md                        │
│   └── slides/                                    │
│       └── dev-together-2024.md                   │
│                                                   │
│         ↓ sn-ppt-standard pipeline                │
│                                                   │
│   style     → 选择视觉语言（暗色 / 学术 / 极简）│
│   generate  → SenseNova U1.5 Lite 配图 + SVG 渲染│
│   build     → Hugo 编译为独立 HTML               │
│   deploy    → GitHub Pages 自动上线               │
│                                                   │
│         ↓                                         │
│   发布后：浏览器中可翻页、可缩放、可全屏          │
└─────────────────────────────────────────────────┘
```

**五个关键设计原则**：

1. **单一事实源**：一个 `.md` 文件，从写作到上线不再切工具
2. **Git 原生**：所有输入输出都可版本控制，diff 即内容变更
3. **可复用模板**：一次设计，无限套用
4. **AI 增强而非替代**：SenseNova 负责图片生成和排版建议，人负责内容和判断
5. **纯 HTML 输出**：不依赖 React/Vue，任何浏览器直接打开即可

## 3. 流水线详解

### 3.1 Style 阶段：视觉语言的确定性选择

传统 PPT 的设计决策是隐性的——设计师凭感觉配色，换一个人做出来就不一样。sn-ppt-standard 把视觉语言显式化为一份配置文件：

```yaml
# 开源之书的视觉规范（82 本书共享）
theme: "dark-academic"
palette:
  navy:   "#0D2137"
  gray:   "#F5F5F5"
  red:    "#E53935"
  accent: "#B4A078"
font:
  serif:  "Noto Serif SC"
  sans:   "Noto Sans SC"
  display: "Playfair Display"
layout: "left-image-right-text"
```

这套配置被 `build_style_catalog.py` 编译为风格目录，供后续阶段调用。所有 77 本书的 slides 共享同一视觉规范。新加一本书时，只需要写文字内容，模板自动应用配色和排版。

**对比**：用 Keynote 做同样工作，每本书要手动调 30-50 个设计参数。这里只需要改 `config.yaml` 一次。

### 3.2 完整 Pipeline：10 个 Stage 的真实流水

sn-ppt-standard 的 `run_stage.py` 是整个流水线的入口，定义了从 Markdown 到 HTML 的 10 个阶段：

```
preflight      -> 验证 deck 目录、检查依赖、生成 document_digest
style          -> 从 style_catalog.md 中挑选视觉语言 (design_style + color_tone + primary_color)
outline        -> LLM 根据 Markdown 内容生成 slide 大纲 (slide_outline.json)
asset-plan     -> VLM 为每页生成配图计划 (每张图的 prompt + 位置)
gen-image      -> SenseNova U1.5 Lite 逐张生成配图 (支持并发 4 张/次)
page-html      -> SVG 排版引擎渲染每页 HTML (CSS + SVG + 配图合成)
refine-page    -> LLM 审校每页文字和排版，修正错误
batch-*        -> 批量执行 (并发优化，4 线程)
export         -> Hugo 编译 + 指纹哈希 + 部署就绪
```

每个 stage 的输入输出都是**确定性的**——`preflight` 读 Markdown 产出 `document_digest`，`outline` 读 digest 产出 `slide_outline.json`，`asset-plan` 读 outline 产出 `asset_plan.json`……以此类推。这种 stage 化的设计让流水线**可插拔、可重试、可并行**：某一步失败了，从失败点重跑即可，无需从头开始。

`style_catalog.md` 是 LLM 的视觉菜单，它由 `build_style_catalog.py` 从 `style_dimensions.json` 编译而来，包含三个维度：

| 维度 | 选项数量 | 示例 |
|---|---|---|
| design_style | 20+ | dark-academic, minimal, editorial |
| color_tone   | 15+ | warm, cool, monochrome, vintage |
| primary_color | 12+ | navy, oxblood, olive, charcoal |

每个设计者只需要从这三个维度各选一个，组合成 `(dark-academic, warm, oxblood)` 这样的视觉指纹，不需要从零设计配色。这解决了传统 PPT 设计中最耗时的**视觉决策**问题。

### 3.3 Generate 阶段：SenseNova U1.5 Lite 生成配图与 SVG 排版

这是 AI 真正发挥价值的环节。SenseNova U1.5 Lite 是商汤"日日新"系列的新一代图片创作模型，2026 年 8 月正式发布，较上一代 U1 Fast 在构图、光影、材质、细节与高分辨率输出上全面提升，尤其强化了复杂图文创作能力——这对 slides 场景至关重要，因为一张 slide 上的配图不仅要好看，还要承载文字信息、图例标注和视觉层级。传统做法：作者花 1 小时找图、改图、调尺寸，而且找来的图很少和主题匹配。

用 SenseNova U1.5 Lite 后：

```python
# 伪代码：单页 slide 的生成流程
from sn_ppt_standard import render_slide

slide = {
    "title": "制度经济学的四大支柱",
    "content": [
        {"text": "Coase (1960)", "note": "交易成本"},
        {"text": "North (1990)", "note": "制度变迁"},
        {"text": "Williamson (1985)", "note": "治理结构"},
        {"text": "Ostrom (1990)", "note": "自组织"},
    ],
    "image_prompt": "抽象学术概念图，四根柱子支撑一个圆顶，暗金色调，极简风格",
    "style": "academic-minimal"
}

output = render_slide(slide, model="sensenova-u1.5-lite")
# 返回：SVG 排版 + SenseNova 生成的背景图 + 组合后的 HTML 页面
```

SenseNova U1.5 Lite 在此阶段的三项贡献：

1. **文生图**：根据 slide 标题和内容自动生成匹配配图，约 30 秒一张。商汤"日日新"Token Plan 支持按 token 计费，一张 1024×768 的 slide 配图约 0.02 元，279 张 slides 的配图成本不到 6 元
2. **SVG 排版**：将文字按设计语言渲染为可缩放的 SVG 矢量图
3. **风格一致性**：82 本书的 slides 共享同一视觉调性，不会因为换了书就变味

相比人工设计费（市场均价 200-500 元/张），AI 生成的成本优势是数量级的，但更重要的是**它让"做一张 slide 的配图"从"找设计师排期"变成了"写一个 prompt 等 30 秒"**——这个工作流转变本身比省钱更重要。

### 3.4 Build 阶段：Hugo 编译为独立 HTML

Hugo 是静态站点生成器，负责把 Markdown + 模板 + 资源编译为纯 HTML。项目结构：

```
content/
  books/
    01-open-source-way.md         # 开源之道（一本书）
    02-open-source-principles.md  # 开源原则（另一本书）
  slides/
    dev-together-2024.md          # 一次分享会
    osbook-6-years.md             # 六周年纪念
  events/
    2026-08-22.md                 # 一次线下活动
assets/
  media/
    slides/
      dev-together-2024/
        page_001.html             # 279 张中的第 1 页
        page_002.html             # 第 2 页
        ...
layouts/
  slides/
    list.html                     # 目录页（缩略图导航）
    single.html                   # 翻页页（←→ 键盘翻页）
```

构建命令：

```bash
hugo build --minify
# 输出：public/slides/dev-together-2024/index.html
# 输出：public/slides/dev-together-2024/page_001.html ...
```

Hugo 在此阶段的角色：

- **路由生成**：`/slides/dev-together-2024/` 自动成为可翻页 deck
- **资源管道**：自动压缩、指纹哈希、CDN 缓存
- **CI 友好**：GitHub Actions 一键部署

实际部署的 GitHub Actions 配置：

```yaml
# .github/workflows/deploy.yml
on: { push: { branches: [main] } }
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: peaceiris/actions-hugo@v3
        with: { hugo-version: '0.164.0', extended: true }
      - run: hugo build --minify
      - uses: actions/upload-pages-artifact@v3
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: { name: github-pages }
    steps:
      - uses: actions/deploy-pages@v4
```

Push 到 `main` → 3 分钟 → 站点上线。没有手动导出、没有 FTP 上传、没有"文件在哪"的疑问。

### 3.5 翻页交互：Vanilla JS 实现

单页 slide 的翻页交互全部用 vanilla JS 实现，不依赖任何前端框架：

```javascript
// layouts/slides/single.html 中的翻页逻辑
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight") nextPage();
  if (e.key === "ArrowLeft")  prevPage();
  if (e.key === "f")          toggleFullscreen();
});

function nextPage() {
  const slides = document.querySelectorAll(".slide");
  const idx = [...slides].findIndex(s => s.classList.contains("active"));
  if (idx < slides.length - 1) {
    slides[idx].classList.remove("active");
    slides[idx + 1].classList.add("active");
  }
}

function toggleFullscreen() {
  document.body.classList.toggle("fullscreen-mode");
}
```

关键点：**不用 `requestFullscreen` API**（浏览器安全策略限制），而是用 CSS class 切换。`fullscreen-mode` 下隐藏导航栏和缩略条，键盘 ←→ 正常翻页。Esc 键退出。

### 3.6 目录页缩略图：用 transform: scale 渲染原尺寸 iframe

缩略图列表页有个常见坑——用 `<iframe>` 嵌套展示 slide 预览时，因为 slide 设计为 1600×900 原尺寸，缩到 200×112 的缩略图会大量留白。解决方案是用 CSS transform 缩放渲染：

```css
/* 目录页缩略图 */
.thumbnail {
  width: 200px;
  height: 112px;
  overflow: hidden;
  position: relative;
}
.thumbnail iframe {
  width: 1600px;
  height: 900px;
  transform: scale(0.125);
  transform-origin: top left;
  pointer-events: none;
}
```

原尺寸渲染、CSS 缩放到 12.5%，无白边、无模糊。

## 4. 实战案例：279 张 slides，77 本书，27 场活动

整个 `oscar-open-source-book/website` 仓库运行这条流水线：

| 类型 | 数量 | 示例 |
|---|---|---|
| 书籍 slides | 77 本 | [开源之道](https://osbook.opensourceway.blog/books/01-open-source-way/) |
| 事件记录 | 27 场 | [开发者大会](https://osbook.opensourceway.blog/events/dev-together-2024/) |
| HTML 单页 | 279 张 | 可翻页 deck |
| 文章 | 7 篇 | [CFP 征集](https://osbook.opensourceway.blog/posts/call-for-presentations-osbook/) |

每一本书的 slides 从"写 Markdown → 生成配图 → 编译 → 部署"全链路不超过 **30 分钟**。

**对比**：用 Keynote / PowerPoint 做同样内容，从设计到导出需要 **4-6 小时**。

具体看一次 6 周年纪念日 slides 的生成过程：

1. 作者写 `content/slides/osbook-6-years.md`（~200 行 Markdown）
2. `run_stage.py` 执行 preflight → style-samples → outline → asset-plan
3. SenseNova U1.5 Lite 生成配图（约 4 张，每张 30 秒）
4. Hugo 编译为 `slides-src/6-years-memory/pages/page_001.html` ~ `page_020.html`
5. Push → GitHub Actions → `osbook.opensourceway.blog/slides/osbook-6-years/`

**全过程约 25 分钟，零人工干预。**

整个 `oscar-open-source-book/website` 仓库从 2019 年创立到今天，经历了三次主题切换、两次域名迁移（从 `osbook.club` 到 `osbook.opensourceway.blog`）、一次 Hugo 大版本升级（0.164.0），以及 sn-ppt-standard 从零到 10 个 stage 的完整演进。**279 张 slides 无一丢失，每一版都可以从 Git 历史回滚。**

这是 Git + Hugo + 单一事实源带来的结构性优势——传统 PPT 无法做到，因为它不是 Git 友好的文件格式。

## 5. 开源生态价值：让 slide 像代码一样

这个流水线对开源生态的意义不是"多了一个工具"，而是把 slide 写作从体力劳动重新定义为写作：

| 维度 | 传统 PPT | sn-ppt-standard + Hugo |
|---|---|---|
| 版本控制 | 文件名后缀 | Git diff |
| 协作 | 文件来回传 | PR review |
| 复用 | 从零开始 | 换内容，模板不变 |
| 发布 | 手动导出 PDF | CI 自动部署 |
| AI 角色 | 无 | 配图生成 + 排版建议 |
| 学习成本 | 设计软件 20h+ | Markdown 语法 2h |
| 可搜索性 | 二进制不可 grep | Markdown 可全文检索 |
| 离线可用 | 依赖 PowerPoint | 纯 HTML 任何浏览器打开 |

**开源之书的实践验证**：77 本书的 slides，从 2019 年到今天，经历了三次主题切换、两次域名迁移、一次 Hugo 版本升级，**从未丢失过一页 slides**。这是 Git + Hugo + 单一事实源带来的结构性优势。

## 6. 总结与展望

SenseNova U1.5 Lite 与 sn-ppt-standard 的结合，把 slide 写作降级为"写 Markdown + 写提示词"的纯文本工作。这不是一个炫技项目，而是一个**真实运行了 279 张 slides、服务了 77 本书籍记录、支撑了 27 场线下活动**的成熟工作流。

开源之书的 slides 仓库（[GitHub](https://github.com/oscar-open-source-book/website)）完全开源。任何人都可以：

1. Fork 仓库
2. 复制一个 `content/books/xx-your-book.md`
3. 写 Markdown 内容 + 配图 prompt
4. Push → CI 自动部署 → 你的 slides 上线

slide 写作的下一个 10 年：不是更好的 PPT 软件，而是让 slide 像代码一样可 Git、可 CI、可复用。

---

*作者：开源之道·适兕（LiJiansheng）*
*仓库：[github.com/oscar-open-source-book/website](https://github.com/oscar-open-source-book/website)*
*线上展示：[osbook.opensourceway.blog](https://osbook.opensourceway.blog/)*
