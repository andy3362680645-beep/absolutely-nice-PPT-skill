# 技术方案 · 跨 AI 的 PPT 制作流程与视觉质量

> 2026-10-23，维护者在收到本设计后回复“继续推进”，已确认本方案并进入阶段 5。下方方案保留原设计内容，实际执行结果在文末追加；没有实测记录的项目仍为计划。

## 先给人看的方案

这次让 skill 清楚地带 AI 完成：**确定主题 → 检索内容 → 确认逐页大纲 → 网上检索风格 → 生图制作对应素材 → 制作并确认可编辑稿 → 整页模型协调 → 核对交付**。

课堂/文献使用大字、内容图解、就近解释和少量重点标注的预设。商业与工作汇报保留适合各自场景的风格。谢谢/交流独立成页；这些要求先在可编辑稿落实，再进入最终生图美化。

另外提供读取成品 PPT 的检查工具。它核对实际对象和字号，明确列出需要人工看的项目；不依赖其他 AI 必须调用本项目的组装器。用四类原创样页验证后，发布一个包含规范、工具和可编辑样页的新包，保留旧包与原有开发工作。

本轮交付不包含豆包专用接口、自动改动识别或自动审美评分。豆包未实际试跑前，兼容状态保持待验证。

## 一、范围与兼容约束

- 任务分支：`feat/cross-ai-visual-workflow`。只暂存本任务明确列出的文件，不使用 `git add -A`，不合并或推送主线。
- 正式文件清单以 spec.md 阶段 3 表格为准：产品规范、模板、三个场景配置、两个新 Python 模块、使用说明与关联质量门。`src/text_fit.py` 仅修正文档/注释。
- 新模块为 `src/presentation_audit.py` 与 `src/release.py`；新增配置和模板为 `.ai/knowledge/visual-profiles.json`、`.ai/templates/presentation-audit.json`、`.ai/templates/cross-host-trial.md`。
- 保留 M1/M2 输入、manifest、运行状态及函数接口；不修改 builder、outline、checks、render、config、m1、m2 实现。新检查是附加检查，不授予旧记录新的 accepted 状态。
- 保留 M2 与 GM 汇报已有未提交文件、字体本体、旧素材与所有旧发布快照。不修改个人安装目录。
- 本任务留档限于本目录的 spec/design/review/retrospective，以及 `spike_presentation_audit.py`、`spike_emphasis.py`、`build_visual_sample.py`。如需修改范围外实现，先回报并修订方案。
- 素材：`assets/cross-ai-visual-workflow/`；过程与交付：`output/cross-ai-visual-workflow/`。每个运行目录拒绝覆盖已有结果。

## 二、制作流程与场景标准

### 2.1 产品流程质量门

| 环节 | 必须留下的结果 | 推进条件 |
|---|---|---|
| 主题 | 受众、场景、时长、页数、主要结论和交付范围 | 缺少会改变制作方向的信息时先补齐。 |
| 内容检索 | 内容依据、数据/原文位置、可用图片与来源，区分用户资料、补充资料和个人建议 | 无依据事实不进入确认稿；尊重模式 A 用户自己的核心观点。 |
| 逐页大纲 | 每页标题、核心结论、准确文案、主要表达形式、重点词、视觉目的、来源和讲稿备注 | 用户确认；独立谢谢/交流页计入总页数。 |
| 风格检索 | 相关主题/场景的网上参考，实际查看范围，以及从中提炼的视觉参数 | 用户确认风格；用户已给参考一并使用，无法访问的页面如实登记并换可访问来源。 |
| 素材生图 | 按页制作独立背景、插画和必要图案，记录工具、提示词与用途 | 先看一个样张确认风格，再批量；不把插画数量当成质量目标。 |
| 可编辑稿 | 可修改文字、准确原生数据对象及独立图片；实际参考图与检查结果 | 用户确认当前版本。内容或版式变化后重新核对确认范围。 |
| 整页协调 | 当前确认参考页、准确文字、背景、独立插画与装饰共同输入模型 | 实际调用生图工具；保留原生输出及输入/输出关联。 |
| 核对交付 | 内容/数据/来源核对、逐页与整套视觉检查、可编辑稿和展示原图 | AI 自检与人类验收分开记录；最多 3 轮修复同一问题。 |

资料充足、已有确认内容可以复用，不要求用户重答；风格检索从已确认内容出发，不以先选模板替代内容规划。模式 A 与模式 B 共用后续流程，外部检索不擅自改写模式 A 的结论。

### 2.2 字号配置：一个数值来源

`visual-profiles.json` 使用 schema_version=1，基准画布 `[960, 540]` pt，包含 `classroom-diagram`、`work-report`、`brand` 三个 profile。每个 profile 独立保存下表的最小字号与建议范围；配置中的数值是唯一机器依据，其他说明引用它。

| 文字角色 | 最低字号 | 课堂/工作建议范围 | 品牌建议范围 |
|---|---|---|---|
| title | 32 | 36–44 | 40–52 |
| heading | 26 | 28–32 | 28–36 |
| body | 22 | 24–28 | 24–30 |
| data_label（含表格文字） | 18 | 18–24 | 18–24 |
| source | 12 | 12–14 | 12–14 |
| page_number | 12 | 12–14 | 12–14 |
| thanks | 36 | 44–56 | 44–60 |
| contact | 18 | 20–24 | 20–24 |

- schema 顶层字段：`schema_version`、`base_canvas_pt`、`profiles`。每个 profile 包含 `label`、`roles`，每种文字角色包含 `min_pt` 与两元素 `recommended_pt` 数组；字段数值为正且 min 不大于建议范围上端。
- 相同比例画布按高度/540 等比例换算字号阈值。当前自动配置只覆盖 16:9，相对比例误差允许 0.5%；其他比例标为需要单独确认配置，不套用基准值宣称已验收。
- 标题通常高于正文，主体按内容建立层级；不保留旧的“所有标题必须正文两倍”规则。自动报告显示实际字号分布，标题/正文视觉层级由审查判断。
- 低层适配默认值 24/10pt 和行距 1.2 保持兼容；制作时显式传入当前角色下限。放不下先精简、图解、重排或调整页数，不将正文缩至技术下限。
- 来源、页码不能用作大段正文的角色替代。角色标注的语义是否正确列为人工审查项，工具展示这些对象的完整文字便于核对。
- 字体沿用已登记的思源黑体 Regular/Bold，正式 v1 的测量字体、PPT 字体与实际导出字体一致。无需新增字体或依赖。

### 2.3 构图与重点表达

- 课堂预设以浅底、深色大标题、蓝青色分组标题和深色正文为起点。过程适用横向图解，比较适用图文对照，数据页让图表成为主要视觉。参考照片的投影偏色与课堂环境不提取为风格。
- 每页先确定阅读顺序和主表达，给插画实际可见主体完整区域，图表解释就近放置。调整图片时联动正文、表格列宽和行高。不机械设置占满率、图片数量或固定图文比例。
- 强调色、加粗与荧光笔式底纹支持少量关键词或结论；建议每页 1–3 组，具体服从内容。颜色之外保留字重、位置或文字标签辅助理解。
- 使用宿主原生文字 runs、独立重点短句或可编辑底纹形状实现强调。图表刻度、标签、公式和数据关系继续用准确原生对象；生成的示意图承担解释角色。
- 谢谢/交流页为末页、单独一页。资料页与内容评价排在此前；独立结束页不放正文要点、数据图或表格。用户之后明确要求不同结构时，先更新大纲和该任务检查说明。
- 背景、透明插画与装饰分别准备；最终协调提示词包含准确文字、每项素材用途、风格和不可改变项，不能让模型重新拟写文案。

## 三、独立检查接口

### 3.1 命令与路径

新增模块提供两个子命令，均不修改输入 PPTX：

```powershell
python -m src.presentation_audit inventory --pptx <文件.pptx> --out <对象清单.json>
python -m src.presentation_audit check --pptx <文件.pptx> --map <角色说明.json> --out <新报告目录> [--pdf <辅助.pdf>] [--profiles <配置.json>]
```

- 用户给定的相对路径按当前工作目录解析；只有未指定的默认 profiles 从模块所在包内读取，避免安装目录和任务目录混淆。
- inventory 输出当前文件 SHA256、画布、逐页/逐对象标识、文字、类型与可读样式，角色初始为 `unknown`。宿主 AI 依据已确认大纲填写，再运行 check。
- 文件输出和报告目录拒绝覆盖，失败保留可读错误。CLI 错误信息使用通俗中文，不要求终端用户理解 XML。
- 公共接口固定为 `inventory_presentation(pptx_path: Path) -> dict` 与 `audit_presentation(pptx_path: Path, mapping: dict, profiles: dict, pdf_path: Path | None = None) -> dict`；CLI 负责输入读取、输出落盘和退出码，审查函数保持只读。

### 3.2 角色说明

附加角色说明 schema_version=1，与原 M1/M2 manifest 独立：

| 字段 | 含义 |
|---|---|
| `pptx_sha256` | 所检查文件的实际字节哈希；文件变化需重新 inventory 和核对角色。 |
| `profile_id` | 三个预设之一。 |
| `require_thanks` | 本次完整汇报默认 true；仅检查抽取的单页片段可明确设 false，并在报告标明片段检查范围。 |
| `slides` | 按真实页序排列的列表，必须覆盖全部页面。 |
| 每页 `slide_index`、`pptx_slide_id` | 1 起始页序与文件内 slide ID，两者共同校验。 |
| 每页 `kind` | `cover` / `content` / `appendix` / `thanks`。 |
| 每页 `message` | 本页确认的主要意思，供人工核对，不当作真实性证明。 |
| 每页 `objects` | 每个叶对象的 `shape_path`、`role`。组合对象用 shape ID 路径定位，不能依赖不唯一的名称。 |

文字角色按上表；图片/图形另有 `background`、`illustration`、`decoration`，未判断的用 `unknown`。对象显示名称仅作辅助信息。重复、失配 ID 或 hash 不同是错误；存在未知角色、未覆盖对象或无法处理的对象是待核查，不能输出完整技术通过。

`.ai/templates/presentation-audit.json` 作为字段示例与填写说明的配套模板，不伪装成与任何真实文件绑定的检查证据。真实说明从 inventory 产生；填写前必须阅读 src 使用说明。

### 3.3 本轮检查边界

| 项目 | 本轮实现方式 | 不能确认时 |
|---|---|---|
| 页数、角色绑定 | 核对文件哈希、真实页序、slide ID 和 shape ID 路径 | 绑定错误为 failed；标注不完整为 requires_review。 |
| 正文字号 | 从 run 显式字号、段落直接默认值、当前文本体对应级别默认值依次读取；记录字号来源 | 占位符、母版或主题继承仍无法确定时不猜默认 18pt，标 requires_review。 |
| 自动缩放 | 记录 normAutofit/fontScale，区分存储值和 PDF 观察值 | 存储值不证明渲染值；无实际 PDF 时将可能缩放的文字标待核查。 |
| 文本、表格 | 扫描非空 runs；普通表格按单元格角色检查，合并格需正确识别主格和跨度 | 不支持的合并或特殊版式列出对象，不能跳过后当通过。 |
| 原生图表 | 识别图表类型；本轮验证二维折线/柱形图中显式字号的标题、坐标标签及数据标签；缓存文字/数值用于清单 | 继承标签、3D/特殊图表、公式布局等列待核查，不把图表缓存文本视为全部可见文字。 |
| 公式与上下标 | 识别可读到的公式/基线偏移标记并列出位置 | 单独数学对象、上下标的缩放可读性列待核查，不把公式小字直接当普通正文判定。 |
| 越界 | 普通未旋转顶层对象与画布比较；真实 PDF 文字另核对字符框 | 旋转、翻转、缩放组合对象仍列清单，无法确定可见范围时标待核查。 |
| 结束页 | require_thanks=true 时恰有一个末页 kind=thanks；禁止其中存在 body/heading、原生表格或图表 | 文本是否把评价伪标成 contact 等仍需人工核对，报告展示结束页全文。 |
| 图文碰撞 | PDF 已关联的非空文字字符核对各自可用区域；文字框交叉和图文交叉列提醒 | 高亮底纹等合法层叠不直接判碰撞，无法分配或有歧义的字符列待核查。 |
| 强调与图案效果 | 清单记录可读到的颜色、字重和图片/图形类型，人工对照重点词与预览 | 本轮不承诺自动判断荧光效果、图案语义、留白质量或科学关系准确性。 |

- 字号误差容差 0.1pt，来自 PPT/PDF 的数值舍入；PDF 字符几何沿用既有检查使用的 1pt 容差，不因失败反复放宽。
- PDF 为可选外部辅助输入，先核对页数与画布尺寸，再按从 PPT 读取的对象区域分配字符、比较文字与观察字号。普通文本仅忽略布局空白，数字、标点与限定词不能忽略。图表/复杂对象不唯一归属时列待核查，不冒称完整逐字比对。
- PDF 与 PPT 均计算实际哈希；这记录了本次检查的文件组合，不单独证明 PDF 的导出工具或人工确认。正式样页使用实际导出记录关联来源。
- 无 PDF 时报告“未执行渲染后文字几何检查”；可读的存储字号与对象边界仍照常检查。与原检查分工明确，不宣称替代所有原检查。
- 生成位图内的文字不反推 pt 字号；可编辑性报告只核对原生对象存在，不用图片数量证明画面完整。

### 3.4 报告与退出码

报告目录含 `audit.json` 和 `审查摘要.md`。JSON 使用 schema_version=1，保存输入哈希、profile 配置哈希、technical_status、errors、needs_review、warnings、逐页观察结果及始终独立的 `visual_review: pending`、`human_acceptance: pending`。

- 退出码 **0**：本次声明范围内客观检查通过，仍等待视觉/人类验收。
- 退出码 **1**：找到小字号、越界、错误绑定、结束页混放等确定问题，或输入无效/处理失败。
- 退出码 **2**：没有确定错误，但存在未知样式、缺失检查、复杂对象等未验证项。
- 状态优先级 failed > requires_review > passed。无 PDF 是未验证项，因此完整 check 不返回 0；片段检查不会伪装成整套验收。

中文摘要先列“哪些页要改、为什么影响阅读、建议怎么改”，再列人工核对项和检查范围。工程字段留 JSON，不给最终用户堆机器日志。

## 四、最小验证与四类样页

### 4.1 先验证，再正式实现

AGENTS.md 要求人类确认 design.md 前不写实现，方案规范又要求关键路径先 spike。本轮先提交本设计，确认后先执行以下最小验证，再补回实测结果；未通过则停下修订方案，不直接编写正式检查器或扩大生成。

1. `spike_presentation_audit.py --probe`：构建技术夹具，检查显式字号、段落继承、未知母版继承、混合 runs、表格、原生二维图表和分组对象的真实读回行为。不依赖尚不存在的正式检查器。
2. `spike_emphasis.py`：用已登记 Regular/Bold 测量同一完整文案，在加粗字体作保守宽度约束的条件下，经 text_fit 求字号与断行，再按同一断行写 runs。验证重点色与可编辑底纹形状，实际 LO 导出、检查全文和字符边界；不新增独立适配算法。
3. 两项通过后，进入配置与正式检查器实现。原探针增加 `--verify-auditor` 模式，对以下正反例执行行为验证：低于阈值、变更文件哈希、漏标对象、评价与谢谢混放、越界、未知样式、缺 PDF，以及正常样页。

技术夹具的纯色图片或简单形状只用于测试文件结构，不充当正式原创插画。若保守测量仍不能稳定处理混合字重，采用独立重点短句与可编辑底纹的已规划方式，不修改 text_fit 算法或旧 builder；记录验证结论。

### 4.2 共用视觉试题

主题固定为 **“把冷链信息讲清楚”**，用于四种排版能力验证，并非指定论文的完整汇报；不使用用户私人论文、参考照片或品牌产品图。

| 页 | 表达目的 | 素材与布局 |
|---|---|---|
| 1 概念图解 | 冷链中的仓储、运输与交接应作为相互衔接的环节理解 | 以原创仓储/运输场景示意和少量说明形成完整图文区域，关键词强调。 |
| 2 流程说明 | 把“发现—核实—处置—复盘”呈现为讲解用的示例流程 | 使用不同于第 1 页的传感器、记录与处置动作插画，原生箭头和大标签连接；示例建议不冒称法规流程。 |
| 3 图表与标注 | 用一条清楚的记录说明“哪里发生变化” | 原生折线图，示例时间 0/1/2/3/4 小时，示例温度 2/3/6/4/3℃；就近重点标注，无安全阈值或真实企业绩效主张。 |
| 4 独立谢谢 | 明确结束与邀请交流 | 大字致谢、适量原创图案和可选联系文字，不混入评价或结论。 |

- 第 3 页就近标“排版演示数据”，属于必要数据性质说明；不添加无用免责声明。样例数值只用于图形准确性核验，不作为查得的事实。
- 先检索内容和适合课堂图解的网上参考，核对第 1 页概念依据，记录实际访问范围。执行源写入本任务 output 下的 `sample-brief.md`，逐页文案和风格交维护者确认后生成素材。
- 本轮候选色板：背景 F8FBFD、标题 20395E、分组 286F83、正文 263445、强调底纹 F5E6A6。按实际参考与确认样张收敛，不从拍摄照片的色偏直接取值。
- 生图素材存 `assets/cross-ai-visual-workflow/{run-id}/`；背景建议 2560×1440，透明插画按构图生成并保存真实尺寸。工具不能锁尺寸时沿用原生输出与已约定比例验收，不拉伸或裁切补齐。
- `build_visual_sample.py` 只负责本任务样页。使用 python-pptx 原生文字、图表、箭头/底纹及独立 PNG，中文调用 text_fit，字体按当前配置。核心属性不写个人姓名、路径或邮箱。
- 命令：`python specs/2026-10-23-cross-ai-visual-workflow/build_visual_sample.py --brief <已确认sample-brief.md> --assets <素材目录> --out <新运行目录>`。脚本同时生成 4 页可编辑 PPT、当前 audit 角色说明、准确文字 JSON 及 sample-record.json；来源与生成信息保持可追溯。
- 样页运行目录含 `editable.pptx`、`presentation-audit.json`、`reference.pdf`、`reference-01.png` 至 `reference-04.png`、审核输出和后续 `model/slide-01.png` 至 `slide-04.png`。script 复用 render 导出函数，保留实际导出与文件哈希。
- 先看第 1 页可编辑参考与图案样张，确认方向后检查整套；用户确认当前 v1 后，先进行第 1 页模型协调最小验证，通过再处理其余页。最终模型图逐字、逐数值、图表几何、字形与整套一致性另核对。
- 模型工具沿用本会话可用路径，不保证底层型号；实施时读取对应生图工具指南。输出先交付逐页原生 PNG，不扩展通用 M5 自动封装能力。
- 最终用户可以独立确认可编辑样页与模型图；进入分发包的仅是已确认可编辑样页和它的参考预览，模型原图另行交付，避免把整页模型图片误认为可编辑效果。

### 4.3 证据与包内样例

sample-record.json schema_version=1，保存本次 brief、素材记录、可编辑 PPT、辅助 PDF 和四张参考图的相对路径/哈希，以及 AI 检查和人类确认范围。人类确认必须绑定 editable.pptx 当前哈希；未确认不发正式包。

`.ai/templates/cross-host-trial.md` 给接收方同一试题与验收标准，要求记录使用平台、实际工具、缺项、实际输出与未验证部分。包内样例放 `examples/visual-sample/`：4 页 editable.pptx、四张完整参考 PNG、去除私人路径后的样例清单。它们来自本轮原创样页，作为学习示例；不包含用户上传的照片、字体或历史素材。

## 五、独立发布接口

### 5.1 命令与产物

```powershell
python -m src.release build --version 2026-10-23-visual-v1 --sample-run <已确认样页运行目录> --out output/releases
python -m src.release verify --folder output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent --zip output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent-2026-10-23-visual-v1.zip [--runtime]
```

- 版本为显式的小写字母、数字、连字符标识，拒绝路径分隔符及已有目录。build 生成独立文件夹、ZIP、文件清单和构建报告；旧版不会被覆盖。
- 公共函数：`build_release(version: str, sample_run: Path, out_root: Path) -> dict`、`verify_release(folder: Path, zip_path: Path, runtime: bool = False) -> dict`。
- 不硬编码 Git/Python 安装路径；Git 仅通过 PATH 做可用时的版本记录，Python 子进程使用 sys.executable。没有 Git 仍可从独立文件夹验证，明确 source_revision 未知。
- 构建时记录来源版本与当前选择文件的实际哈希，并记录是否存在未提交改动。来源版本信息不替代发布文件清单；不能把工作区快照伪装成干净提交。

### 5.2 选文件与生成说明

- 基础允许列表：SKILL.md、AGENTS.md、requirements.txt，`.ai/` 下 Markdown 与本轮两个指定 JSON，`src/` 顶层 Python 文件；不递归收集整个工作区。
- SKILL.md 与核心产品规范按源文件复制，避免发布时拼接旧版核心规则。源码入口同时适用于仓库与独立副本，清楚说明工具条件和当前能力边界。
- 发布版的 `使用说明.md`、`src/README.md`、`fonts/README.md`、`.ai/knowledge/architecture.md` 由 release 模块内明确的发行说明生成：使用相对引用，不依赖 specs；保留所有核心规则入口、新检查指令及 M1 样例/M2 实验状态。原仓库这四份文件不被导出过程改写。
- 说明含主题到最终生图的完整顺序、宿主缺项处理、双版本区别和新版检查；明确 prepare-image 为早期茶饮提示词，不是通用主题渲染器。
- 样例只复制 sample-record 指定并经哈希核对的 editable.pptx 和四张 PNG。另生成包内样例文件清单，不拷贝原运行日志、原照片、绝对路径或用户确认原话。
- 不分发 specs、.git、.venv、缓存、密钥、字体本体、源运行目录或旧输出；不新增开源许可证、不替第三方素材授予许可。

### 5.3 验证与开发隔离

- 验证器核对文件允许列表、哈希与尺寸、ZIP CRC/路径和 folder/ZIP 内容一致性；拒绝软链接、路径穿越及清单外文件。
- 检查实际 Markdown 相对链接与锚点；检查文本中的个人路径、邮箱、凭证模式；样例 PPTX 内检查外部关系、备注与文档属性中是否含私人路径/身份。必要官方 HTTPS 资料链接允许保留。
- 对样例验证 PPT 可重开、恰为 4 页、原生文本与二维图表存在，PNG 真能读取；这些不替代视觉验收。
- `--runtime` 在独立临时提取副本运行 M1/M2/new CLI help、对象 inventory 与新检查 smoke。使用接收环境已有依赖，明确不证明全新机器安装。PDF/字体等只在私有验证副本准备，不回写正式包；新检查存在待人工核查项时如实记录退出 2，不伪称技术全绿。
- build/verify 前后比较选定源文件、受保护旧任务、旧发布快照及 Git 分支/HEAD/status；允许变化只限新 output 结果。本任务正常编码改动发生于发布前，隔离检查不把它们误当发布过程修改。
- 源文件变化和新增输出分别记录，发布过程不创建或切换工作分支、不提交、不安装字体或其他依赖，不编辑个人安装副本。

## 六、实施切片与检查点

以下命令均待方案确认后执行。`python` 代表当前项目已准备好的解释器，仓库中优先使用 `.venv/Scripts/python.exe -B -X utf8`；正式模块命令能由任一具备依赖的宿主调用。每个切片控制在同一责任域、1–5 个正式文件，验证脚本归其验证责任域，不将全部改动混成一次提交。

| 步骤 | 新增/修改文件 | 可运行验证或检查 | 门 |
|---|---|---|---|
| 0 关键路径探针 | 本任务 spike_presentation_audit.py、spike_emphasis.py；design 仅补实测结论 | 两个脚本分别 --probe / 实际导出，保存读回、混合样式与几何结果 | A：两项探针真实通过；不通过先修方案。 |
| 1 统一规范数据 | visual-profiles.json、presentation-audit.json、visual-workflow.md | JSON 可解析，检查 profile 数值和必需字段；逐项对照需求 | |
| 2 成品检查器 | presentation_audit.py，原探针的 --verify-auditor 分支 | CLI help、正常/小字号/未知继承/失配/漏标/越界/混放/缺PDF负例，确认退出码和定位 | B：正常例通过，负例不会假通过，未知例明确退出 2。 |
| 3 制作模板 | deck-outline.md、style-params.md、cross-host-trial.md | 本地链接检查，四类试题能填写完整大纲、风格及角色信息 | |
| 4 产品入口 | SKILL.md、product-sop.md、literature-report.md | skill 入口校验与必读资源链接检查；人工顺读完整八环节与确认点 | C：入口/模板/规范一致，独立结束页与两次生图明确。 |
| 5 字体与约定 | fonts.md、pitfalls.md、conventions.md | 检索旧字号表述，确认技术默认值与场景标准分开，授权白名单未变化 | |
| 6 关联质量门 | 01-intake.md、03-design.md、04-coding.md、05-review.md、templates/review.md | 对照新场景与人工审查字段，只改相关表述，不改变六阶段或确认要求 | D：相关规范无旧阈值冲突，人工/机器验收职责明确。 |
| 7a 低层说明 | text_fit.py，仅注释/docstring | diff 确认无算法、参数、默认值变化 | |
| 7b 使用与架构说明 | src/README.md、README.md、architecture.md | 新旧入口、相对资源与里程碑状态对照检查 | E：现有 M1 全新运行目录 build/check 通过，旧 accepted 证据未写入。 |
| 8 样页验证 | 本任务 build_visual_sample.py；素材与产物只进 assets/output | 先研究、大纲/风格与样张确认，再构建 4 页、导出、运行新检查、逐页看图；v1 确认后模型协调 | F：4 页对象、内容、字号、几何、视觉及版权核对通过；模型图另验收。 |
| 9 发布模块 | src/release.py | build、verify --runtime、篡改文件/漏文件/覆盖旧版本等拒绝行为；只在临时副本测试负例 | |
| 10 交付检查 | 本任务 spec/design/review，收尾 retrospective | 新包隔离核验、源与旧任务/旧快照保护核验；汇总技术与人类视觉证据 | G：分发核验通过，待验证平台明确列出，提交阶段 6 审查。 |

可复跑关键命令：

```powershell
python specs/2026-10-23-cross-ai-visual-workflow/spike_presentation_audit.py --probe --out output/cross-ai-visual-workflow/probe-01
python specs/2026-10-23-cross-ai-visual-workflow/spike_emphasis.py --out output/cross-ai-visual-workflow/emphasis-01
python specs/2026-10-23-cross-ai-visual-workflow/spike_presentation_audit.py --verify-auditor --out output/cross-ai-visual-workflow/auditor-regression-01
python -m src.presentation_audit --help
python -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/cross-ai-visual-workflow/m1-regression-01
python -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/cross-ai-visual-workflow/m1-regression-01
```

文档/配置切片的检查命令如下；命令只证明对应的格式、解析或差异范围，人工顺读仍需按表中质量门记录，不能由命令成功推断设计效果。

| 步骤 | 预计执行的命令 |
|---|---|
| 1 | `python -m json.tool .ai/knowledge/visual-profiles.json`，同样解析 `.ai/templates/presentation-audit.json`；核对上表角色值与 schema 字段。 |
| 3 | `git diff --check -- .ai/templates/deck-outline.md .ai/templates/style-params.md`；新增试题文件另外检查尾部空格，后续由 release verify 核验相对链接。 |
| 4 | `git diff --check -- SKILL.md .ai/product-sop.md .ai/knowledge/literature-report.md`；可用时使用 skill-creator 的 quick_validate.py 校验入口，实际路径从宿主环境获取，不将其变为分发依赖。 |
| 5 | `rg -n -e 10pt -e 14pt -e 18pt -e 下限 .ai/knowledge/fonts.md .ai/knowledge/pitfalls.md .ai/knowledge/conventions.md`，逐条解释保留的低层数值。 |
| 6 | `git diff --check -- .ai/01-intake.md .ai/03-design.md .ai/04-coding.md .ai/05-review.md .ai/templates/review.md`，人工对照仅有本轮相关变更。 |
| 7a | `git diff -- src/text_fit.py`，人工确认只涉及注释/docstring。 |
| 7b | `git diff --check -- src/README.md README.md .ai/knowledge/architecture.md`，再执行上方 M1 两条回归命令。 |
| 8 | `python specs/2026-10-23-cross-ai-visual-workflow/build_visual_sample.py --brief output/cross-ai-visual-workflow/sample-brief.md --assets assets/cross-ai-visual-workflow/sample-01 --out output/cross-ai-visual-workflow/sample-01`；再执行 `python -m src.presentation_audit check --pptx output/cross-ai-visual-workflow/sample-01/editable.pptx --map output/cross-ai-visual-workflow/sample-01/presentation-audit.json --pdf output/cross-ai-visual-workflow/sample-01/reference.pdf --out output/cross-ai-visual-workflow/sample-01/audit-v1`。 |
| 9、10 | 执行第五节的 build 与 verify --runtime 命令；负例在单独临时复制目录验证，不损坏正式发布产物。 |

运行失败时不复用旧结果；已存在目录使用新的明确编号，不重命名失败问题来绕过最多 3 轮限制。检查点通过后仅提交本任务相关文件，先汇报真实结果；阶段 5 全部完成后仍需阶段 6 人类审查，当前无合并授权。

## 七、关键决策、备选与找茬

| 决策 | 采用 | 备选与取舍 | 两个可能出错点及应对 |
|---|---|---|---|
| 视觉预设 | 课堂图解独立，其他场景按风格参数 | 所有场景同一模板易失去品牌适配，未采用 | ①大字撑爆旧内容：返回精简/图解/页数取舍；②按照片机械复制配色：只提炼设计方法并看样张。 |
| 数据兼容 | 保留旧 schema，新检查附加角色说明 | 改 M1/M2 共用 manifest 会影响未验收任务，未采用 | ①附加说明过期：绑定真实哈希；②把正文误标成来源：报告全文并人工核对，不能宣称自动语义验证。 |
| 字号读取 | 解析已验证的显式/局部继承，未知明确列出 | 实现全部 OOXML 样式级联扩大范围，未采用 | ①继承值 None 被当 18：禁止默认猜值；②自动缩放改变显示：核对真实 PDF，缺检查返回 2。 |
| 重点标注 | 原生 runs/独立短句和底纹，先测量后施加样式 | 扩展旧 builder rich-text schema 增加兼容风险，未采用 | ①加粗后变宽：用已登记粗体保守测量并实际导出；②底纹被判碰撞：只检查文字几何，视觉审查图层。 |
| 生图分工 | 先内容对应独立素材，再按确认 v1 整页协调 | 仅最后整页生成无法保证 v1 自身质量，未采用 | ①模型改数值或曲线：逐项核对，只修受影响页；②素材换主体或重复：按逐页分配表与总览核验。 |
| 审查结论 | 机器技术状态与视觉/人类验收分开 | 一个 passed 混合所有质量容易误导，未采用 | ①退出 0 被当成品验收：摘要明确仍需视觉确认；②未知项被警告吞掉：needs_review 使退出码为 2。 |
| 独立分发 | 白名单快照，带原创 v1 样例与完整预览 | 整仓库复制会泄露资料，只有规则文件又缺直观示例 | ①样页嵌有私人身份/路径：检查 PPT 属性、备注及关系；②源规范与发布入口漂移：核心规范原样复制，发行说明逐项校验。 |

## 八、专项回答、状态与确认

1. **中文处理**：text_fit 为唯一字号适配入口；当前角色阈值显式传入，超量返回内容/版式阶段。normAutofit 仅兜底，真实 PDF 继续核查。
2. **字体**：沿用已登记思源黑体 Regular/Bold，核对实际导出字体。不分发字体本体，接收方准备自己的可用字体。
3. **v1/v2**：规范两者共用；新检查主要检查真实 v1，v2 位图另做准确文字和图表关系核对，不从位图推断 pt 或对象可编辑性。
4. **改动闭环**：本轮不实现自动 diff；附加角色说明不修改原 manifest。PPT 变化需重新导出、检查并记录确认。
5. **素材与模型**：提示词依据当前大纲、场景和素材用途，记录真实工具与输出尺寸；背景和独立插画分别保存，最终整页协调包含全部准确文字与来源。
6. **版权**：网上参考只提炼参数。样例使用本轮原创插画与原生数据对象；必要资料引用追溯来源，不复制用户照片、模板字体或私人论文。
7. **spike 状态**：尚未执行，路径和预期行为已锁定。确认本设计后先执行步骤 0，通过再进入正式实现；失败回到本方案，不伪造实测结论。

### 待确认问题

无未决需求或接口选择。未知外部能力与复杂对象作为明确的检查边界和验证门保留，不以待定默认值进入实现。

### 人类确认

- 确认状态：**已确认**，2026-10-23，维护者在本方案呈现后回复“继续推进”。
- 早先的“继续推进”确认阶段3范围并授权编写方案；方案呈现后的继续授权已确认本设计。最终样页仍分别确认。
- 本轮确认将覆盖：上述产品顺序、字号配置、独立检查边界、先最小验证再实现、四类样页，以及独立发布方案。
- 样页内容/风格、当前 v1 和模型最终图仍在对应制作质量门分别确认，不从开发方案批准推断为视觉验收。

### 本阶段文档检查记录

2026-10-23 实际执行只读检查：8 个必需设计章节全部存在；spec/design 尾部空格为 0；SKILL、README、.ai、src 的正式文件差异为空；拟议实现/探针文件尚不存在；spec 对 design 的本地引用目标存在。检查输出 `Passed: true`。该结果只证明本阶段文档和未提前实现的状态，不代表步骤 A–G 已执行或通过。

## 阶段 5 实测记录

### 检查点 A：最小验证通过

- `spike_presentation_audit.py --probe --out output/cross-ai-visual-workflow/probe-01`：退出 0，显式正文 26pt、段落继承 24pt、表格 22pt、图表标签 18pt 均读回；未知继承为 null，组合对象需要单独坐标处理。
- 强调探针首次运行在沙箱内临时字体加载受限，未得到导出结果；不记为排版修复。保留 emphasis-01 失败目录。
- 在允许临时加载已授权字体的执行环境重跑，输出 emphasis-02：退出 0、`passed: true`，2 个可编辑 runs、30pt、文字完整、字符未越界，真实 PDF 同时包含 SourceHanSansSC-Bold/Regular；LO 退出 0，临时字体引用已释放。
- 相关结果分别保存在 probe-01/result.json 与 emphasis-02/result.json，后续正例检查引用 emphasis-02 的实际 PPT/PDF，不复用失败目录。
- 结论：可以实现独立审查与原生强调，不需要改变 text_fit 算法或 M1/M2 数据结构。

### 检查点B至G收尾证据

对象检查正反例、规范/模板、M1回归、四页可编辑样例与独立发布核验均已真实执行，命令和结果见review.md。v1获用户明确认可，四张整页模型图已生成及AI自检，人类确认仍待答；阶段6尚未开始。

### 学术密度反馈与补充方案（待确认）

用户认可画面风格，要求学术/论文分析有足够文字和论证；当前最终视觉未获通过。具体规则调整、影响范围与第3页上屏文案见[修订草案](academic-density-revision.md)。先确认补充方案再改样页实现，保留旧版，重新确认受影响v1后再模型协调；暂不进入阶段6。

### 学术密度修订确认与执行

用户明确回复“认可，按此调整规则和第3页”，补充方案与大纲已确认。7份产品规则/模板已同步修改，样例脚本仅改第3页。sample-academic-02构建检查退出0，technical_status=passed，errors=[]，needs_review=[]；新版v1尚待人类确认后才重渲染第3页，未构建新包。

## 最新阶段5收尾状态

学术密度规则与第3页修订已实施，新v1获确认，第3页实际模型图亦获用户明确认可。visual-v2包的49文件、73处引用及5项独立入口/对象读取检查通过，55个受保护历史文件不变。具体命令见review.md。阶段5完成，停下等待进入阶段6的继续指令；未推送、未合并，豆包实测仍待验证。
