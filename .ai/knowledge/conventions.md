# 编码约定

> 所有代码遵守。新约定在蒸馏中确认后加入。

## 通用

- Python 3.10+；统一在虚拟环境中运行。
- 小函数、单一职责；每个模块文件顶部写模块用途。
- 公共函数写 docstring：参数、返回值、异常、单位。
- 路径、字体、画布尺寸、字号上下限等常量集中在配置中，不写死盘符和用户名。
- 写文件函数幂等：重复运行不产生重复文件、不覆盖素材（除非明确要求）。
- 不提交任何 token、密钥、个人路径。

## 单位与画布（PPT 坐标）

- 1 inch = 914400 EMU；1 pt = 12700 EMU（`pt = emu / 12700`）。
- 72dpi 下 1px = 1pt。
- 默认画布 16:9：13.333in × 7.5in（python-pptx 默认 16:9）。
- 文本框可用尺寸 = 宽高减去四边内边距（`margin_left/right/top/bottom`）。

## 中文文本

- 唯一字号自适应入口：`text_fit.best_font_size()` / `text_fit.cjk_wrap()`。
- 行距系数 1.2；默认字号上限 24pt、下限 10pt；放不下返回 None。
- 禁止对中文调用库自带 `fit_text()`。
- 文本框统一设置 `word_wrap=True` 与 `MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE`。

## 文件与命名

- 素材：`assets/{deck_id}/bg_01.png`、`assets/{deck_id}/ill_01.png`；插画透明底。
- 产物：`output/{deck_id}/{主题}_v1_可编辑.pptx`、`{主题}_v2_展示版.pptx`、`slides/slide_01.png`、`manifest.json`。
- 任务留档：`specs/YYYY-MM-DD-任务名/`。
- 命名用英文小写连字符；含中文主题的产物文件名保留中文。
- 生成的图片、pptx、pdf、字体本体不入库。

## 字体

- 从 `fonts/` 或统一配置读取字体路径；PPT 字体名按 fonts.md 映射。
- 新增字体必须先在 `fonts/README.md` 登记授权。

## 错误处理

- 外部依赖（LibreOffice、生图 API、文件读取）失败要给出明确报错与下一步建议，不静默吞掉。
- 内容超量、字号到底、素材缺失等"用户可处理"的问题，以结构化方式返回，由上层提示用户。

## 验证

- 关键路径改动必须附最小验证脚本与真实输出。
- 新增渲染/排版逻辑，至少用 3~5 页样例大纲验证。
