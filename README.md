# PPT_agent

制作与优化 PPT 的 AI skill（后续演进为 Agent）。

- **双模式**：熟悉主题就逐页填空；不熟悉主题就先和 AI 头脑风暴，最后汇成同一份逐页大纲。
- **双版本交付**：v1 可编辑 pptx（文本框 + 独立插画，可直接拖动修改）；v2 整页渲染版（美观、跨设备不跑版）。
- **改动闭环（规划）**：在 v1 上改 → 自动识别改动 → 只重渲染受影响页。
- **风格与真实性**：从参考模板只提取风格参数；原创背景/装饰由AI生成，用户要求真实产品时核对图源、使用权和保真要求，字体只用可商用白名单。

## Skill入口与复用约定

[SKILL.md](SKILL.md)是仓库内入口，区分“使用skill做PPT”和“开发本仓库”。内容制作必读[文案与来源约定](.ai/knowledge/content-style.md)；选图、生图和交付必读[视觉制作与交付约定](.ai/knowledge/visual-workflow.md)。

已沉淀：展示版实际使用生图模型、逐页变化且整体统一、真实产品图与模型创作分开、原图确认后再做画面融合、文案不加空泛免责句、报告先让人看懂、确认只覆盖当前产物。

这是项目内入口，尚未自动安装到个人skills目录，也未宣称可脱离仓库独立运行。其他项目复用时保留SKILL.md引用的.ai/、src/、fonts/README.md等资源，按当前环境配置依赖；样例照片、字体本体和历史输出不随入口直接分发。[本次经验留档](specs/2026-10-21-skill-lessons/retrospective.md)记录了适用范围与检查结果。

## 目录说明

```
PPT_agent/
├── SKILL.md             # 产品skill入口与复用必读路由
├── AGENTS.md            # AI 协作总纲（最高准则，人和 AI 都读）
├── .ai/                 # 流程规范、模板、知识库
│   ├── 00~06-*.md       # 开发六阶段规范
│   ├── git-workflow.md  # git 分支/PR 规范
│   ├── product-sop.md   # 带用户做 PPT 的流水线
│   ├── templates/       # 文档模板
│   └── knowledge/       # 字体、架构、约定、踩坑记录
├── src/                 # M1 校验/组装/辅助导出/检测/生图交接与中文适配
├── fonts/               # 放字体文件（不入库，按 README 下载）
├── assets/              # 生成的背景/插画（不入库）
├── output/              # 产出的 pptx/pdf/png（不入库）
└── specs/               # 每个开发任务的留档（入库）
```

## 第一次使用：环境准备（Windows）

1. 安装 **Python 3.10+**（安装时勾选 Add Python to PATH）。
2. 安装 **LibreOffice**（辅助 PDF/参考图与检查用）：https://www.libreoffice.org/download/ ，配置直接的 soffice.com/exe，不使用会改名的包装脚本。
3. 安装 **Git for Windows**：https://git-scm.com/download/win
4. 在项目目录打开终端，安装依赖：
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. 按 `fonts/README.md` 下载白名单字体，放入 `fonts/`。
6. 依 `.ai/git-workflow.md` 在 feature 分支开发；当前仓库已初始化，无需重复执行初始化脚本。提交通过的检查点，由人类审查后合入。
7. 需要远程协作时，按 `.ai/git-workflow.md` 关联远程仓库；本次样例仅本地分支，未推送。

## M1 当前能力

已确认大纲/风格 → 会话生图生成独立素材 → 单页可编辑 PPT（中文自适应）→ LO 辅助导出及几何/内容检查 → 用户确认 v1 → 生图交接包 → 会话工具整页重绘 → 逐字/数字与视觉核对。

四个本地命令及运行条件见 [src/README.md](src/README.md)。样例执行源为 [m1-input.json](specs/2026-10-18-m1-single-slide/m1-input.json)，开发证据见 [design.md](specs/2026-10-18-m1-single-slide/design.md)。首张正式重绘已获人类视觉确认，代码、画面与素材来源检查通过，维护者已批准本次成果作为后续开发基础；已提供仓库内skill入口，独立打包与完整自动化仍在后续路线中。[验收说明](specs/2026-10-18-m1-single-slide/review.md)列出了交付物、当前限制与检查记录，实际合入记录见 Git 历史。

最终展示图使用当前会话的 image_gen 工具重绘，底层型号未知；没有独立 API 接入。M1交付为v1 PPTX、模型原生PNG、辅助PDF/参考图和核对记录。M2多页能力正在建设，部分检查点已通过，正式五页交付尚未完成验收；整图v2 PPTX、自动diff与独立skill打包仍在后续路线中。修改v1后先人工同步输入再重跑。

## 日常怎么和 AI 协作

开工时对 AI 说：

> 先读 AGENTS.md，按 `.ai/00-workflow.md` 走六阶段流程。现在进入阶段 1，先复述需求并提问，不要写代码。

如果是要让 AI 做 PPT（产品流程），说：

> 按 `.ai/product-sop.md` 开始，先判断我是模式 A 还是模式 B，并逐页确认大纲。

## 关键约束

- 中文文本字号自适应只能用 `src/text_fit.py`，不要用库自带的 `fit_text()`（对中文失效，见 `.ai/knowledge/pitfalls.md`）。
- 不直接使用参考模板里的图片、插画、字体；只提取风格参数。
- 每个开发任务都走 git 分支 + PR，不直接改 main。
