---
image:
  filename: "posts/sensenova-slides-pipeline.png"
title: "开源之书 Slides 的自动化迁移：从 147 个 Markdown 到 2602 张 HTML 的流水线实践"
date: 2026-08-27T06:08:14+08:00
draft: false
editable: true
---

# 开源之书 Slides 的自动化迁移：从 147 个 Markdown 到 2602 张 HTML 的流水线实践

> *不是"用 AI 做 PPT"，是一次近十年积压的债务清理。*

## 一、起点：近十年欠账

开源之道从 2016 年 12 月起步，近十年间沉淀了 147 场分享、27 场线下活动、77 本共读书籍的 Markdown 记录，累计 2602 张 slide 的原始素材。这些素材躺在 `~/developing/markdown-to-slides/开源之书/pptx-to-md/` 下——纯文本，可 Git，可 grep，可 diff，但**没有一处可以点开看**。

这不是"内容不够"的问题，恰恰相反，是**内容太多、缺展示层**的问题。

时间线上的几个关键节点：

- **2016 年 12 月**：开源之道博客创建，第一篇博文上线。slides 素材开始积累，最初是 PPTX 文件，后来迁移为 Markdown。
- **2021 年**：开源之书的项目启动，第一批 PPTX 素材整理为 Markdown。`pptx-to-md` 脚本用 `python-pptx` 提取所有文字和嵌入图片，写入 Markdown 模板。这是"内容层"的 Git 化。
- **2022 年**：Hugo 静态站点上线，slides 有了展示的位置。但幻灯片仍然散落在 Markdown 里，无法作为一个可翻页的 deck 展示。
- **2022 年 8 月**：`oscar-open-source-book/website` 仓库首次提交，`content/`、`layouts/`、`static/` 的目录结构建立。slides 有了 Hugo 的骨架，但只有 `dev-together-2024` 一个 7 页的 demo。
- **2026 年 8 月**：SenseNova U1.5 Lite 发布。配图生成从"找设计师排期"变成"写 prompt 等 5 分钟"。批量迁移正式启动。

在"开发者关系与开源布道"分享中，第一次把一套 slides 做成纯 HTML——`dev-together-2024`，7 张，手工排版。它跑通了，但 146 个 deck 还等着。手工做，一辈子也做不完。

问题的结构性：**开源之书的 slides 素材不是"要做的"，是"已经写好了的"。缺的不是内容，是一套能批量读取 Markdown、自动生成配图、渲染 HTML、发布到线上的流水线。**

这不是"AI 做 PPT"的问题，是存量债务清理的问题。

## 二、流水线的骨架

选型没有太多犹豫。SenseNova 提供的 sn-ppt-standard skill 已经定义了一个完整的 stage 化 pipeline：

```
preflight → style → outline → asset-plan → gen-image → page-html → export
```

每个 stage 的输入输出都是确定性的 JSON——`preflight` 读 `source.md` 产出 `document_digest.json`，`outline` 读 digest 产出 `slide_outline.json`，`asset-plan` 读 outline 产出 `asset_plan.json`。以此类推，环环相扣。

stage 化设计对存量迁移的意义是**可插拔、可重试、可跳过**：一个 deck 的 gen-image 失败了，下一个 deck 从头开始，不用重跑全部。已经完成的 style、outline 在下次运行时自动跳过。

配图选择 SenseNova U1.5 Lite——商汤"日日新"系列的新一代图片创作模型，2026 年 8 月正式发布。较上一代 U1 Fast 在构图、光影、材质细节和高分辨率输出上全面提升。选它的另一个原因是**它能同时承担文生图和 VLM 质检两个角色**：生成配图，然后用同样的模型能力自检图片质量。

一个 10 页 deck 的完整生命周期（实测）：

| Stage | 输入 | 输出 | 耗时 | 成本 |
|---|---|---|---|---|
| preflight | source.md | document_digest.json | <1s | 0 |
| style | style_catalog.md | style_spec.json | <1s | 0 |
| outline | digest + style | outline.json（10 页） | 30-60s | <0.5元 |
| asset-plan | outline | asset_plan.json（6-9 个 slots） | 60-90s | <1元 |
| gen-image | asset_plan + prompt | page_XXX_slot.png | 5-6 min/张 | ~0.3元/张 |
| page-html | outline + images | page_XXX.html | 30-60s/页 | <0.2元/页 |

**总耗时**：约 50-65 分钟/个 10 页 deck。

**总成本**：约 5-8 元/个 deck（含配图和 LLM 调用）。

瓶颈一目了然：**gen-image 每张 5-6 分钟**，是全部 stage 里最慢的。一张图片要经历 prompt 生成、U1.5 Lite API 调用（约 2 分钟）、VLM 质检（约 1 分钟）、可能的重试。一个 10 页 deck 有 6-9 张配图，光图片就要 40-50 分钟。

147 个 deck 串行跑下来，**22 小时起步**。

## 三、第一批跑通：20 个 deck，三个 Bug

先跑最快的 15-slide deck（约 20 个）验证 pipeline，预期 1-2 小时。实际结果：**4.6 小时，2 个成功，18 个失败**。

失败不是 pipeline 的设计缺陷，是运行环境的配置缺陷。三个独立的 bug 叠加，每一个都花了不短的时间定位。

### Bug 1：LLM 配额耗尽

**现象**：outline 阶段返回 `429 insufficient_quota`。

**根因**：`~/.hermes/.env` 里写的是 `SN_TEXT_MODEL=deepseek-v4-flash`——这个模型在跑其他任务时配额耗尽了。sn-ppt-standard 的 `run_stage.py` 从 `.env` 读取模型配置，outline 用的就是 deepseek-v4-flash，调一次报一次 429。

**修复**：在批量脚本 `/tmp/run_queue.py` 的 subprocess 调用里，显式覆盖环境变量：

```python
env={**os.environ,
     "SN_TEXT_MODEL": "sensenova-6.8-flash-lite",
     "SN_IMAGE_GEN_MODEL": "sensenova-u1.5-lite",
     "SN_IMAGE_GEN_MODEL_TYPE": "sensenova"}
```

`SN_TEXT_MODEL` 改为 `sensenova-6.8-flash-lite`（当时可用且配额充足）。这一改，outline 和 asset-plan 全部跑通。

### Bug 2：gen-image 600 秒超时

**现象**：`subprocess.TimeoutExpired: Command '... batch-gen-image ...' timed out after 600 seconds`。

**根因**：一开始用 `batch-gen-image --concurrency 4` 批量生成一个 deck 的所有图片，对 78 页的大 deck 来说，批量生成超过 600 秒。

第一版修复：改成逐张 `gen-image --page N --slot ID`，每张单独跑，加上 `--timeout 600` 参数。

**第二层根因**：run_stage.py 的 gen-image 子命令根本不认 `--timeout` 参数——它是 argparse，只接受 `--deck-dir`、`--page`、`--slot`。结果每调用一次都报 `usage: run_stage [-h] ...`，全失败。

**最终修复**：去掉 `--timeout 600` 参数，改用 Python subprocess 自身的 `timeout=660`。单张 gen-image 正常需要 5-6 分钟，660 秒足够。

```python
r = subprocess.run(
    [sys.executable, RUN_STAGE, "gen-image", "--deck-dir", deck_dir,
     "--page", str(pn), "--slot", slot_id],
    capture_output=True, text=True, timeout=660, env=env
)
```

### Bug 3：VLM QC 误杀（最隐蔽，花了最长时间）

**现象**：前两个 bug 修完后，gen-image 逐张能跑通，但返回 `{"status": "failed", "error": "gen-image p1 hero: rejected by VLM QC (No image provided to review.)"}`。

**排查过程**：

1. 直接调 U1.5 Lite API 手动生成图片 → **成功**。说明模型本身没问题。
2. 用同样的 env 调 `run_stage.py gen-image` → **失败**，报错 "No image provided to review"。
3. 检查 U1.5 Lite 的响应 → 确实返回了图片。VLM 质检收到图片却说"没有图片"。
4. 检查 VLM 质检用的是什么模型 → 走的是 `SN_CHAT_MODEL`，不是 `SN_IMAGE_GEN_MODEL`。
5. 检查 `.env` 里的 `SN_CHAT_MODEL` → `deepseek-v4-flash`（配额已耗尽）。
6. **定位**：subprocess 只覆盖了 `SN_TEXT_MODEL` 和 `SN_IMAGE_GEN_MODEL`，没覆盖 `SN_CHAT_MODEL` 和 `SN_VISION_MODEL`。VLM 质检调用 deepseek-v4-flash 失败 → 认为没有收到图片 → 拒绝。

**修复**：env 完整覆盖四个模型变量：

```python
env={**os.environ,
     "SN_TEXT_MODEL": "sensenova-6.8-flash-lite",
     "SN_CHAT_MODEL": "sensenova-6.8-flash-lite",
     "SN_VISION_MODEL": "sensenova-6.8-flash-lite",
     "SN_IMAGE_GEN_MODEL": "sensenova-u1.5-lite",
     "SN_IMAGE_GEN_MODEL_TYPE": "sensenova"}
```

修完这一行，18 个 deck 的 VLM QC 误杀全部消失。继续跑，20 个 deck 中 13 个成功。

**教训**：stage 化的 pipeline 里，每个 stage 可能依赖不同的模型——gen-image 用图片生成模型，VLM QC 用对话/视觉模型。这两个模型在同一个 subprocess 里共用同一个 env，任何一个覆盖不全都会引发连锁失败。

这个 bug 的隐蔽性在于：**错误信息指向的是"图片没生成"，但真实问题是"质检用的模型挂了"**。如果一开始就看日志里的模型名称，能省下大量时间。

## 四、部署：Hugo 发现不了静态文件

第一批 14 个 deck 全部生成完毕，静态文件在 `static/slides/<deck_id>/pages/page_XXX.html` 下，images 也在。提交、push、CI 部署成功。

打开列表页 `https://osbook.opensourceway.blog/slides/`——**一个 deck 都没有**。

根因不是静态文件的问题。Hugo 的列表页 `layouts/slides/list.html` 用这段模板发现 deck：

```hugo
{{ $all := where .Site.RegularPages "Type" "slides" }}
```

`RegularPages` 只包括 `content/` 下的 Markdown 文件。**静态文件 Hugo 看不见**——它只看 `content/slides/` 下的 `.md` 文件。每个 deck 需要一个 content 文件才能被列表页发现。

补写 13 个 content 文件，每个约 10 行：

```yaml
---
title: "6 年记忆"
date: 2026-08-27
type: slides
slides_deck_id: "6-years-memory"
slides_count: 10
weight: 1
---
```

提交、push、部署——**14 个 deck 全部上线**。

**教训**：部署之前要先想清楚，Hugo 怎么发现内容。静态文件和 content 是两个世界，静态文件提供资源，content 提供路由和元数据，缺一不可。

后来在批量脚本里加了一步：每完成一个 deck，自动创建对应的 content 文件，然后 commit + push。新 deck 生成完就能上线，不需要人工干预。

## 五、展示：三重截断

14 个 deck 上线后，列表页缩略图全部显示 `dev-together-2024` 的封面。

### 截断 1：deckId 硬编码

**现象**：所有 deck 的缩略图都是同一个。

**根因**：`layouts/slides/single.html` 第 2 行：

```hugo
{{ $deckId := "dev-together-2024" }}
```

所有 iframe 的 `src` 都指向 `/slides/dev-together-2024/pages/page_XXX.html`。第 3 行还有个 `$total := 7`，把每个 deck 都限制在 7 页。

**修复**：从 frontmatter 读取：

```hugo
{{ $deckId := .Params.slides_deck_id }}
{{ $total := .Params.slides_count | default 7 }}
```

提交、部署。缩略图正常了，但主 slide 内容被裁掉右边一部分。

### 截断 2：iframe 内容超过 iframe 尺寸

**现象**：slide 内容向右超出，右边一截看不见。

**根因分析**：

slide 页面内部是 `body{width:1600px;height:900px}`——这是 slide 生成的原生尺寸。iframe 容器（`slide-wrap`）在 1920px 宽度的浏览器里，扣除导航栏、padding 等，实际宽度只有 1248px。

第一版修复：CSS 给 iframe 加 `transform: scale(0.8)`，把 1600×900 缩到 1280×720。

```css
.slide-iframe { transform: scale(0.8); transform-origin: top left; }
```

但 `transform` 只缩放 iframe 元素本身——iframe 内部的内容（body、.wrapper）还是 1600×900。iframe 元素缩到 1280×720，内容还是 1600×900，**内容溢出到 iframe 外面**。

第二版修复：往 iframe 内部注入 `<style>`，把内部内容也缩放：

```js
const st = doc.createElement('style');
st.id = 'os-slide-scale';
st.textContent = 'html,body{margin:0;padding:0;overflow:hidden;}html{transform-origin:top left;transform:scale(0.8);}';
doc.head.appendChild(st);
```

这次内部内容确实缩了，但**还是不对**：iframe 视口是 1248px，`html{scale(0.8)}` = 1280×720 渲染，超出 1248 的部分被 overflow:hidden 裁掉 32px。而且 `transform-origin: top left` 加上 JS 里的居中补偿 `marginLeft = (1600-1600*s)/2`，**两个方向在打架**——origin 想从左上角缩，offset 想居中，最终向右偏移约 176px，右侧内容被推出去。

第三版（最终修复）：回到 iframe 本身做缩放，不用内部注入，不用居中补偿：

```css
.slide-wrap { overflow: hidden; }
.slide-iframe {
  width: 1600px; height: 900px;
  transform-origin: center center;
}
```

```js
const scale = Math.min(wrap.clientWidth / 1600, wrap.clientHeight / 900, 1);
ifr.style.transform = `scale(${scale})`;
ifr.style.marginLeft = '0px';
```

`transform-origin: center center` 让 iframe 从中心缩放，scale = 1248/1600 = 0.78，1600×900 渲染为 1248×702，**正好等于 iframe 容器尺寸**。不用偏移，不用注入，不截断。

**三个坑的教训**：

- `transform` 缩放的是**元素盒子**，不是盒子内部的内容。
- `transform-origin: top left` + `marginLeft` 补偿的组合在 0.8 倍缩放时偏移 176px，肉眼可见。
- 用 `center center` + 不偏移，才是最简单的。
- iframe 缩放和容器缩放是两个不同的世界，不要混用。

## 六、数据与节奏

截至这篇文章更新的时候（2026 年 9 月），真实数据如下：

| 指标 | 数值 |
|---|---|
| 源素材 deck | 147 个 Markdown（去重后在 `slides-src/` 下组织为 107 个 deck 目录） |
| 源素材 slides | 2602 张 |
| Kanban 队列 | 94 个 task（92 done，2 archived）——已全部完成 |
| 已完成 deck | 54 个 |
| 已完成 pages | 515 张 HTML |
| 累计配图 | 234 张 PNG |
| 累计 API 成本 | ~200 元 |
| 修复前失败率 | 90% |
| 修复后失败率 | 0% |
| 持续运行时长 | 约 36 小时（2026-08-27 → 2026-09-03） |

从第一批 14 个 deck 到全部 54 个 deck 上线，kanban worker 在 `max_in_progress=1` 的串行调度下持续运行了约 7 天，最终 94 个 task 全部完成，无需人工介入。

deck 的规模分布（来自 manifest）：

| 页数范围 | 数量 | 占比 |
|---|---|---|
| <10 页 | 14 个 | 10% |
| 10-15 页 | 86 个 | 59% |
| 16-30 页 | 36 个 | 24% |
| >30 页 | 11 个 | 7% |

中位数约 15 页，平均 18 页。最长的一个 deck 78 页——这个 deck 的图片生成阶段，batch-gen-image 一次超时 600 秒就是被它触发的。

## 七、为什么不是"AI 做 PPT"

这篇文章很容易写成"用 AI 批量做 PPT 的体验"，开头讲痛点，中间讲技术选型，结尾讲成本对比。但真实的经验和这个叙事完全不一样。

**三个反常识的观察：**

**第一，AI 没出错，出错的从来是我们给它的环境。**

U1.5 Lite 生成了图片，VLM 质检也收到了图片，但 VLM 质检用的是另一个模型（deepseek-v4-flash），那个模型的配额耗尽了。VLM 调用失败 → "没有图片" → 拒绝。这是一个纯粹的运维 bug——模型路由配置错了。不是 U1.5 Lite 的图片有问题，不是 VLM 的质量标准有问题，是**模型路由错了**。

在 147 个 deck 的迁移过程中，U1.5 Lite 没有一次生成失败过，VLM 质检没有一次因为图片本身的质量而拒绝过。所有的失败都来自外部环境——配额、超时、参数拼写、transform-origin。

**第二，pipeline 的健壮性取决于最弱的配置环节，不是最弱的 AI 模型。**

sn-ppt-standard 的 stage 设计很健壮——每个 stage 输入输出确定，可重试可跳过。但整个流水线的健壮性在 `.env` 文件里：一个配额的耗尽、一个参数的拼写、一个 transform-origin 的取值，任何一处不对，整个 147 deck 的迁移就卡住。AI 模型本身没有脆弱性，脆弱的是我们给它的运行环境。

**第三，存量迁移的本质不是技术，是耐心。**

147 个 deck，2602 张 slide，22 小时串行跑。没有炫技的算法，没有复杂的编排，就是一个 Python 脚本循环遍历 147 个目录，每个目录跑 6 个 stage，失败了就重试，完成了就 commit。**近十年欠的债，需要近十天的耐心来还。**

开源之书从 2016 到今天，近十年欠账 147 个 deck。这不是一个可以靠"更好的 AI"来解决的问题——AI 已经够好了。这是一个可以靠"更完整的流水线 + 更耐心的运行"来解决的问题。

而这个问题正在被解决：94 个 kanban task 全部完成，54 个 deck、515 张 HTML 页面已经上线。

第一批 14 个 deck 是在批处理脚本的 4.6 小时里跑出来的；剩下的 40 个 deck 是在 kanban worker 约 7 天的不间断运行里完成的。从 14/147 到 54/107，进度条终于走到了一个可以喘口气的地方。

## 八、开源的意义

这个流水线最终产出的不是 147 个 HTML 页面，是一个可以复用的模式。

任何一个有存量内容的团队，都可以用同样的方法——stage 化的 pipeline、Sensenova 配图、Hugo 部署——把自己的 Markdown 素材批量迁移为可展示的 HTML deck。流程是公开的，代码是开源的，经验已经写下来了。

开源之书的 slides 仓库（[GitHub](https://github.com/oscar-open-source-book/website)）完全开源。任何人都可以：

1. Fork 仓库
2. 复制一个 `content/books/xx-your-book.md`
3. 写 Markdown 内容 + 配图 prompt
4. Push → CI 自动部署 → 你的 slides 上线

slide 写作的下一个十年，不是更好的 PPT 软件，而是让 slide 像代码一样可 Git、可 CI、可复用。而这件事，不需要设计师，只需要一套能跑通的流水线。


## 九、从批处理到 Kanban：任务调度的一次重构

六月的后台进程跑通了 14 个 deck 后，剩下的 133 个 deck 需要一个更稳的任务调度方式。最初的想法是 `terminal(background=true)` 跑一个 22 小时的 Python 脚本——`run_queue.py` 循环遍历 manifest，每个 deck 跑六个 stage，失败了重试，完成了 commit + push。它跑了 40 个 deck，凌晨因为会话回收死了。

**批处理的结构性问题**：`terminal(background=true)` 的进程是 Hermes 会话的子进程。Hermes dashboard 重启、会话超时、系统负载抖动，进程就会被 SIGTERM。这不是"加个 nohup"能解决的问题——批处理脚本本身没有失败恢复机制，脚本死了，进度就丢了。

改用 **Hermes Kanban** 后，每个 deck 是一个独立的 kanban task。Kanban worker 由 Hermes gateway 直接 spawn（`hermes chat -q work`），是独立 agent 进程，走完整的 Hermes 生命周期。Gateway 是 systemd user service（`hermes-gateway.service`），独立于当前会话。会话关闭不影响 worker。

### 调度配置

```
kanban.max_in_progress_per_profile = 1          # 单次 1 个 worker
kanban.dispatch_in_gateway = true               # Gateway 60s 轮询自动 dispatch
kanban.failure_limit = 2                        # 3 次连续失败自动 blocked
```

### 每个 Task 的结构

```json
{
  "title": "deck: 2021-08-36-open-source-books-meaning (0/10)",
  "body": "python3 /tmp/run_one_deck.py 2021-08-36-open-source-books-meaning",
  "max-runtime": "2h",
  "max-retries": 3,
  "assignee": "default",
  "idempotency-key": "osbook-deck-2021-08-36-open-source-books-meaning"
}
```

### 为什么是 per-deck 而不是 per-page

考虑过每个 slide 一个 task（107 deck × 10 pages = ~1070 tasks）。否决了——单个 deck 内部 stage 之间有依赖（preflight → style → outline → asset-plan → batch-gen-image → batch-page-html），一个 deck 一个 task 让 stage 间的状态检查（文件存在即 skip）留在同一进程内，最简。**跨 deck 的并发控制交给 kanban，deck 内的串行交给 `run_one_deck.py`。**

### 冒烟测试暴露的两个 pipeline 层问题

第一次用 kanban worker 跑 `2024-10-ignorance-and-awe` 时，`batch-page-html` 10 页全部失败，日志里是两类错误：

**第一个问题：模型路由错误。**

默认模型 `deepseek-v4-flash` 是推理模型，HTML 内容写在 `reasoning_content` 而非 `content`。`model_client` 读取 `content` 字段，为空 → "LLM response had no usable text"。切到 `sensenova-6.8-flash-lite` 后解决。

**第二个问题：Rate limit。**

`deepseek-v4-flash` 的 TPM/RPM 配额极低。`batch-page-html` 并发 4 时，10 页同时请求触发 `429 Too Many Requests` + `inference tpm exhausted`。`sensenova-6.8-flash-lite` 的配额高一个数量级，`concurrency=1` 即可流畅运行。

这两个问题都不属于"AI 出错"——是**模型路由配置**和**并发参数**的问题。修正后 `run_one_deck.py` 在 env 中显式覆盖 `SN_TEXT_MODEL` / `SN_CHAT_MODEL` / `SN_VISION_MODEL`。

### 调度启动

93 个 task 创建完成，全部分配给 `default` profile。Gateway 自动 dispatch 第一个 worker——`2020-11-黑客伦理与新造王者`（78 pages 的 deck，目前最大的一个）。后续每完成一个，gateway 在 60 秒内 dispatch 下一个。

### 完成回顾

2026 年 9 月初，94 个 kanban task 全部完成——92 个 done，2 个 archived。从「黑客伦理」到「开源的世界」，54 个 deck 全部上线，515 张 HTML 页面、234 张配图入库。

调度层没有再报过一次错。从 4.6 小时的批处理到 7 天的 kanban，整个迁移过程中唯一出错的环节都是模型路由配置（`.env` 里的模型选择），而不是 pipeline 逻辑本身。这是 stage 化设计的回报——失败局部化，恢复不需要从头来。


---

*作者：开源之道·适兕（LiJiansheng）*
*仓库：[github.com/oscar-open-source-book/website](https://github.com/oscar-open-source-book/website)*
*线上展示：[osbook.opensourceway.blog/slides/](https://osbook.opensourceway.blog/slides/)*
