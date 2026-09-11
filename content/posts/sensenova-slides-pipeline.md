---
image:
  filename: "posts/sensenova-slides-pipeline.png"
title: "演示文稿的文本化和版本化，以及利用SenseNova U1.5 Lite 实时生成的能力"
date: 2026-08-27T06:08:14+08:00
draft: false
editable: true
---

# 演示文稿的文本化和版本化，以及利用SenseNova U1.5 Lite 实时生成的能力

> *不是"用 AI 做 PPT"，而是把演示文稿拆回文本叙事，再让它重新拥有版本、上下文和实时再生成能力。*

## 一、起点：近十年欠账

真正的问题，不是“有没有 slides”，而是**近十年的 slides 一直被锁在二进制 PPTX 里**。

开源之道从 2016 年 12 月起步，到 2026 年，已经积累 147 场分享、27 场线下活动、77 本共读书籍的记录，累计 2602 张 slide。这些内容不是普通资料，而是近十年里反复讲、反复改、反复沉淀下来的知识资产。但它们长期以 PPTX 文件存在：能放映，难 diff；能打开，难检索；能复制，难合并；能改一版，却很难说清“这一版到底改了什么”。

把 PPTX 当作知识容器，几乎是逆向而行。PPTX 适合表达，不适合演化；适合一次性交付，不适合长期协作；适合屏幕里的视觉秩序，不适合文字层面的审查和版本治理。对于持续生产内容的组织来说，这不只是“文件格式不优雅”，而是一种结构性阻塞：内容越长，阻塞越重；分享越多，债务越厚；越重要，越难维护。

近十年里，这件事一直像鲠在喉中。它不致命，但每次整理、合并、迁移、复述，都会重新卡住一次。

这次迁移要解决的，就是把演示文稿拆回它真正应该拥有的形态：**文本叙事**。具体来说，是用 Hermes Agent + SenseNova 系列模型和 Skills 能力，把多个 PPTX 转成 Markdown；再以 Markdown 作为可 Git、可 diff、可 grep、可审计的事实源；最后通过 SenseNova U1.5 Lite、SenseNova 6.8 Flash Lite、sn-ppt-standard 流水线实时生成 HTML 页面与配图。

PPTX 是展示容器，Markdown 才是知识容器。当知识容器被版本化之后，演示文稿才第一次具备像代码一样的演化能力。

这篇文章讲的是这条迁移路径：不是“用 AI 做 PPT”，而是把已经被二进制封装的十年内容重新文本化、版本化、再生成化。开源之书的 slides 素材不是“要做的”，而是“已经写好了的”；缺的不是内容，是一套能把内容从二进制牢笼里放出来、再让它重新长出来的流水线。

## 二、流水线的骨架

选型没有太多犹豫。SenseNova 提供的 sn-ppt-standard skill 已经定义了一个完整的 stage 化 pipeline：

```
preflight → style → outline → asset-plan → gen-image → page-html → export
```

每个 stage 的输入输出都是确定性的 JSON——`preflight` 读 `source.md` 产出 `document_digest.json`，`outline` 读 digest 产出 `slide_outline.json`，`asset-plan` 读 outline 产出 `asset_plan.json`。以此类推，环环相扣。

stage 化设计对存量迁移的意义是**可插拔、可重试、可跳过**：一个 deck 的 gen-image 失败了，下一个 deck 从头开始，不用重跑全部。已经完成的 style、outline 在下次运行时自动跳过。

### Hermes Agent：让 pipeline 拥有执行、记忆和修复能力

这条流水线不是单点脚本。它的执行环境是 **Hermes Agent**：Agent 负责读取仓库、调用 stage、检查中间 JSON、在失败时定位模型路由或超时问题，再把恢复策略写回脚本和 Kanban task。这个环境的关键不是“会调用 API”，而是它把模型调用、文件状态、任务队列和部署反馈连接成一个可恢复闭环。

![SenseNova Slides Pipeline architecture](/media/posts/sensenova-slides-pipeline-architecture.svg)

这条架构线里有三个可审计对象：`Markdown` 是事实源，`JSON stage artifacts` 是生成中间态，`HTML deck` 是发布态。Agent 的价值不是替代这三者，而是在它们之间建立可恢复的调度与修复。

配图选择 SenseNova U1.5 Lite——商汤"日日新"系列的新一代图片创作模型，2026 年 8 月正式发布。较上一代 U1 Fast 在构图、光影、材质细节和高分辨率输出上全面提升。选它的另一个原因是**它能同时承担文生图和 VLM 质检两个角色**：生成配图，然后用同样的模型能力自检图片质量。

一个 10 页 deck 的完整生命周期（实测）：

| Stage | 输入 | 输出 | 耗时 |
|---|---|---|---|
| preflight | source.md | document_digest.json | <1s |
| style | style_catalog.md | style_spec.json | <1s |
| outline | digest + style | outline.json（10 页） | 30-60s |
| asset-plan | outline | asset_plan.json（6-9 个 slots） | 60-90s |
| gen-image | asset_plan + prompt | page_XXX_slot.png | 5-6 min/张 |
| page-html | outline + images | page_XXX.html | 30-60s/页 |

**总耗时**：约 50-65 分钟/个 10 页 deck。

瓶颈一目了然：**gen-image 每张 5-6 分钟**，是全部 stage 里最慢的。一张图片要经历 prompt 生成、U1.5 Lite API 调用（约 2 分钟）、VLM 质检（约 1 分钟）、可能的重试。一个 10 页 deck 有 6-9 张配图，光图片就要 40-50 分钟。

147 个 deck 串行跑下来，**22 小时起步**。

## 三、运行中的摩擦，与 Agent + Skill + 模型的分工

从 20 个 deck 的验证批开始，真正的问题不再只是“能不能生成”，而是**不同环节之间的边界是否清晰**。

验证批运行时遇到的三类问题，本质上都指向同一个工程教训：

1. **模型路由要显式配置。** outline、asset-plan、page-html 走文本/推理模型；gen-image 走文生图模型；VLM 质检走视觉模型。任何一个环境变量没覆盖，错误信息都可能伪装成“图片没生成”或“模型返回为空”。
2. **长任务要按资源边界拆分。** 78 页的大 deck 一次批量生图必然超过常规 timeout。最后采用的策略不是“把超时调更长”，而是逐张生成、单图超时、deck 级重试。
3. **发布系统有自己的发现规则。** Hugo 的 `content/` 是路由和元数据，`static/` 是资源；slides 播放器里硬编码的 deck id 和 iframe 缩放逻辑，也必须在模板层修正，否则静态文件“存在”但不等于“可见”。

这些问题当然重要，但它们不是这篇文章的主线。它们更像迁移过程中的摩擦：真实、必要、可修，但不应掩盖真正有价值的变化——**演示文稿第一次成为 Agent 工作流里的可调度对象**。

```text
PPTX / Markdown
   ↓
Hermes Agent：理解目标、读取仓库、调用工具、判断状态、恢复失败
   ↓
SenseNova Skills：把任务拆成可执行 stage，约束输入输出和重试边界
   ↓
SenseNova Models：6.8 Flash Lite 负责推理与 HTML，U1.5 Lite 负责配图与视觉表达
   ↓
Hugo / GitHub Actions：发布、索引、版本化
```

**Hermes Agent 是操作主体。** 它不是“调用模型 API 的脚本”，而是维护上下文、调用 skill、读取日志、判断失败类型、决定重试策略的执行者。Agent 的价值在于把分散的模型能力和文件状态连接起来：哪一个 stage 完成了，哪一个图片失败了，哪一个 deck 可以进入下一个任务，都由 Agent 根据事实和工具反馈推进。

**SenseNova Skills 是流程约束。** `sn-ppt-standard` 把工作拆成 `preflight → style → outline → asset-plan → gen-image → page-html → export`。每个 stage 有明确输入、输出、JSON artifact 和可跳过条件。Skill 约束了模型的自由度：模型不是每次从零创作整套 PPT，而是在确定的中间态上继续生成。这样，Agent 的错误可以被定位到某个 stage，而不是淹没在“生成结果不好”这个黑盒里。

**SenseNova 模型提供具体生产能力。** `sensenova-6.8-flash-lite` 负责文本理解、大纲、HTML 结构和页面修复；`sensenova-u1.5-lite` 负责实时配图，承担文生图能力。它们不是同一件事：文本模型负责结构与叙事，图像模型负责视觉表达；Agent 负责让它们在同一条流水线里协作。

这就是这条 pipeline 的核心：不是“让大模型做 PPT”，而是让 **Agent 调度 Skill，Skill 调用 Model，Model 产出可审计 artifact，Agent 再根据 artifact 继续推进**。

## 四、数据与节奏

截至这篇文章更新的时候（2026 年 9 月），真实数据如下：

| 指标 | 数值 |
|---|---|
| 源素材 deck | 147 个 Markdown（去重后在 `slides-src/` 下组织为 107 个 deck 目录） |
| 源素材 slides | 2602 张 |
| Kanban 队列 | 94 个 task（92 done，2 archived）——已全部完成 |
| 已完成 deck | 54 个 |
| 已完成 pages | 515 张 HTML |
| 累计配图 | 234 张 PNG |
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

## 五、为什么不是"AI 做 PPT"

这篇文章很容易写成"用 AI 批量做 PPT 的体验"，开头讲痛点，中间讲技术选型，结尾讲工程闭环。但真实的经验和这个叙事完全不一样。

**三个反常识的观察：**

**第一，AI 没出错，出错的从来是我们给它的环境。**

U1.5 Lite 生成了图片，VLM 质检也收到了图片，但质检阶段被路由到了另一个不可用的模型。VLM 调用失败 → "没有图片" → 拒绝。这是一个纯粹的运维 bug——模型路由配置错了。不是 U1.5 Lite 的图片有问题，不是 VLM 的质量标准有问题，是**模型路由错了**。

在 147 个 deck 的迁移过程中，U1.5 Lite 没有一次生成失败过，VLM 质检没有一次因为图片本身的质量而拒绝过。所有的失败都来自外部环境——配额、超时、参数拼写、transform-origin。

**第二，pipeline 的健壮性取决于最弱的配置环节，不是最弱的 AI 模型。**

sn-ppt-standard 的 stage 设计很健壮——每个 stage 输入输出确定，可重试可跳过。但整个流水线的健壮性在 `.env` 文件里：一个配额的耗尽、一个参数的拼写、一个 transform-origin 的取值，任何一处不对，整个 147 deck 的迁移就卡住。AI 模型本身没有脆弱性，脆弱的是我们给它的运行环境。

**第三，存量迁移的本质不是技术，是耐心。**

147 个 deck，2602 张 slide，22 小时串行跑。没有炫技的算法，没有复杂的编排，就是一个 Python 脚本循环遍历 147 个目录，每个目录跑 6 个 stage，失败了就重试，完成了就 commit。**近十年欠的债，需要近十天的耐心来还。**

开源之书从 2016 到今天，近十年欠账 147 个 deck。这不是一个可以靠"更好的 AI"来解决的问题——AI 已经够好了。这是一个可以靠"更完整的流水线 + 更耐心的运行"来解决的问题。

而这个问题正在被解决：94 个 kanban task 全部完成，54 个 deck、515 张 HTML 页面已经上线。

第一批 14 个 deck 是在批处理脚本的 4.6 小时里跑出来的；剩下的 40 个 deck 是在 kanban worker 约 7 天的不间断运行里完成的。从 14/147 到 54/107，进度条终于走到了一个可以喘口气的地方。

## 六、开源的意义

这个流水线最终产出的不是 147 个 HTML 页面，是一个可以复用的模式。

任何一个有存量内容的团队，都可以用同样的方法——stage 化的 pipeline、Sensenova 配图、Hugo 部署——把自己的 Markdown 素材批量迁移为可展示的 HTML deck。流程是公开的，代码是开源的，经验已经写下来了。

开源之书的 slides 仓库（[GitHub](https://github.com/oscar-open-source-book/website)）完全开源。任何人都可以：

1. Fork 仓库
2. 复制一个 `content/books/xx-your-book.md`
3. 写 Markdown 内容 + 配图 prompt
4. Push → CI 自动部署 → 你的 slides 上线

slide 写作的下一个十年，不是更好的 PPT 软件，而是让 slide 像代码一样可 Git、可 CI、可复用。而这件事，不需要设计师，只需要一套能跑通的流水线。


## 七、从批处理到 Kanban：任务调度的一次重构

如果只把 pipeline 看成脚本，问题停在“跑完 147 个 deck”。但真正的问题是：近十年素材不是一批同质任务，而是不同页数、不同主题、不同图像复杂度的长尾队列。这里需要 Agent 的任务拆解能力，而不是一个更长的后台进程。

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

这正是 Kanban 在 Agent 工作流里的价值：它不是传统项目看板，而是一个可恢复的任务事实源。每个 deck 的状态、重试次数、失败原因和幂等键都被显式记录；Agent 不需要“记住”当前跑到哪里，只需要读取队列，处理下一张可运行卡片。对 147 个 deck 这种长尾任务来说，这种拆解比让 LLM 一次性规划全部生成路径更可靠。
### 冒烟测试暴露的两个 pipeline 层问题

第一次用 kanban worker 跑 `2024-10-ignorance-and-awe` 时，`batch-page-html` 10 页全部失败，日志里是两类错误：

**第一个问题：模型路由错误。**

默认模型返回的 HTML 内容没有被读取到 `content` 字段，`model_client` 只能看到空文本，于是报 "LLM response had no usable text"。切到 `sensenova-6.8-flash-lite` 后解决。

**第二个问题：Rate limit。**

默认模型的 TPM/RPM 配额不够支撑批量页面生成。`batch-page-html` 并发 4 时，10 页同时请求触发 `429 Too Many Requests` + `inference tpm exhausted`。`sensenova-6.8-flash-lite` 的配额更合适，`concurrency=1` 即可流畅运行。

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
