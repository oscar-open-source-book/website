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
        text_color_light: true
  - block: markdown
    content:
      title: ""
      text: |
        <div x-data="{ idx: 0, images: [
          '/media/images/meetup/2023-01-14-dialog.jpeg',
          '/media/images/meetup/2023-04-15-all.jpeg',
          '/media/images/meetup/2023-07-08-all.jpeg',
          '/media/images/meetup/2023-09-23-all.jpg',
          '/media/images/meetup/2023-12-23-all.jpg',
          '/media/images/meetup/2024-06-15-all.jpg'
        ] }" class="mt-8 flex flex-col items-center gap-4 max-w-4xl mx-auto px-4">
          <div class="relative w-full aspect-video bg-gray-900 rounded-xl overflow-hidden shadow-2xl ring-1 ring-white/10">
            <template x-for="(img, i) in images" :key="i">
              <img :src="img" x-show="idx === i" x-transition:enter="transition ease-out duration-500"
                   x-transition:enter-start="opacity-0 scale-95"
                   x-transition:enter-end="opacity-100 scale-100"
                   x-transition:leave="transition ease-in duration-300"
                   x-transition:leave-start="opacity-100"
                   x-transition:leave-end="opacity-0"
                   class="absolute inset-0 w-full h-full object-cover"
                   alt="meetup photo" />
            </template>
            <button @click="idx = (idx - 1 + images.length) % images.length"
                    class="absolute left-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full backdrop-blur-sm transition"
                    aria-label="prev">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
            </button>
            <button @click="idx = (idx + 1) % images.length"
                    class="absolute right-3 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full backdrop-blur-sm transition"
                    aria-label="next">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </button>
            <div class="absolute bottom-2 right-3 bg-black/40 text-white text-xs px-2 py-1 rounded backdrop-blur-sm"
                 x-text="`${idx + 1} / ${images.length}`"></div>
          </div>
          <div class="flex gap-2">
            <template x-for="(img, i) in images" :key="'t'+i">
              <button @click="idx = i"
                      class="w-14 h-10 rounded-lg overflow-hidden border-2 transition"
                      :class="idx === i ? 'border-amber-400 ring-2 ring-amber-400/30' : 'border-transparent hover:border-white/40'"
                      :style="'background-image:url(' + img + '); background-size:cover; background-position:center;'"></button>
            </template>
          </div>
          <div class="grid grid-cols-3 md:grid-cols-6 gap-2 mt-2 text-center text-xs text-gray-400">
            <span>2023-01-14</span><span>2023-04-15</span><span>2023-07-08</span>
            <span>2023-09-23</span><span>2023-12-23</span><span>2024-06-15</span>
          </div>
        </div>
    design:
      background:
        color: "#0F172A"
        text_color_light: true
  - block: collection
    id: 书单
    content:
      title: "书单"
      text: "82 本开源经典著作，共读、共识、共进。"
      filters:
        folders:
          - books
      count: 6
    design:
      view: article-grid
      columns: 3
  - block: collection
    id: 共读
    content:
      title: "共读 Meetup"
      text: "2022–2026，26 场线下共读。"
      filters:
        folders:
          - events
      count: 6
    design:
      view: article-grid
      columns: 3
  - block: collection
    id: 文章
    content:
      title: "文章"
      text: "从图书馆、开源文集、走组织、Reading and Talking 到开发者峰会——社区六年来的思考与行动记录。"
      filters:
        folders:
          - posts
      count: 6
    design:
      view: article-grid
      columns: 3
---