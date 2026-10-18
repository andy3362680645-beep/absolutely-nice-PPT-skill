# src 代码模块

按 product-sop 流水线拆分。每个模块一个文件、单一职责。

## 已就位

- `config.py`：解析项目相对路径、字体及运行参数，不包含个人路径。
- `outline.py`：读取/校验 M1 单页 JSON、素材存在性、背景比例与透明 alpha。
- `m1.py`：当前提供 `validate`，其余 build/check/prepare-image 按设计后续实现。

当前可运行：

```powershell
.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json --schema-only
```

去掉 `--schema-only` 会校验实际素材；素材缺失返回非零。结构通过不表示已可构建或已完成 M1。

- `text_fit.py`：中文文本适配（三道防线的防线①）。
  - `cjk_wrap(text, font, max_width)`：中文按字断行、英文整词、标点避头尾。
  - `best_font_size(...)`：求最大可用字号；超量返回 None。
  - `fit_textframe(shape, ...)`：直接写入 python-pptx 文本框并设置 normAutofit 兜底。
  - 已实测：纯中文、中英混排、标点避头尾、超长 URL、字号上下限、超量返回 None。

## 待开发（按 M1~M6 顺序）

| 模块 | 职责 | 里程碑 |
|---|---|---|
| `outline.py` | 单页 JSON 读取/校验已实现；Markdown 为阅读快照，不做通用解析 | M1 |
| `style.py` | 读取 style-params；截图色板提取 | M4 |
| `images.py` | 调用生图模型生成背景/插画，透明底、命名、参数登记 | M2 |
| `builder.py` | 组装 v1 pptx（背景/插画/文本框分层，文本走 text_fit） | M1/M2 |
| `manifest.py` | 生成与读取 manifest.json（逐 shape 记录） | M2 |
| `diff.py` | 读回 v1 与 manifest diff，定位改动页/改动项 | M3 |
| `render.py` | M1：LibreOffice 渲染；M5：HTML/CSS + Playwright 截图 | M1/M5 |
| `checks.py` | PyMuPDF 几何检测（溢出/越界/碰撞）+ 视觉自检辅助 | M1 |

## 开发纪律

- 每个模块先写最小样例跑通，再批量；关键路径先开 spike（见 AGENTS.md）。
- 常量（路径、画布尺寸、字体、字号上下限）集中配置，不硬编码。
- 中文文本一律走 `text_fit.py`，禁止用库自带 `fit_text()`。
