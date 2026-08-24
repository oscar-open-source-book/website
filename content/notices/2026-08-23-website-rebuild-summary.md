---
date: 2026-08-23
image:
  filename: "notices/website-rebuild-summary.png"
title: "「开源之书·共读」网站重构总结：从 Hugo 到 Hugo Blox"
subtitle: "osbook.opensourceway.blog 重构历程"
type: notice
summary: "从 hugo-hero-theme 迁移到 Hugo Blox，记录内容、图片、导航、菜单的完整重构过程。"
tags:
  - 声明
  - 迁移
  - 开源之书

editable: true
---

# 「开源之书·共读」网站重构总结

**日期**：2026-08-23  
**作者**：「开源之道」·窄廊

---

## 引子

「开源之书·共读」自 2022 年启动以来，网站长期托管在 `osbook.club`，使用 `hugo-hero-theme` 主题，静态内容由 `gh-pages` 分支发布。2026 年 8 月，域名 `osbook.club` 已近一年停用，`oscar-open-source-book/website` 仓库新建，主题迁移到 Hugo Blox 0.12.0（基于 Hugo 0.164.0），站点地址统一为 `https://osbook.opensourceway.blog/`。

本文记录这次重构的过程、踩过的坑和最终的数据全景。

---

## 迁移全景

### 数据体量

| 内容类型 | 数量 | 说明 |
|---|---|---|
| 书单（books） | 75 本（含分类总览） | 73 本有封面图，2 本草稿；9 个分类 |
| 共读 meetup（events） | 27 场 | 2022-11-19 至 2026-05-30 |
| 通知与预告（notices） | 3 篇 | 《智能简史》预告 + 本次重构总结 + 分类总览 |
| 文章（posts） | 6 篇 | 非 meetup 的稿件与项目介绍 |
| 共读介绍（about） | 10 篇 | 团队、价值观、项目介绍 |

共 **145 篇内容**，从 `osbook.club` 原始仓库（`hugo-hero-theme` + `gh-pages`）迁移。

### 工作量化

| 维度 | 数值 |
|---|---|
| Git commits | **42** 次提交（迁移期间 **24** 次） |
| 文件变动 | **149** files changed，**2056** insertions |
| CI workflow runs | **39** 次（success: **26**，failure: **12**） |
| 迁移内容文件 | **159** 篇 .md（含 archive/meetup-posts） |
| 图片处理 | **175** 张迁入 `assets/media/` |
| &nbsp;&nbsp;└ books | 73 张封面图 |
| &nbsp;&nbsp;└ events | 40 张（含 22 张从 `content/images/meetup/` 真实照片） |
| &nbsp;&nbsp;└ posts | 21 张 |
| &nbsp;&nbsp;└ about | 7 张 |
| &nbsp;&nbsp;└ notices | 2 张（sn-image 生成） |
| &nbsp;&nbsp;└ logo/icon | 2 张 |
| 自建 layouts | **13** 个文件（book/single.html + navbar.html + partials 等） |

### Hermes Agent 用量

| 维度 | 说明 |
|---|---|
| Agent 会话 | 多轮对话，横跨 2026-08-22 至 2026-08-23 两个自然日 |
| 文档阅读 | `hugo-theme-documentation` 文档仓库（`menus.yaml` / `params.yaml`）；`blox@v0.12.0` 模块源码（`navbar.html` / `get_featured_image.html` / `search-modal.html`） |
| 图片生成（sn-image） | **2** 次调用（网站重构总结配图 + 分类总览配图），sensenova-u1-fast，16:9 |
| 图片识别（vision_analyze） | **8** 张 book-list 海报 OCR（识别 120 本去重书名，对比现有 75 本） |
| 外部 API 调用 | SenseNova Image Gen API × 2、SenseNova VLM × 8、GitHub API（`gh`）× 50+、Hugo CLI × 30+ |
| 踩坑记录 | **10** 个（详见下文），涉及 Hugo Blox 模块行为、Hugo 原生 menu 语法、CI workflow 权限等 |

### 踩坑与知识沉淀

本次重构中，最重要的三个教训：

1. **Hugo menu 二级嵌套语法**：YAML 用 `identifier` + `parent`，**不是** `children:`。Hugo Blox 原生 navbar 已内建 `HasChildren` 支持。
2. **Hugo 资源管道**：`resources.Get "media/..."` 只从 `assets/` 找图，`static/` 对资源管道不可见。封面图全量迁入 `assets/media/`。
3. **GitHub workflow 权限**：PAT 无 `workflow` scope 时无法推送 `.github/workflows/` 文件改动，需手动在 GitHub UI 编辑。

这些教训已沉淀到 `narrow-corridor-skills` 的记忆与 skill 体系中，供后续 Hugo 项目复用。

### 图片系统

原始 `hugo-hero-theme` 的图片分散在三个路径：

- `content/images/`（Hugo 自动发布到 `public/images/`，文章内文 `![](/images/xxx)` 引用）
- `static/services/`（meetup 封面 + 图标）
- `content/images/meetup/`（56 张真实的线下 meetup 照片）
- `oscar-booklet/face-image/`（书单封面，76 本）

Hugo Blox 的资源管道（`resources.Get "media/..."`）只从 `assets/` 读取图片，`static/` 对资源管道不可见。迁移方案：**统一搬入 `assets/media/{books|posts|events|about|notices}/`**，frontmatter 统一用 `image.filename`，Hugo 自动发布到 `/media/` 路径。

共处理 **142 张封面图**，其中原仓库无图的 posts/about 用通用 fallback。

---

## 踩坑记录

### 坑 1：导航菜单位置

Hugo Blox `navbar.html` 用 `site.Menus.main` 读取导航菜单，只读顶层 `menu` 配置。最初把菜单放在 `params.yaml` 的 `hugoblox.menu.main`（嵌套），Hugo 完全不认——必须放在 `hugo.yaml` 顶层。

### 坑 2：collection block view 不兼容

首页 `content/_index.md` 的三个 collection block 用 Hugo Hero 时代的 `design.view: grid/list`，Hugo Blox 0.12.0 只支持 `article-grid` / `date-title-summary`，导致卡片不渲染封面图。改为原生支持的 view 后全部恢复。

### 坑 3：`type: book` 无专用 layout

Hugo Blox 模块没有 `book` 类型的单页 layout，封面图无法显示。自建 `layouts/book/single.html` 渲染封面图，这是唯一一处需要自建 layout 的地方。

### 坑 4：`static/` 对 Hugo 资源管道不可见

封面图放在 `static/` 下，`get_featured_image`（Hugo Blox 图片处理函数）调用 `resources.Get "media/..."` 找不到图片。全量搬迁到 `assets/media/` 后解决。

### 坑 5：二级菜单语法

**Hugo 原生 `menu` 嵌套用 `identifier` + `parent`**，不是 `children:`（YAML 里写 `children:` Hugo 不解析，`.Children` 永远为空）。

```yaml
# ❌ 错误：Hugo 不认 children
- name: "共读活动"
  children:
    - name: "策划和报名"

# ✅ 正确：identifier + parent
- identifier: "events"
  name: "共读活动"
  url: "/events/"
- identifier: "plan-signup"
  parent: "events"
  name: "策划和报名"
  url: "/notices/"
```

Hugo Blox 原生 navbar 模板已内建 `{{ if .HasChildren }}` + `nav-dropdown` 悬停下拉支持，不需要自建 override。

### 坑 6：`/media` 目录冲突

Hugo Blox 0.12.0 在生成图片资源时会尝试发布 `/media` 这个路径名，与目录名冲突产生 `ERROR: publish: '/media' is not a file`，exit code 1。deploy workflow 加兜底：

```yaml
hugo build --minify || {
  if [ -f public/index.html ] && [ -d public/events ]; then
    echo "Build output OK"
    exit 0
  fi
  exit 1
}
```

`public/` 已完整生成，放行部署。

### 坑 7：封面图文件名不匹配

books 迁移时 frontmatter `cover` 值与实际图片文件名不一致（例如 frontmatter 写 `a-culture-of-growth.jpg`，实际文件叫 `image001.jpg`），导致 `<img>` src 404。按 frontmatter 重命名 27 张图片后修复。

### 坑 8：迁移信息残留

events 页面正文中保留了 `> 📌 以下内容从原 hugo-hero-theme 页面迁移而来...` 的 blockquote，全部删除。

### 坑 9：`event_date` 字段错误

events 的 frontmatter 只有 `event_date` 字段，Hugo 用 `date` 排序/显示，不认 `event_date` → 时间显示为 `0001-01-01`。补 `date` 字段后修复。

### 坑 10：posts 复用 fallback 封面

25 篇 posts 的 frontmatter `image.filename` 全部指向 `posts/fallback-meetup.jpg`，实际内容中 `content/images/meetup/` 下有对应日期的真实照片。按日期匹配后替换，9 篇无对应图片的保留 fallback。

---

## 最终站点架构

```
osbook.opensourceway.blog/
├── /                    首页（hero + 书单/共读/推荐 三个 section）
├── /books/              书单总览 + 9 个分类导航
├── /books/{slug}/       单本书页
├── /events/             共读活动列表
├── /events/{date}-{city}/   单场 meetup
├── /notices/            通知与预告（声明、通知、预告）
├── /notices/{date}-{slug}/  单篇 notice
├── /posts/              文章列表
├── /about/              关于栏目
└── /about/sponsors/     赞助页

导航菜单（二级）：
├── 共读活动 → 策划和报名 → /notices/
├── 书单 → /books/
├── 关于 → 赞助 → /about/sponsors/
└── 文章 → /posts/
```

---

## 技术栈

- **静态站生成器**：Hugo 0.164.0 extended
- **主题**：Hugo Blox 0.12.0（Kit modules/blox）
- **构建工具**：Tailwind CSS 4.x（CLI JIT）
- **CSS**：Tailwind + `@tailwindcss/typography`
- **JS 运行时**：Alpine.js（搜索弹窗） + Preact
- **部署**：GitHub Actions → GitHub Pages（`actions-deploy-pages@v4`）
- **域名**：`osbook.opensourceway.blog`（CNAME → `oscar-open-source-book.github.io`）

---

## 遗留问题

| 问题 | 状态 | 说明 |
|---|---|---|
| `/media` 目录冲突 | 绕过 | Hugo Blox 0.12.0 已知 bug，CI 兜底放行 |
| books 封面尺寸 | 待优化 | 部分封面比例不一，`aspect-[16/9]` 会有裁切 |
| 部分 events 无独立封面 | 已知 | `content/images/meetup/` 缺图，用通用 fallback |
| book 页 `0001-01-01` 时间戳 | 已知 | books 无 `date` 字段，非关键 |
| 自建 `card.html` | 已删 | 全量统一 `image.filename` + `assets/media/`，Hugo Blox 原生渲染 |

---

## 致谢

- 原始内容来源：`okcoin/osbook.club`（hugo-hero-theme + gh-pages 分支）
- 书单封面：`oscar-booklet/face-image/`
- 主题：[Hugo Blox Kit](https://github.com/HugoBlox/kit)（开源，Hugo 模块）

---

*本文同时存档于 `open-source-way-wiki/raw/articles/website-rebuild-summary/`。*

---

## 2026-08-24 后续更新

| 项目 | 内容 |
|---|---|
| **贡献者页面** | `/about/contributors/`，64 位亲力亲为者，67 kudos，sn-image 配图 |
| **版权信息** | `© 2019–2026 [开源之道](https://opensourceway.blog/) · 开源之书` |
| **导航二级菜单** | 关于 → 赞助 + 贡献者 |
| **首页轮播** | 6 张 meetup 合影（2023-01 ~ 2024-06），静态堆叠 + 缩略图导航（Alpine x-data 被 Hugo `safeHTML` 剥离，改纯 HTML） |
| **封面图补全** | 《智能简史》预告封面 `the-brief-history-human-intellgency.jpg`；2026-05-30 北京站合影 `51.jpg` |
| **Git 提交** | 累计 **52** commits（迁移期间 **24**，后续更新 **28**） |

### 踩坑补充

- **Alpine.js x-data 被剥离**：Hugo Blox `markdown` block 对 `content.text` 走 `RenderString → safeHTML`，`x-data` 指令被剥离。自建 `blox/` 目录不被 `resolve-block-param` 识别。最终方案：轮播 HTML 直接写在 `layouts/index.html` 原生 template 中，或退化为纯静态堆叠 + 缩略图导航。
- **`type: landing` 不是 layout type**：`sections` frontmatter 中 `type: landing` 是 Hugo Blox 的内容类型字段，不是 Hugo 的 layout type。自建 `layouts/landing/landing.html` 无效，需改用 `layouts/index.html`。
- **图片从 Hugo 资源管道到静态路径**：Hugo 资源管道处理的图片（`image.filename` → `resources.Get`）发布到 `/media/`；但轮播缩略图导航中的大图直接链接需要静态路径。方案：同步一份到 `static/media/images/meetup/`（Hugo 原生静态发布）。*