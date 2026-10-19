# src 代码模块

按 product-sop 流水线拆分。每个模块一个文件、单一职责。

## 已就位

- `config.py`：解析项目相对路径、字体及运行参数，不包含个人路径。
- `outline.py`：读取/校验 M1 单页 JSON、素材存在性、背景比例与透明 alpha。
- `m1.py`：提供 `validate`、`build`、`check`；`prepare-image` 待 v1 确认后按设计继续实现。
- `builder.py`：分层组装单页可编辑 PPT，同步最小 manifest，再重开核验元素与素材哈希；文字框支持可选底色、内边距、左/中/右对齐，并读回核验。
- `render.py`：LibreOffice 辅助 PDF/参考 PNG 导出，每次独立目录，不读取陈旧文件；Windows 中临时加载配置字体到当前会话，退出 LO 后释放本次引用。
- `checks.py`：核对原生对象、PDF 文案/字体/字号与几何，输出 checks.json；视觉与人类确认单独记录。

当前可运行：

```powershell
.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json --schema-only
.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json
.venv/Scripts/python.exe -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide
.venv/Scripts/python.exe -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide
```

去掉 `--schema-only` 会校验实际素材；素材缺失返回非零。结构通过不表示已可构建或已完成 M1。

运行前准备项目依赖、白名单字体（见 fonts/README.md）、已确认的独立素材与 LibreOffice。必要时用 `check --soffice <直接的soffice.com或exe路径>` 指定程序，不使用会重命名文件的包装脚本。

`latest.json` 指向 `runs/{run_id}/` 下的 PPTX、manifest 与本次辅助导出，记录输入和文件哈希。`check` 通过只进入 `awaiting_v1_confirmation`；先查看参考图并让用户检查 v1，再准备会话生图工具所需输入。最终展示 PNG 由模型整页重绘，PDF/参考 PNG 用于核对与交接。当前尚未完成正式最终图，不把普通导出称为最终效果。

用户改 v1 后先人工同步输入再重建；当前会拒绝输入或 PPTX 与记录不一致，不执行自动 diff。超量文本构建失败，需精简或调整大纲。

`slides[].content_groups` 可用完整句和有序 `shape_ids` 关联拆分说明；输入加载时拼接核对，保留“近”“超”和单位。数字摘要另用原生文本框强调，完整确认句仍保留。最终生图前须使用当前输入和当前 v1 的全部准确文案，不能沿用旧页的文字清单。

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
| `builder.py` | 单页已实现；多页组装待开发 | M2 |
| `manifest.py` | 生成与读取 manifest.json（逐 shape 记录） | M2 |
| `diff.py` | 读回 v1 与 manifest diff，定位改动页/改动项 | M3 |
| `m1.py prepare-image` | v1 确认后输出最终生图交接包 | M1 |

## 开发纪律

- 每个模块先写最小样例跑通，再批量；关键路径先开 spike（见 AGENTS.md）。
- 常量（路径、画布尺寸、字体、字号上下限）集中配置，不硬编码。
- 中文文本一律走 `text_fit.py`，禁止用库自带 `fit_text()`。
