# 技术方案 · M1 单页生图展示链路

> 方案于 2026-10-18 获确认；2026-10-19 阶段 5 检查点 A～F 完成，正式 v1 与模型图已获人类视觉确认。当前待阶段 6 审查验收；下文保留方案及各次运行的历史记录，以末尾收尾状态为准。
> 依据：spec.md 阶段 1～3，以及人类“认可范围，继续”。此回复认可勘察范围，不等于已确认本方案。

## 方案概述

用喜茶 2025 年年度营销回顾的一页内容，验证以下路径：

已确认文案/风格 → 生图背景与独立透明插画 → 单页可编辑 v1（中文自适应）→ 辅助 PDF/参考 PNG → v1 几何与内容核对 → 会话生图工具参考原页及素材重绘 → 最终 PNG 逐字/逐数字核对与人类视觉验收。

本地代码负责数据、组装、辅助导出、检查和输入包；Codex 会话负责调用内置生图工具及视觉核对。M1 不实现独立 API 调用、完整 skill 打包、多页系统、PPT diff 或 HTML 精排版。LibreOffice 是参考页和检测载体的辅助导出工具，最终展示图片由生图模型生成。

交付建议：1 页 v1 PPT、最终 PNG、辅助 PDF/参考 PNG、最小 manifest、检测报告和生图交接记录。本次暂不额外封装整图 v2 PPT；如人类要求，须在本方案中补充后再实现。

## 阶段衔接与审批边界

发现的规则冲突：

- AGENTS.md：人类确认 design.md 前禁止写实现代码。
- .ai/03-design.md：前置 spike 必须先做，结论写入 design.md 并附脚本路径。
- .ai/00-workflow.md：关键新依赖/新 SDK 等触发项须最小验证后再评分。

本次建议的明确安排，须人类批准：先确认本 design.md 中的验证设计；进入阶段 5 后只做环境准备与 spike，先取得文本适配、辅助渲染和参考图重绘证据；结果回填本文件。通过后才做正式模块，不把提前写正式业务代码当作 spike。任何失败最多修复 3 轮；仍失败或需要变更路线/范围，则停下回到对应阶段，修订方案并重新确认。若触发新的 SDK/API/渲染依赖，返回阶段 2 复评。没有明确批准该衔接前，不执行代码。

## 数据结构与接口

### 输入与唯一执行源

- deck-outline.md：已确认的一页内容与来源的阅读快照。
- style-params.md：已确认的视觉方向和本次拟定的具体参数快照，不称为官方品牌 VI。
- m1-input.json：唯一机器执行源，显式列出所有上屏文字、字体/布局和素材引用。Markdown 不做任意语法解析器，避免将 M1 扩展为通用文档系统。
- 三份文件首次一起由已确认内容整理，人工/AI 对照；执行源计算 SHA256。改变文字、来源或关键布局后原确认及交接记录失效，重新检查再运行；程序不暗中从图片或旧文案回写内容。

JSON 字段契约（这里只定义字段，不提供实现）：

| 对象 | 关键字段 |
|---|---|
| 根对象 | schema_version、deck_id、title、slides（必须 1 页）、canvas、style、sources |
| canvas | width_pt=960、height_pt=540；参考 PNG 目标 2560×1440；最终生图目标 16:9 |
| style | 颜色、字体映射、字号上下限、行距系数、文本框边距；字体文件/LO 程序路径允许命令行覆盖 |
| slide | slide_id、texts、images；形状 ID 唯一，显式层角色和阅读顺序 |
| text | id、role、text、box_pt[x,y,w,h]、font_key、cap_pt、floor_pt、color、align |
| image | id、role（background/illustration）、path、box_pt、require_alpha、subject_safe_box_pt |
| sources | id、标题、发布机构、URL、发布日期、相关事实项；不把所有来源内容放在页脚 |

内容固定为已确认的标题、副标题、三组要点和页脚“数据来源：北京日报客户端，2026-01-23。”。“近”“超”、年份、GO 和数字必须保留。正文如需分成小标题/段落/大数字多个形状，逐项记录在同一逻辑组内，仍以完整确认句为核对依据。

M1 只支持轴对齐、无旋转的文字框及图片；不做表格/图表对象、嵌套组合、富文本混排或任意母版解析。装饰优先包含在 AI 背景/插画内，减少无关形状。

#### 2026-10-19：v1 文字视觉调整

人类反馈“文字部分纯文字可能有点素”。在上述已批准的原生文字框与大数字拆分范围内，调整日期/数字的大小、字重与茶绿色，给关键数据文字框设置浅茶绿填充与适当内边距。继续保留三组内容及右侧独立插画，不新增形状类型、外部素材或渲染依赖，不将此反馈视为 v1 确认。

- text 的可选字段 `fill_color` 为六位色值、`margin_pt` 为非负内边距；`align` 按原契约支持 left/center/right。默认仍为无填充、全局内边距、左对齐，所有中文继续经 text_fit。
- 拆分的正文在 slide.content_groups 中保存原完整句与有序 shape_ids；加载时核对拼接后仅忽略空白仍逐字一致，避免突出数字后丢失“近”“超”或单位。manifest 保留逻辑组与完整句。
- 本轮涉及原方案范围内的 outline.py、builder.py、输入/大纲/风格快照及开发记录；原生填充、对齐与内边距须读回核对。导出期间已复现的会话字体未加载问题在原范围 render.py 内修复。重新 build/check 并查看实际参考图后，再交人类确认。

### 最小 manifest（建议纳入）

由 builder 同步写 output/{deck_id}/manifest.json；暂不新增 src/manifest.py。

- 根：schema_version、deck_id、input_sha256、canvas、font_records、slides。
- 每页：slide_id、slide_index、形状列表。
- 每形状：稳定业务 id、实际 shape_id、name、type、role、z_order；EMU 位置尺寸及 pt 位置尺寸。
- 文字：原文、写入文字/布局换行、逻辑组、字体内部名/字重/测量字体文件哈希、选定字号、边距、有效文字区域、适配状态。
- 图片：素材相对路径、文件哈希、像素尺寸、透明度检查结果及主体安全区。
- 本次只服务于重新打开核验、几何映射和生图交接；不实现与用户改动的 diff。

### 生图输入包与检查状态

output/{deck_id}/image-input/ 包含参考页、准确文字清单、素材索引、提示词及来源输入哈希。优先保存素材的相对引用和哈希，不重复制造无关副本。

最终图片不得仅因存在就标记成功。区分状态：v1_checks_passed、awaiting_v1_confirmation、ready_for_image_generation、image_generated、content_reviewed、awaiting_visual_acceptance、accepted/failed。最终 content_reviewed 是人工/AI 逐项目视记录，本次不冒充 OCR 自动检测；人类确认后才 accepted。

### 模块接口契约（名称可在实施中保持等义，不改变职责）

| 模块 | 接口 | 输入 → 输出/失败 |
|---|---|---|
| config.py | load_config(input_path, overrides) | 合并布局/环境配置，解析项目相对路径 → 有效配置；无效路径或参数明确失败 |
| outline.py | load_outline(input_path) | JSON → 经字段、单页、唯一 ID、数值/边界检查的单页对象 |
| text_fit.py | 既有 best_font_size/cjk_wrap/fit_textframe | 保持既有用途；增加极窄框可靠失败与确定的行距/换行行为 |
| builder.py | build_slide(outline, config, run_dir) | 素材/文案 → v1 路径与最小 manifest；内容超量不写成功产物 |
| render.py | render_reference(pptx_path, config, run_dir) | 独立 LO 转换 → 真实 PDF 路径；再由 PyMuPDF 生成参考 PNG，记录实际尺寸 |
| checks.py | check_v1(pptx_path, pdf_path, manifest) | 对象层及文字几何 → checks.json；任何缺页/错文/失败项则失败 |
| m1.py | validate / build / check / prepare-image | 四个最小命令；prepare-image 只有通过检查且 v1 已确认才能产出可用交接状态 |

CLI 拟使用 python -m src.m1，不要求用户手动在 WPS 制作页面。运行时明确 Python 路径，公共源码不包含本机绝对路径。

## 文本、字体与几何策略

### 中文三道防线

1. 生成前：统一经 text_fit.best_font_size/cjk_wrap/fit_textframe。正文目标约 20～24pt，标题目标约 36～42pt，页脚目标 11～12pt；所有内容硬下限 10pt。单页放不下则报内容超量、请求精简，不自动拆页。
2. 写入时：记录测量折行，明确写入换行；使用软换行或等价可核对结构，设置段前/段后为 0、显式 1.2 行距并顶部对齐；保留 normAutofit 兜底。设置拉丁/东亚字体名称，禁止默认中文回退字体。具体 LO 行高仍由 spike 验证。
3. 渲染后：核对 PDF 的文字完整性、字号与几何。发现字体替换、文字丢失、实际字号低于下限或越界则失败；不能让 normAutofit 掩盖问题。必要时降低字号后重新生成，不超过全环节 3 轮修复限制。

极窄框：cjk_wrap 对非正宽度或单字不可容纳必须终止并报告/返回约定失败；best_font_size 可以继续尝试更小字号，全部失败返回 None。先用子进程超时保护复现原边界，禁止让试验无限挂起。

### 字体建议与待批边界

- v1/测量/LO：优先使用白名单思源黑体 Source Han Sans SC 静态 Regular 与 Bold。官方下载与 SIL OFL 1.1 依据见文末；登记字体版本、真实内部名、来源、日期、哈希与授权存档后使用。无需字体随产物分发。
- 字体文件进入忽略的 fonts/；必要的授权文本/截图同样存 fonts/ 下，fonts/README.md 留存来源与本地证据位置。
- 不默认为应用共享目录写字体。先检查 LO 可识别情况；若需要安装，采用用户级字体安装并遵守执行权限；若无法让三处一致就停止，不换成系统默认黑体。
- 系统 NotoSansSC-VF.ttf 只作候选备选，不在未验证可变字重与内部名称前直接复用。
- 最终 PNG 是模型生成字形，不能保证与思源黑体像素级一致。建议人类批准：v1 严格白名单字体，展示 PNG 验收中文无衬线气质、层级与可读性；不声称它用了某个精确字体。若必须精确字形，本方案不能直接满足，须重新讨论路线。

### 几何与内容检查

- 坐标：EMU/12700 得 pt；PDF 确认实际页宽高与 960×540pt 对应后再映射，不按先前样图像素尺寸推导。
- 重新打开 v1：1 页、形状数/类型/业务 ID 与 manifest 一致；逐文字框去除布局换行后与确认文案一致，保留标点和所有数字/限定词。
- PDF：用 PyMuPDF rawdict 字符、坐标与字号提取；先在非重叠的逻辑文字区域分配字符，再按行/阅读顺序重建。不能只用全页字符串包含判断通过，也不能只在 clip 框里提取以致漏掉溢出字符。
- 几何：文字有效区域和实际字框均在画布内；字框不得越出所属有效区域（初始容差 1pt，在 spike 核实，不能任意调大以通过）；正文/标题不得低于配置下限。无法可靠映射到单一文本框时，报告需复核，不自动通过。
- 碰撞：不同文字区不得重叠；文字与插画主体安全区不得非预期相交。背景覆盖整页是合法叠放，不判为错误。透明图片的整幅矩形不等于主体轮廓，以明确的主体安全区作保守检查，并视觉核对其他遮挡。
- PDF 文字可提取不等于图上可见，仍检查参考 PNG 的字体、对比和遮挡。不得宣称几何检测可自动证明所有视觉问题都不存在。
- 负例：必须在 spike 中证明越界/碰撞/漏文/超量至少各能被发现一次；避免只验证正常样例。

### 尺寸与素材

- v1 固定 16:9，960×540pt。背景优先 2560×1440，插画独立透明 PNG；核对真实 alpha，不把白底当透明底。
- 生图背景明确无文字，并为标题/正文预留安全区；插画不带复制的品牌标识、联名 IP 或营销海报。先背景，后插画；按产品 SOP 交人类确认素材方向后组装。
- 最终展示 PNG 优先要求 16:9、2560×1440，但会话工具无法锁定尺寸。建议保留原生输出，记录真实尺寸；宽高比相对 16:9 偏差不超过 0.5%可验收，不承诺固定像素，不自动裁切、拉伸或缩放。超过则请求模型修正；这项验收口径须人类批准。
- 凡 image_gen 生成/编辑均由其工具执行。本地代码不重绘或后期叠加准确文字；模型保真不合格时按最多 3 轮修复规则处理。

## 实现步骤（本次是计划，以下命令尚未执行）

约定：命令在项目根目录执行；使用 .venv/Scripts/python.exe，不依赖 PATH 的 LibreOffice Python。单步最多 5 个源码/文档文件，同一职责切片；每 2～3 步设汇总检查点，各步还须有自己的结果核查。生成产物不是额外实现模块，但必须留存来源与检查。

### 步骤 1：确认环境与运行字体（验证准备）

- 文件：fonts/README.md；环境落点 .venv/ 与 fonts/，不修改系统/应用共享 Python。
- 操作：用可用 Python 创建项目隔离环境；安装现有 requirements.txt 声明的三包，记录具体安装版本；获取并登记选定字体，让 LO 实际识别；新依赖异常按阶段 2 触发规则处理。
- 验证命令：.venv/Scripts/python.exe --version；.venv/Scripts/python.exe -m pip show python-pptx Pillow PyMuPDF；已选 LO 可执行文件 --version。字体内部名及实际 PDF 字体在步骤 3 核验。
- 通过条件：三包可用、字体文件及授权记录齐全、没有把包安装进应用共享环境。

### 步骤 2：验证并定点修复文本适配

- 文件：specs/.../spike_text_fit.py、src/text_fit.py。
- 操作：先复现边界，之后只修复本方案列出的不可前进循环、非法尺寸处理及显式行距/折行一致性。保留返回 None 的失败语义，上层拒绝交付超量页。
- 命令：.venv/Scripts/python.exe specs/2026-10-18-m1-single-slide/spike_text_fit.py。
- 通过条件：中文、GO/数字混排、显式换行、长英数单位、标点、宽度 0/负值/单字超宽、10pt 仍超量均能终止并返回符合约定的结果；输出实际结果摘要。

检查点 A：步骤 1～2 均通过；否则不进入 PPT 业务模块。

### 步骤 3：最小 PPT→PDF→PNG 与检查验证

- 文件：specs/.../spike_render.py、specs/.../image-redraw-checklist.md。
- 操作：只在 spike 脚本中创建最小单页文字/图片形状，验证同一套字体、LO 辅助转换、PyMuPDF 字符坐标与 1 页参考图；加入正常和故意异常样例。不先写完整 builder/render/checks。
- 测试图片仅用最小纯色像素或简单几何夹具验证图片形状，不冒充最终 AI 背景/插画；放在 output/m1-single-slide/spike/。正式素材仍按步骤 7 通过生图工具生成。
- 命令：.venv/Scripts/python.exe specs/2026-10-18-m1-single-slide/spike_render.py --out output/m1-single-slide/spike。
- LO 选择：优先配置直接 soffice.com/exe，参数以列表传递、带超时及独立临时 profile；不修改包装器。核对转换退出码、真实新增文件、页数和输入哈希，拒绝读取上次遗留 PDF。
- 通过条件：准确读回 PPT，LO 导出成功，参考图可见完整文字；实际 PDF 字体与配置一致；负例能正确失败。脚本复跑不把上轮产物当作本轮结果。

### 步骤 4：参考图生图最小验证（会话动作）

- 文件：specs/.../image-redraw-checklist.md、design.md（只回填真实证据）。
- 操作：使用步骤 3 真实 PPT 导出的参考图，而不是旧的直接生图样张；提供完整准确文字清单与明确的输入角色，请会话工具重绘。此为“有参考图编辑”的最小试验，和阶段 2 直接生成图区分。
- 检查方法：image_gen 工具调用记录、输入/输出哈希、逐字逐数字核对、实际尺寸和视觉记录；不写不存在的自动化调用命令。字体字形/尺寸依人类批准口径验收。
- 通过条件：画面协调、文字/数字/近超等全部保留；可核对真实输入来自 v1；最多 3 轮修复，失败则回到方案，不继续正式模块。

检查点 B：步骤 3～4 通过后回填 spike 结论；至此仍只验证关键路径。若需要改方案，重新确认；按已批准方案通过才进入正式实现。

### 步骤 5：落实可执行的单页输入

- 文件：specs/.../deck-outline.md、specs/.../style-params.md、specs/.../m1-input.json。
- 操作：把已确认内容整理为阅读快照与唯一机器源，加入布局、安全区及素材占位路径，保留源文案及统计限定词。
- 验证命令：.venv/Scripts/python.exe -m json.tool specs/2026-10-18-m1-single-slide/m1-input.json（语法检查）；对照已确认文案与页脚，记录批准输入哈希。
- 通过条件：单页内容完全一致，所有视觉参数有明确值；缺少的真实素材不能假装已存在。

### 步骤 6：最小输入验证入口

- 文件：src/config.py、src/outline.py、src/m1.py。
- 操作：先只实现 validate 子命令；集中环境覆盖与项目相对路径，检查数据结构、唯一 ID、画布、文本框、字号与素材路径。素材尚未生成时明确输出缺失，不标记 ready。
- 验证命令：.venv/Scripts/python.exe -m src.m1 validate --input specs/2026-10-18-m1-single-slide/m1-input.json；使用错误字段/非法框/缺图数据验证非零退出，不需要永久新增测试框架。
- 通过条件：有实际可运行入口；合法结构与缺失素材分别清楚报告，无硬编码个人路径。

检查点 C：步骤 5～6 的输入、验证语义及来源哈希一致。

### 步骤 7：生成独立背景与插画

- 代码文件：无新增模块；会话动作更新 specs/.../image-redraw-checklist.md。
- 产物：assets/m1-single-slide/bg_01.png、ill_01.png、source-record.json，记录提示词/来源/时间/可获取的模型信息/哈希与真实尺寸。
- 操作：根据确认参数先生成留出安全区的背景，再生成透明插画；不把旧整页图剪成背景/插画，不烘焙任何文字。
- 检查命令：再次运行步骤 6 的 validate，确认图片存在/可读/背景比例与插画 alpha；会话查看素材并交人类确认后继续组装。

### 步骤 8：实现单页 v1 构建

- 文件：src/builder.py、src/m1.py。
- 操作：实现 build；背景最底层、独立插画、原生文字；每个 shape 有业务 ID 与层角色；同步最小 manifest。所有文本通过 text_fit；任何 None 令构建失败，不能把失败产物称为成功。
- 命令：.venv/Scripts/python.exe -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide。
- 通过条件：1 页且形状类型/数量符合输入；原生文字可编辑，插画独立；重开核验与 manifest 对应。M1 不要求自动生成多个版式。

检查点 D：步骤 7～8 通过，得到来自独立素材与原生文本的真实 v1。

### 步骤 9：辅助导出与几何/内容核对

- 文件：src/render.py、src/checks.py、src/m1.py。
- 操作：实现 check，复用 spike 证实的最小逻辑；生成辅助 PDF、参考 PNG、checks.json。按上文几何策略区分背景/主体安全区/文本；抽取结果、允许叠放及待复核项可追溯。
- 命令：.venv/Scripts/python.exe -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide。
- 通过条件：无缺页、缺字、越界、非预期碰撞或字体替换；失败退出非零，未知映射不伪装通过。参考 PNG 经视觉核对后交人类检查 v1。

### 步骤 10：v1 确认后准备最终重绘与验收

- 文件：src/m1.py、specs/.../image-redraw-checklist.md。
- 操作：用户确认 v1 后，通过明确的 --v1-confirmed 参数准备输入包；这是记录已有确认，不是让程序自动代用户确认。输入哈希变化则再次确认。会话查看 v1 参考图、背景与插画，按准确文案清单调用 image_gen 整页重绘。
- 命令：.venv/Scripts/python.exe -m src.m1 prepare-image --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide --v1-confirmed。
- 通过条件：最终生图对应通过检查且用户确认的 v1；准确文字/数字与来源逐项一致、无旧免责尾句；AI 初检和人类视觉验收分别记录；未验收只标记等待。

检查点 E：步骤 9～10 通过，才认定 M1 内容链路完成。用户改 v1 后自动 diff 不在本次范围；修改后先人工同步输入再重跑，不混用旧 manifest。

### 步骤 11：同步产品流程与实现说明

- 文件：src/README.md、README.md、.ai/product-sop.md、.ai/knowledge/architecture.md。
- 操作：写清真实能力与命令、LO/生图分工、v1 确认及生图后核对；保留未来 M2～M6 规划但不声称已经实现；引用既有文案约定。
- 验证：文档中的命令与实际 CLI --help 对照执行，引用文件存在，图中流程与实现状态一致。

### 步骤 12：同步已验证风险与验收条目

- 文件：.ai/02-feasibility.md、.ai/04-coding.md、.ai/05-review.md、.ai/knowledge/pitfalls.md。
- 操作：定点更新旧的 HTML 唯一路线断言、辅助渲染角色、生图内容检查、已复现的文本边界及真实搜索方式。不把尚未复现的猜测写为已验证事实。
- 验证：检索旧路线断言并逐项对照，保留仍适用的未来选项；不整篇重写规范或替换无关内容。

检查点 F：步骤 11～12 完成，文档不再把本次最终图当作普通导出，也不夸大自动化能力。

阶段 5 收尾：仅更新已认可范围内的 spec.md/design.md，将真实命令输出和证据填入记录，停下等待进入阶段 6。review.md 在阶段 6 按模板创建，不提前写“全部通过”。

## 提交与产物策略

- 保持 feat/m1-single-slide，不运行 setup_git.bat、不重命名分支、不自行合入。
- 当前无任何提交。建议在验证准备具备可复核条件后，先对现有骨架/本任务规范做明确文件清单的基线提交，再按已通过检查点分别提交。已有初始化文件仅纳入本仓库文本资产，不 git add -A，不包含生成图/字体/环境或个人路径记录。
- .gitignore 继续排除 assets/、output/、fonts/ 本体和 .venv/。需入库的规格/设计去掉本机绝对路径，使用相对路径和角色说明；此前记录的本机诊断路径只留必要摘要，提交前在 spec.md 中清理为可复用表达。
- 首次提交涉及原有未跟踪骨架的纳入，须在本方案批准时同时确认；本次不修改 setup_git.bat，也不创建/推送远程仓库。
- 一次运行有独立 run_id/输入哈希，保留当前旧样图。不覆写他人素材；同一次运行输出可原子替换，失败不得读取陈旧产物。具体 run 目录记录在最新状态文件，运行成功与接受状态分开。

## 专项检查

1. 中文：唯一入口 text_fit；10pt 下限；显式行距/换行与 PDF 检查；None 失败。
2. 字体：v1 三处使用同套静态思源字体并验证，最终 PNG 的精确字形边界待人类批准。
3. v1/v2：v1 可编辑，PNG 为本次展示交付；二者共用输入哈希与准确文案；不额外承诺整图 PPT。
4. 改动识别：仅最小 manifest 供核对和交接，不做 diff；用户修改需要同步输入后重跑。
5. 素材：内置工具生成，背景无字、透明插画独立；原始生成记录和核对表落盘，不复制参考素材。
6. 版权：从公开内容提取风格方向；字体官方许可登记；不把来源图片自动视为可商用。
7. spike：计划脚本已命名，尚未创建/执行。先审批本验证设计的流程安排；通过后才能将真实结论回填为“已验证”。

## 关键决策与备选

| 决策点 | 推荐 | 备选与取舍 |
|---|---|---|
| 接入 | 已选的会话生图工具 | API 可指定型号，但需额外接入与重新验证，本次不引入。 |
| 执行源 | 单个 JSON，Markdown 为阅读确认快照 | Markdown 通用解析器增加歧义与范围，M1 暂不开发。 |
| 构建记录 | builder 同步最小 manifest | 单独 manifest 模块留 M2；完全无记录则几何与素材交接难追溯。 |
| 字体 | v1 静态思源，PNG 验收气质与可读性 | 精确像素字形要求会改变整页生成路线，不能默认采用后期补字。 |
| 尺寸 | v1 严格 16:9，最终图保留原生尺寸并核对比例 | 严格 2560×1440 需工具支持或另获后处理授权，不能假称已满足。 |
| 检查 | v1 自动几何/内容＋最终图逐项目视 | 自动 OCR 要新依赖且不能代替人工，暂不引入。 |
| 实现节奏 | 批设计后先环境/spike，通过后业务模块 | 未经设计先写脚本违反 AGENTS；虚写 spike 结论同样不可接受。 |

## 找茬自审（每项两处失效与应对）

| 决策 | 可能出错 1 → 应对 | 可能出错 2 → 应对 |
|---|---|---|
| 会话接续 | Python 无法直接调用工具 → 输出包交给会话，不伪造 API | 换会话缺少素材上下文 → 索引、哈希、文字清单及角色落盘 |
| 唯一执行源 | Markdown 与 JSON 分叉 → 明确执行源并人工对照；变更失效旧确认 | 编辑 v1 后仍用旧 JSON → 本次不做自动闭环，人工同步再检查 |
| manifest | shape_id 与输入 ID 不同 → 两者同时记录 | 图片换了但路径未变 → 使用文件哈希关联，不只比路径 |
| 字体 | LO 悄悄替换 → 核对 PDF 字体并视觉查看 | 模型不能精确复现字体 → 人类明确批准最终图口径，不能冒称一致 |
| 尺寸 | 工具忽略尺寸提示 → 记录实际尺寸、核对宽高比 | 为追求尺寸裁掉文字 → 不擅自裁切或拉伸，请求模型修复 |
| 几何 | 背景与所有文字相交造成误报 → 按层角色与主体安全区检查 | 字符提取但被图遮住 → 参考图视觉检查，不能只看文本层 |
| spike/提交 | 首次复现卡住 → 子进程超时与明确失败 | 无基线全量纳入产物 → 显式暂存清单、忽略规则、检查后才提交 |

## 已确认决策

人类已明确回复“同意三项，确认方案”，以下三项推荐组合全部确认，无遗留阻塞问题。

1. **验证顺序与代码授权边界**：是否批准“确认本设计后，阶段 5 先做环境与 spike；通过并回填证据后才正式实现，失败/变更则回退”的具体衔接？这明确处理当前规范冲突，不代表 spike 已通过。
2. **字体与像素验收口径**：是否接受 v1 严格使用白名单静态思源字体；最终生图验收无衬线风格与可读性，不承诺精确字形；最终 PNG 保留原生尺寸，16:9 比例偏差≤0.5%，不强制固定 2560×1440？
3. **最小范围与提交**：是否接受 JSON 执行源＋最小 manifest，交付 v1/PNG/辅助文件/报告，暂不封装整图 v2 PPT；在当前 feature 分支用显式文件清单建立骨架基线并按通过的检查点提交？不推送、不合入。

## 人类确认

- 确认人：项目维护者（本会话用户）。
- 日期：2026-10-18。
- 已确认内容：本方案及上述三项，原话“同意三项，确认方案”。
- 阶段 4 状态：质量门通过，进入阶段 5；没有将尚未运行的 spike 视为通过。

## 资料依据（只读核实，非运行验证）

- [Adobe 思源黑体官方发布](https://github.com/adobe-fonts/source-han-sans/releases)：静态字体可作为首选来源。
- [官方 SIL OFL 1.1 许可](https://github.com/adobe-fonts/source-han-sans/blob/master/LICENSE.txt)：字体使用许可依据；实际下载与证据登记尚未执行。
- [python-pptx 文本对象](https://python-pptx.readthedocs.io/en/latest/api/text.html)：文本框/段落支持换行、行距与字体设置；不代替本机 LO 实测。
- [PyMuPDF TextPage](https://pymupdf.readthedocs.io/en/latest/textpage.html)：rawdict 提供逐字符内容与几何数据，可用于设计上述检查；不是现成的 PPT 溢出检测器。

## 阶段 5 实际执行记录（持续更新）

### 检查点 A：通过

- 隔离环境：Python 3.12.14；python-pptx 1.0.2、Pillow 13.0.0、PyMuPDF 1.28.2。未改应用共享 Python。
- 官方思源静态字体 2.005R 已下载并登记，用户级字体已安装，许可证原文及忠实渲染留证见 fonts/README.md。
- `spike_text_fit.py --probe-old`：真实复现极窄框 2 秒超时。
- 修复后 `spike_text_fit.py`：8 项断行/非法宽度检查＋4 项字号/超量检查通过。
- `src/text_fit.py` 保留 None 失败语义；新增不可前进保护、明确软换行/行距及东亚字体；根据实际 LO 混排差异保留 10% 横向余量。
- 首次基线提交：`2a84b12`，在 feature 分支创建，没有推送。

### 检查点 B：通过最小验证，正式产物未验收

- `spike_render.py --out output/m1-single-slide/spike` 最新结果：`passed=true, slides=1, shapes=10, geometry_issues=[]`。
- 实际 PDF 字体：SourceHanSansSC-Regular / Bold；漏文、越界、碰撞负例均能被拒绝。
- 第一次失败为字体替换；修复 1 使用系统实际家族别名“思源黑体”，字体检查通过但出现行高度量框误报。
- 修复 2：使用 PyMuPDF 的字号高度字框与原有 1pt 容差，不将字体行高框等同可见字框；同时处理混排二次折行的横向余量。本轮通过；没有超过 3 轮修复。
- 输出目录：output/m1-single-slide/spike/3f54457df349/；参考 PNG 为 2560×1440。
- 真实参考图经会话工具重绘为 redraw.png，1672×941，比例符合已批准口径；逐项目视核对准确文案与来源页脚一致。证据和提示词见 image-redraw-checklist.md 引用的运行目录。
- 该重绘是最小试验，尚无人类单独验收；不冒充正式 v1 或最终展示图。
- 额外 OOXML 技能验证工具因其 Python 环境缺少 defusedxml 未运行，未擅自引入新依赖；不声称 XSD 已通过。

### 检查点 C：通过，等待正式素材

- 已落实 deck-outline.md、style-params.md、m1-input.json；JSON 执行源哈希为 `43b940ee92c82081b81b8ba4d8ab18d0447e0452a5a9c52807f174eb698d839d`。
- `python -m src.m1 validate ... --schema-only`：valid_schema=true，ready=false，退出码 0。
- 去掉 --schema-only：明确报告独立背景/插画尚未生成，退出码 2；未把缺图状态称为 ready。
- 重复 ID、负坐标、字号低于 10、来源缺失四类负例均返回 2；compileall 通过。
- 已补 config.py、outline.py、m1.py 最小验证入口，未写 builder/render/checks 正式模块。

### 发现但不碰

- .ai/templates/review.md 原有第 26 行尾随空格；基线空白核查记录该既有问题，未修改范围外模板。后续新增/修改文件保持正常 diff --check。
- Tabbit 路由不可用（exit 69），未切换控制其他浏览器；授权证据采用保存的官方许可证原文渲染并如实标注。

### 检查点 D：通过（2026-10-19）

- 人类对独立背景与透明插画回复“可以”，素材确认已记录；完整输入校验为 valid_schema=true、ready=true、issues=[]。真实尺寸、alpha、提示词和哈希见 assets/m1-single-slide/source-record.json，文件未入库。
- 已实现 builder.py 与 build 入口，所有文本走 text_fit；背景与插画独立。最小 manifest 记录输入/素材/字体哈希、原生对象 ID、层次、坐标及实际字号，PPTX 保存后重开核对。
- 真实命令：`.venv/Scripts/python.exe -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide`。
- 最新输出：passed=true、slides=1、shapes=11；标题 40pt、副标题 26pt、小标题 24pt、正文 20pt、页脚 12pt。
- 运行目录：`output/m1-single-slide/runs/20261018T163215Z-57aaf205/`。文件：`喜茶 2025 年度营销回顾_v1_可编辑.pptx`、manifest.json。
- 初版视觉发现词语拆行和孤立句号；第一轮修复在断行工具增加标点随前字下移保护，并只在输入正文调整显式语义换行。文案字符、数字及限定词不变；修复后重新 build/check 通过，无第二轮修复。
- 新执行源哈希：`c0ee451939f629bd38ce301cd6a3678e8345efb7568dc5ac428862ecfa373435`。检查点 C 的旧哈希保留为历史记录，旧产物未沿用为最新确认。

### 步骤 9：自动检测与 AI 视觉初检通过，检查点 E 待完成

- 实现 render.py、checks.py 与 check 入口，实际命令：`.venv/Scripts/python.exe -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide`。
- 真实输出：passed=true、state=awaiting_v1_confirmation、issues=[]、slides=1、shapes=11。
- 实际 PDF 字体为 BAAAAA+SourceHanSansSC-Bold、CAAAAA+SourceHanSansSC-Regular，无替换；9 个文本块与确认文案逐项一致（忽略布局空白）。
- 辅助 PDF 与 2560×1440 参考图位于本次运行 `render-898dea60/`；报告 checks.json。AI 已查看参考图，未见文字裁切、孤立句号、内容遮挡或“喜茶”“提交”拆行。
- 负例实测：正文 2000 个“茶”在最低字号仍超量，明确失败且不写成功状态/PPTX；检测能拒绝漏文、文本碰撞、文本/插画主体碰撞；改变输入哈希拒绝沿用旧运行。
- 验证扩展：style=[]、canvas=null、schema_version=true、title=123 四类非法结构返回退出码 2 与 JSON 错误，无 traceback；真实 validate 返回 ready=true。
- `.venv/Scripts/python.exe specs/2026-10-18-m1-single-slide/spike_text_fit.py`：修复后 9 项断行/非法宽度检查＋4 项字号/超量检查通过；compileall 与 git diff --check 通过。
- checks.json 中 visual_review/v1_confirmation 仍为 pending：自动生成的报告不代替此处 AI 初检记录或人类确认。latest.json 的 v1_confirmed=false；未执行最终重绘。

### 后续

- 当前停留步骤 9 后的人类 v1 检查点。按步骤 10 与产品 SOP“用户确认后进入 v2”，先交付实际 v1 及预览供检查；不能把素材确认当成 v1 确认。
- 用户确认当前 v1 后，继续 prepare-image、正式整页生图与核对，再执行步骤 11～12 的整体流程文档同步。当前已随结构改动同步 src/README.md、architecture.md，登记已复现的文本问题。
- 已提交：检查点 A/基线 2a84b12；检查点 B 27c4a02；检查点 C b65d427；素材状态记录 4ba86bf。作者身份按用户提供信息仅配置本仓库，没有推送或合入。
- 阶段 5 未完成；不得进入阶段 6 或宣称 M1 已完成。

### v1 文字视觉调整检查点（2026-10-19）：通过，等待新版确认

- 用户反馈“文字部分纯文字可能有点素”，随后明确“继续任务”。保留原生文字与独立素材路径，未推进最终整页生图。
- 三个数据摘要使用可编辑浅茶绿文字框：2025.11、超 100 万份、近 30 款；完整确认句仍在其下，第三组“超 500 万份。”单独突出。content_groups 对照原完整句，不删除限定词、标点或来源。
- 首次调整的预览中大标点不自然，进行 1 轮版式修复：摘要只显示日期/数据，标点保留在完整说明中。没有增加未经来源支持的事实。
- 另有 1 次真实导出未过字体检查；确认原字体文件和注册记录存在但当前会话未枚举，临时加载后实际导出通过。此修复已写入 render.py，并在 LO 退出后释放本次引用；未重装字体、未写共享目录。
- 最新真实 build：passed=true、run_id=20261019T001301Z-b675a7c0、slides=1、shapes=15（13 个原生文字框＋2 张图片）。
- 最新真实 check：passed=true、state=awaiting_v1_confirmation、issues=[]，实际字体 SourceHanSansSC-Regular/Bold。参考图 `output/m1-single-slide/runs/20261019T001301Z-b675a7c0/render-f1c51121/reference.png`；2560×1440。
- AI 已查看本参考图，摘要与说明清晰、无文字裁切/遮挡；保留此前字体、来源、数字和近/超限定词，未新增免责尾句。
- 输入 SHA256：`52c0cd18079dc958e9a6e5f626b4d154b58d4179ea12148ca3dee247ac3df835`；PPTX SHA256：`6b2290edbcfd562702b133a28cc07353b080187e7409d182197c5fc084b8d2f2`。旧运行目录保留，仅最新状态指向本版。
- 负例核查 9 项通过：非法底色/内边距/对齐、删掉限定词、重复/未知组成员，及读回底色/内边距/对齐不一致；旧版 v1 的重开核验仍通过。compileall 通过。
- 字体已加载不直接作为通过依据，仍以真实 PDF 字体/内容/几何报告为准。latest.json 的 v1_confirmed=false，用户尚未确认新版；阶段 5 未完成。

### 步骤 10：v1 已确认，正式重绘及 AI 初检完成（2026-10-19）

- 人类原话：“可以，后续再通过图片渲染来再做美观一点吧，接下来先进行下一步”。确认对象为 run `20261019T001301Z-b675a7c0` 的 15 元素 v1，未将其当成最终重绘图验收。
- 实现 `m1.py prepare-image`。真实命令：`.venv/Scripts/python.exe -m src.m1 prepare-image --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide --v1-confirmed`。
- 真实输出：passed=true、state=ready_for_image_generation、v1_confirmed=true、texts=13。包内含准确文案、完整句分组、参考与素材角色/路径、各项哈希及实际提示词。
- 入口负例通过：未确认、报告哈希改变、报告明确失败（即使更新哈希）、参考图改变均被拒绝，且失败前不写交接目录。合法调用通过，重复准备不倒退已有最终图状态；compileall 通过。
- 补充状态核查：对隔离副本模拟重新 check 失败，返回 1、state=failed，清除旧 v1 确认、生图交接及最终图验收引用；原历史文件保留。生产运行仍为 awaiting_visual_acceptance，没有重复导出或改动已确认 v1。
- 查看真实参考页、背景和透明插画后调用会话 image_gen；使用保存的完整提示词，没有本地 API 模拟调用。底层型号未知；首次即生成，修复 0 轮。
- 保存原图：`output/m1-single-slide/runs/20261019T001301Z-b675a7c0/final/slide-01-image-v1.png`；RGB、1672×941，比例误差 0.0531%，符合已确认≤0.5%口径。精确复制，未后处理。
- 原图哈希 `b50c14eaf8b863dcafe19aaa5aec22bfd2ee751efd723fbf1c427f677e95c8ff`；完整证据 image-review.json。13 项文字/数字/来源逐项目视核对通过；保留正文和摘要，不新增免责声明。
- 提交工具前仅去掉提示词首尾空白，实际文本另存 image-input/submitted-prompt.txt，哈希记录于 image-review.json；没有更改生成图片。
- latest.json 当前为 awaiting_visual_acceptance、v1_confirmed=true、content_reviewed=true、human_accepted=false。检查点 E 的技术链路已具备证据，最终人类视觉验收仍待确认，不能标记 accepted。

### 步骤 11～12：流程同步

- 已同步 README.md、src/README.md、product-sop.md、architecture.md 的真实命令、LO 与模型重绘分工、v1 确认与最终图核对、目前未实现的能力。
- 定点更新 02-feasibility.md、04-coding.md、05-review.md、pitfalls.md，删除“美化必须 HTML”的旧唯一路线断言；区分 v1 自动几何与模型位图目视核对，不冒称 OCR、指定字体或指定底层型号。
- 这是阶段 5 内的实施说明同步；未提前创建阶段 6 review.md，未推送或合入。最终视觉确认后才能收尾阶段 5 并停下汇报。
- 文档验证：实际 CLI --help 列出 validate/build/check/prepare-image，prepare-image --help 与文档参数一致；rg 在本次当前运行说明中未找到旧唯一路线断言。检查点 F 的流程同步已完成；检查点 E 的人类最终视觉验收仍待确认。

### 阶段 5 收尾（2026-10-19）

- 人类回复“可以，继续吧”，确认正式模型原图的视觉效果。当前运行 `20261019T001301Z-b675a7c0`，输入与最终图哈希未改变；image-review.json 记录原话、日期、具体图像哈希，latest.json 更新为 accepted、human_accepted=true。
- 本轮真实完整性核验输出：passed=true、state=accepted、slides=1、shapes=15、geometry_issues=[]、reviewed_texts=13、human_visual_acceptance=passed、size_px=[1672,941]、artifact_hashes_verified=true。核对了 PPTX、manifest、当前字体/图片、检测报告、PDF、参考图、交接包、实际提示词、最终原图与核对记录的关联；没有重新生成或修改已确认图片。

| 检查点 | 收尾结果 |
|---|---|
| A 环境与中文适配 | 通过；极窄框复现后修复，9 项断行/边界＋4 项字号检查通过 |
| B 辅助渲染/模型重绘 spike | 通过；真实 PPT/LO/PDF 与参考图生图证据具备 |
| C 输入与素材校验 | 通过；正例 ready=true，非法字段/缺图负例被拒绝 |
| D 独立素材与正式 v1 | 通过；当前 1 页、13 文本框＋2 独立图片，v1 已获确认 |
| E 真实检测与整页重绘 | 通过；几何/内容/字体检查、13 项最终图目视核对与人类视觉确认具备 |
| F 流程文档同步 | 通过；命令帮助、旧路线断言检索及本地链接核对已执行，文档与实现一致 |

- 主要实现：config.py、outline.py、text_fit.py、builder.py、render.py、checks.py、m1.py；入口、执行源、快照、spike 与证据索引见 src/README.md 和本任务目录。生成文件、字体本体与隔离环境未入库。
- 发现但不碰：原模板尾随空格、Tabbit 路由不可用保持既有记录；额外 OOXML 工具缺 defusedxml，不声称 XSD 通过。阶段 6 可据此评估补充验证，不假称已在 WPS/PowerPoint 实际打开。
- 已实现的 M1 不包含多页、自动 diff、独立生图 API、整图 v2 PPTX 或 skill 打包。accepted 只表示本图获确认，不表示开发审查或合入已完成。
- 阶段 5 待确认问题：无。依 AGENTS 第 9 条在本阶段结束处停下汇报；未创建 review.md、未进入阶段 6、未推送或合入。

## 阶段 6 审查执行（2026-10-19）

- 人类回复“继续”，进入阶段 6。本会话按审查清单自查，不冒称独立会话审查或远程 PR 检查。
- 发现并复现一个阻塞项：隔离副本删除最终图后，prepare-image 仍返回 accepted。第一轮修复在原范围 m1.py 内增加已生成/验收阶段的证据校验及只读复用；无新依赖、无产物重绘。
- 修复核查：缺图、改核对记录、改提示词、改准确文字、改交接包五类负例均被拒绝并标记 failed；有效 accepted 原件复跑只读、状态/提示词/图像等哈希不变。没有第二轮修复。
- 独立审查目录真实运行 build/check：run_id=20261019T004402Z-aa5fbc36、passed=true、slides=1、shapes=15、issues=[]、PDF 为 SourceHanSansSC-Regular/Bold；参考 PNG 与正式已确认 v1 的参考图哈希一致。
- 结构补充：正式 PPTX 41 个 XML/关系文件可解析，42 个内部关系目标与内容类型覆盖引用有效，ZIP 完整，未内嵌字体本体。这些是基础结构检查，不称为 XSD 通过；额外验证器缺 defusedxml 保持如实记录。
- 字体、许可证、两项 AI 素材来源哈希均与登记一致；没有素材/字体大文件入库，未发现源码硬编码密钥或个人路径。证据摘要在 output/m1-single-slide/review-20261019/，正式 accepted 图未改变。
