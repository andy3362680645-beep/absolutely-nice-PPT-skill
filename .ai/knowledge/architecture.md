# 仓库架构（随代码刷新）

> 最后更新：2026-10-18（初始骨架，尚未开发）。
> 每次结构性改动后必须更新本文件，随提交一起合入。

## 目标架构

```
PPT_agent/
├── AGENTS.md              # AI 协作总纲
├── .ai/                   # 流程规范 / 模板 / 知识库
│   ├── 00~06-*.md         # 开发六阶段
│   ├── git-workflow.md
│   ├── product-sop.md     # 产品流水线
│   ├── templates/
│   └── knowledge/
├── src/                   # 代码
│   ├── text_fit.py        # 中文文本适配（已就位，已实测）
│   ├── outline.py         # 大纲读取与校验
│   ├── style.py           # 风格参数、色板提取
│   ├── images.py          # 生图调度与素材管理
│   ├── builder.py         # v1 pptx 组装
│   ├── manifest.py        # v1 清单生成与读取
│   ├── diff.py            # v1 改动识别
│   ├── render.py          # 渲染（LO / HTML 两阶段）
│   └── checks.py          # 几何检测 / 视觉自检辅助
├── fonts/                 # 字体文件（不入库）
├── assets/                # 背景、插画素材（不入库）
├── output/                # 每个任务的产物：v1/v2/manifest/渲染图（不入库）
└── specs/                 # 开发任务留档（入库）
```

## 一次 PPT 产出的数据流

```
deck-outline.md（逐页内容）
style-params.md（风格参数）
        │
        ├──► images.py ──► assets/（背景 + 透明底插画 PNG）
        │
        ▼
builder.py（text_fit 处理所有中文文本）
        │
        ├──► output/{任务名}/{主题}_v1_可编辑.pptx
        └──► output/{任务名}/manifest.json
                │
                ▼
用户在 WPS/PPT 改 v1
                │
                ▼
diff.py：读回 v1 与 manifest diff → 受影响页
                │
                ▼
render.py：
  M1 阶段 = LibreOffice 转 PDF/PNG
  M5 阶段 = HTML/CSS 精排版 + Playwright 截图
                │
                ▼
checks.py：几何检测 + 视觉自检
                │
                ▼
output/{任务名}/{主题}_v2_展示版.pptx + 逐页 PNG
```

## manifest.json 结构（规划，以实现为准）

```json
{
  "deck": "主题",
  "slides": [
    {
      "slide_index": 1,
      "shapes": [
        {"shape_id": 10, "type": "picture", "name": "bg",
         "left": 0, "top": 0, "width": 12192000, "height": 6858000,
         "image_path": "assets/xxx/bg_01.png"},
        {"shape_id": 11, "type": "text", "name": "title",
         "text": "……", "font": "Source Han Sans", "font_size": 32,
         "left": 800000, "top": 500000, "width": 10000000, "height": 1200000}
      ]
    }
  ]
}
```

## 模块依赖原则（自底向上）

- 数据结构（outline / style-params / manifest）→ 工具函数（text_fit / 色板）→ 逻辑（builder / images / diff）→ 渲染（render / checks）→ 入口封装。
- 上层依赖下层，下层不反向依赖上层。
- 所有模块用统一配置读取路径、字体、画布尺寸，不硬编码。

## 当前状态

- [x] 协作规范、SOP、模板、知识库骨架
- [x] text_fit.py（中文适配三道防线）
- [ ] M1 单页端到端
- [ ] M2 完整 v1
- [ ] M3 改动闭环
- [ ] M4 风格参数提取
- [ ] M5 HTML 渲染
- [ ] M6 skill/Agent 封装
