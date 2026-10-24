# absolutely-nice-PPT-skill

> PPT_agent：制作与优化 PPT 的 AI skill。Let’s try it—you won’t forget it.

制作与优化 PPT 的 AI skill（后续演进为 Agent）。

制作流程：**确定主题与受众 → 检索内容资料和真实图片 → 确认逐页大纲 → 真实文案灰阶线稿与总览 → 确认密度和布局 → 看参考图选风格 → 原创素材及正式整页模型渲染 → 核对交付。**

课堂/文献采用大字图解、就近解释与适量重点标注，工作/品牌按场景选风格。谢谢/交流独立成末页并计入总页数。[场景字号](.ai/knowledge/visual-profiles.json)是制作和审查依据，历史10pt技术值不作为正文投影标准。

- **双模式**：熟悉主题就逐页填空；不熟悉主题就先和 AI 头脑风暴，最后汇成同一份逐页大纲。
- **默认交付**：准确大纲、线稿、正式模型图片及约定的展示PPT/PDF；可编辑PPT按需提供。默认修改内容从大纲开始，更新受影响线稿和正式页。
- **风格选择**：AI展示实际参考图片供选择，或使用用户提供的理想图，自动提取设计参数并组织原创提示词，用户无需掌握提示词。
- **自然文案与个人偏好**：原创规则去空泛口号和免责套话，保留必要论证；经确认的长期偏好独立保存，可查看、修改、删除或迁移，不随公共包分发。宿主无持久读写能力时采用可携带档案。
- **自动改动识别（规划）**：原生v1的自动diff仍未完成，不与按大纲人工定位混称。
- **风格与真实性**：从参考模板只提取风格参数；原创背景/装饰由AI生成，用户要求真实产品时核对图源、使用权和保真要求，字体只用可商用白名单。

## Skill入口与复用约定

[SKILL.md](SKILL.md)是仓库内入口，区分“使用skill做PPT”和“开发本仓库”。内容制作必读[文案与来源约定](.ai/knowledge/content-style.md)；选图、生图和交付必读[视觉制作与交付约定](.ai/knowledge/visual-workflow.md)。

线稿、风格及个人偏好分别见[线稿布局](.ai/knowledge/wireframe-layouts.md)、[原创风格提示词](.ai/knowledge/style-prompts.md)、[偏好协议](.ai/knowledge/user-preferences.md)。空白模板可分发，私人实例放.local/ppt-agent/preferences.md或用户指定的私有位置。参考风格只提取一般规律，AI重绘不自动排除版权风险。

开发源、安装副本与独立发布快照分别维护。复用时保留SKILL.md引用的.ai/、src/、fonts/README.md等资源，准备宿主工具与依赖。`src.release`提供白名单构建与核验；实际发行以检查结果为准，不自动更新安装目录。只纳入原创且确认的样例，不分发私人资料、参考照片和字体本体。[早期经验留档](specs/2026-10-21-skill-lessons/retrospective.md)保留当时范围。

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
7. 需要远程协作时，按 `.ai/git-workflow.md` 使用任务分支和 Pull Request；禁止直接向 `main` 提交。

## M1 当前能力

新增`python -m src.presentation_audit inventory/check`可读取跨宿主成品及附加角色说明，未知项明确列出，结果不替代看图。`python -m src.release build/verify`用于独立分发；参数见[src说明](src/README.md)。接收方用[同一试题](.ai/templates/cross-host-trial.md)复测，未跑平台不能登记已验证。

已确认大纲/风格 → 会话生图生成独立素材 → 单页可编辑 PPT（中文自适应）→ LO 辅助导出及几何/内容检查 → 用户确认 v1 → 生图交接包 → 会话工具整页重绘 → 逐字/数字与视觉核对。

四个本地命令及运行条件见 [src/README.md](src/README.md)。样例执行源为 [m1-input.json](specs/2026-10-18-m1-single-slide/m1-input.json)，开发证据见 [design.md](specs/2026-10-18-m1-single-slide/design.md)。首张正式重绘已获人类视觉确认，代码、画面与素材来源检查通过，维护者已批准本次成果作为后续开发基础；仓库已提供 skill 入口及独立发行构建、核验能力。[验收说明](specs/2026-10-18-m1-single-slide/review.md)列出了交付物、当前限制与检查记录，实际合入记录见 Git 历史。

历史最终展示图使用会话image_gen工具重绘，底层型号未知，没有独立API接入。本地保留M1单页、M2实验多页可编辑构建、逐页检查、跨宿主成品审查及独立发行核验。新默认流程由宿主按规范执行，不是这些Python命令已自动跑通的新引擎；本次没有新增线稿样张或跨平台实际视觉验证。

## 日常怎么和 AI 协作

开工时对 AI 说：

> 先读 AGENTS.md，按 `.ai/00-workflow.md` 走六阶段流程。现在进入阶段 1，先复述需求并提问，不要写代码。

如果是要让 AI 做 PPT（产品流程），说：

> 按 `.ai/product-sop.md` 开始，先判断我是模式 A 还是模式 B，并逐页确认大纲。

## 关键约束

- 中文文本字号自适应只能用 `src/text_fit.py`，不要用库自带的 `fit_text()`（对中文失效，见 `.ai/knowledge/pitfalls.md`）。
- 不直接使用参考模板里的图片、插画、字体；只提取风格参数。
- 每个开发任务都走 git 分支 + PR，不直接改 main。
