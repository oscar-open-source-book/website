---
title: "{{ replace .TranslationBaseName \"-\" \" \" | title }}"
date: {{ (now.Add (time.ParseDuration "-30m")).Format "2006-01-02T15:04:05-07:00" }}
originalTitle: "[原书名]"
author: "[作者]"
image:
  filename: "books/<slug>.jpg"
  caption: "<slug>"
category: "[分类]"
type: book
weight: 100
recommender: "[推荐语]"
editable: true
---

## 推荐理由

[一句话推荐理由]

## 内容简介

[本书核心内容概要]

## 适兕评注

[适兕的个人评注]