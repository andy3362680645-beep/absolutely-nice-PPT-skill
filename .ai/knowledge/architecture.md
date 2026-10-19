# 仓库架构（随代码刷新）

> 最后更新：2026-10-19，正式 v1 已获确认；prepare-image 与首次模型整页重绘已执行，AI 内容初检通过，等待最终人类视觉验收。阶段 5 尚未结束。
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
│   ├── config.py          # M1 路径、字体与运行配置（已实现）
│   ├── m1.py              # M1 CLI：validate / build / check / prepare-image
│   ├── outline.py         # 大纲读取与校验
│   ├── style.py           # 风格参数、色板提取
│   ├── images.py          # 生图调度与素材管理
│   ├── builder.py         # 单页 v1 组装、最小 manifest、读回核对（已实现）
│   ├── manifest.py        # v1 清单生成与读取
│   ├── diff.py            # v1 改动识别
│   ├── render.py          # LO 辅助 PDF/参考 PNG 导出（已实现）
│   └── checks.py          # v1 对象、PDF 内容/字体/几何检查（已实现）
├── fonts/                 # 字体文件（不入库）
├── assets/                # 背景、插画素材（不入库）
├── output/                # 每个任务的产物：v1/v2/manifest/渲染图（不入库）
└── specs/                 # 开发任务留档（入库）
```

## 当前 M1 数据流

```
m1-input.json（执行源；大纲/风格 Markdown 为阅读快照）
        ＋ 会话生图工具生成的背景、透明插画（用户已确认）
        ▼
build → builder.py → text_fit.py
        ├── runs/{run_id}/{主题}_v1_可编辑.pptx
        ├── runs/{run_id}/manifest.json
        └── latest.json（运行目录、输入/产物哈希与确认状态）
        ▼
check → render.py（LO 导出辅助 PDF/参考 PNG）
      → checks.py（原生对象、内容、字体、几何）→ checks.json
        ▼
AI 目视检查 ＋ 用户确认 v1
        ▼
prepare-image 交接包 → 会话生图工具参考 v1 整页重绘
        ▼
最终 PNG 逐字/数字与 AI 初检通过 → 待人类视觉验收（当前停留点）
```

## manifest.json（M1 已实现的最小结构）

```json
{
  "schema_version": 1,
  "deck_id": "任务标识",
  "run_id": "本次运行标识",
  "input_sha256": "执行源哈希",
  "canvas_emu": [12192000, 6858000],
  "font_records": {"regular": {"path": "fonts/字体文件.otf", "sha256": "字体哈希"}},
  "slides": [
    {
      "slide_index": 1,
      "shapes": [
        {"id": "bg", "shape_id": 2, "type": "picture", "role": "background",
         "box_emu": [0, 0, 12192000, 6858000], "box_pt": [0, 0, 960, 540],
         "image_path": "assets/xxx/bg_01.png", "image_sha256": "素材哈希"},
        {"id": "title", "shape_id": 4, "type": "text", "role": "title",
         "text": "……", "font_key": "regular", "font_name": "思源黑体", "font_size_pt": 32,
         "box_pt": [40, 40, 800, 60], "effective_box_pt": [42, 42, 796, 56]}
      ]
    }
  ]
}
```

以上为字段节选；完整记录由 builder 同步生成，还包括层顺序、实际换行、字号下限、图片尺寸/alpha、字体及来源哈希。`manifest.py`、自动 diff、多页和整图 v2 PPTX 仍是后续能力。

文字框可选 `fill_color`、`margin_pt`、`align`，用于可编辑数据强调。`slides[].content_groups` 保存完整确认句与有序文字对象 ID，加载输入时核对拼接文案；数据摘要框可以重复强调已有日期/数值，不代替完整句。当前视觉调整版为 13 个文本框、2 张独立图片。

## 模块依赖原则（自底向上）

- 数据结构（outline / style-params / manifest）→ 工具函数（text_fit / 色板）→ 逻辑（builder / images / diff）→ 渲染（render / checks）→ 入口封装。
- 上层依赖下层，下层不反向依赖上层。
- 所有模块用统一配置读取路径、字体、画布尺寸，不硬编码。

## 当前状态

- 已有运行入口：`python -m src.m1 validate/build/check/prepare-image`，真实命令见 src/README.md。`--schema-only` 只核验结构与字体且不标记 ready。
- `outline.py` 已实现单页 JSON/图片检查；`config.py` 集中解析路径与字体；`text_fit.py` 已验证极窄框终止、混排和字号下限，并补显式行距、折行与东亚字体。
- `builder.py` 已生成真实单页 v1；`render.py` 和 `checks.py` 已通过真实导出与内容/字体/几何检查。背景允许与文字叠放，插画按主体安全区检查；自动检测不替代目视检查。
- Windows 导出时，render.py 临时加载配置中的已授权字体到当前会话，在 LO 子进程退出后释放本次加载引用；不写共享字体目录或安装记录。实际 PDF 字体仍须检查，临时加载成功不等于字体验收通过。
- 输入/manifest/PPTX 哈希变化会拒绝沿用当前运行；每次 check 重新导出，清除旧确认。超量返回失败，不静默截断。
- prepare-image 核对已确认 v1、检测/辅助导出/素材/字体哈希，输出 image-input/handoff.json、exact-text.json、redraw-prompt.txt。复跑不倒退已有最终图状态；输入变更失效原交接。
- 最终生图采用会话工具参考 v1 导出图重绘；工具接入不在本地 Python 中伪造。正式原图与 image-review.json 已保存于当前 run，latest.json 为 awaiting_visual_acceptance；AI 逐项核对通过，人类验收仍待确认。LO 导出不是最终美化交付。

- [x] 协作规范、SOP、模板、知识库骨架
- [x] text_fit.py（中文适配三道防线）
- [ ] M1 单页端到端
- [ ] M2 完整 v1
- [ ] M3 改动闭环
- [ ] M4 风格参数提取
- [ ] M5 展示渲染完善（生图一致性与整图封装等）
- [ ] M6 skill/Agent 封装
