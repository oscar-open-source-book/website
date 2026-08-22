---
title: "开源之书 · 共读"
type: landing
sections:
  - block: markdown
    content:
      title: "开源之书 · 共读"
      text: |
        # 共读 · 共识 · 共进

        「OSCAR·开源之书·共读」——82 本开源经典著作，26 场线下 meetup，持续生长的开源思想地图。

        「开源之道」致力于开源相关思想、知识和价值的探究。

        「开源之书·共读」是其中的思想实践——用共读的方式，建立一张持续生长的开源思想地图。
    design:
      background:
        color: "#1B3B6B"
  - block: collection
    id: 书单
    content:
      title: "书单"
      text: "从《大教堂与集市》到《智能简史》，按 7 个分类排列。"
      filters:
        folders:
          - books
      count: 6
    design:
      view: grid
      columns: 3
  - block: collection
    id: 共读
    content:
      title: "共读 Meetup"
      text: "2022 至今，26 场线下共读。"
      filters:
        folders:
          - events
      count: 4
    design:
      view: list
      columns: 1
  - block: collection
    id: 推荐
    content:
      title: "每日推荐"
      text: "每周精选一本书或一篇论文，与制度分析框架对话。"
      filters:
        folders:
          - posts
      count: 3
    design:
      view: list
      columns: 1
---