# src 代码模块

按 product-sop 流水线拆分。每个模块一个文件、单一职责。

## 跨宿主成品检查

宿主可使用自己的PPT工具，再用本入口检查真实成品。相对输入按当前工作目录解析，默认[场景配置](../.ai/knowledge/visual-profiles.json)从包内读取。

```powershell
python -m src.presentation_audit inventory --pptx my-report.pptx --out output/inventory.json
python -m src.presentation_audit check --pptx my-report.pptx --map my-report-audit.json --pdf my-report.pdf --out output/audit-01
```

inventory给出文件哈希、实际页序、slide ID、shape_path和样式。AI依据确认大纲填写profile_id、require_thanks、每页kind及对象role。字段见[角色模板](../.ai/templates/presentation-audit.json)，模板本身不是当前文件的证据；PPT变化必须重读。

文字角色为title、heading、body、data_label、source、page_number、thanks、contact；图形角色为background、illustration、decoration。正文不能冒标来源或页码。完整汇报require_thanks=true；单页片段可明确false，报告标明范围。

check核验实际字号、普通对象边界与辅助PDF字符。未知继承、旋转/分组、特殊图表、公式或缺少PDF列待核查。退出0=本次客观检查通过，1=确定问题/输入失败，2=仍有未验证项。输出audit.json和通俗审查摘要，视觉与人类验收另行记录；不改输入，不覆盖已有输出。

## 独立发行快照

```powershell
python -m src.release build --version 2026-10-23-visual-v1 --sample-run output/cross-ai-visual-workflow/sample-01 --out output/releases
python -m src.release verify --folder output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent --zip output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent-2026-10-23-visual-v1.zip --runtime
```

构建要求样页客观、视觉和绑定当前PPT哈希的人类v1确认已具备，白名单选择规范/代码及原创样例，拒绝覆盖版本。验证文件/ZIP、哈希、相对链接、隐私和隔离入口；源、旧任务、旧包和Git状态受保护。发布说明与开发说明分别生成，不自动更新安装副本。接收方使用[共用复测任务](../.ai/templates/cross-host-trial.md)，未实际运行的平台写待验证。

新审查附加角色说明与旧manifest分开。下方保留原M1路径；M2实验代码的正式任务未在本轮验收。m1 prepare-image含早期茶饮、暖白/茶绿固定提示词，其他主题按当前确认页组织实际生图，不当作通用主题渲染器。

## 已就位

- `config.py`：解析项目相对路径、字体及运行参数，不包含个人路径。
- `outline.py`：读取/校验 M1 单页 JSON、素材存在性、背景比例与透明 alpha。
- `m1.py`：提供 `validate`、`build`、`check`、`prepare-image`；最后一个命令生成会话生图交接包，不调用模型 API。
- `builder.py`：分层组装单页可编辑 PPT，同步最小 manifest，再重开核验元素与素材哈希；文字框支持可选底色、内边距、左/中/右对齐，并读回核验。
- `render.py`：LibreOffice 辅助 PDF/参考 PNG 导出，每次独立目录，不读取陈旧文件；Windows 中临时加载配置字体到当前会话，退出 LO 后释放本次引用。
- `checks.py`：核对原生对象、PDF 文案/字体/字号与几何，输出 checks.json；视觉与人类确认单独记录。

当前可运行：

```powershell
.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json --schema-only
.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json
.venv/Scripts/python.exe -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide
.venv/Scripts/python.exe -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide
# 仅在人类确认当前 v1 后运行；此参数记录已有确认
.venv/Scripts/python.exe -m src.m1 prepare-image --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide --v1-confirmed
```

去掉 `--schema-only` 会校验实际素材；素材缺失返回非零。结构通过不表示已可构建或已完成 M1。

运行前准备项目依赖、白名单字体（见 fonts/README.md）、已确认的独立素材与 LibreOffice。必要时用 `check --soffice <直接的soffice.com或exe路径>` 指定程序，不使用会重命名文件的包装脚本。

`latest.json` 指向 `runs/{run_id}/` 下的 PPTX、manifest 与本次辅助导出，记录输入和文件哈希。`check` 通过只进入 `awaiting_v1_confirmation`；先查看参考图并让用户检查 v1，再准备会话生图工具所需输入。最终展示 PNG 由模型整页重绘，PDF/参考 PNG 用于核对与交接。

`prepare-image` 核对输入、PPTX、素材、字体、检测报告及辅助导出哈希，输出 `runs/{run_id}/image-input/` 的 handoff.json、exact-text.json、redraw-prompt.txt。路径引用分别标明 project_root 或 run_dir；会话查看参考图与素材后调用 image_gen，再保存原图及 image-review.json。当前样例已完成首次整页重绘、AI 逐项核对与人类视觉确认，运行状态为 `accepted`；该状态表示本图获确认，开发审查与合入记录分别见 review.md 及 Git 历史。本地程序不冒充自动 OCR、自动审美验收或独立生图 API。

生成最终图后的 `prepare-image` 复跑会核对原交接包、准确文字、原提示词、实际提交提示词、图像与核对/验收记录，只读复用原包。证据缺失、哈希变化或验收未绑定当前图像时返回失败，当前运行标为 failed，不覆盖原证据或自动沿用 accepted。恢复证据或重新检查/重绘后再验收。

用户改 v1 后先人工同步输入再重建；当前会拒绝输入或 PPTX 与记录不一致，不执行自动 diff。超量文本构建失败，需精简或调整大纲。

执行源的 input_sha256 统一按 LF 换行计算，避免 Git 在 Windows 检出 CRLF 后误判内容改变；其他字节仍参与核对，真实文字、数字或布局变化仍会使旧运行失效。图片、PPTX 等产物使用原始文件哈希。

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

## 开发纪律

- 每个模块先写最小样例跑通，再批量；关键路径先开 spike（见 AGENTS.md）。
- 常量（路径、画布尺寸、字体、字号上下限）集中配置，不硬编码。
- 中文文本一律走 `text_fit.py`，禁止用库自带 `fit_text()`。
