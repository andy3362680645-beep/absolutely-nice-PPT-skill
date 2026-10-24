# 9页插画分配 · 8类主体

用户指出两张第6页试稿复用了相同的右侧画面，并认为仅新增两张插画偏少。本轮实际补齐4张，连同前轮2张与既有2张，共8类不同主体。背景不计入8类。

两张用户截图是同一页的表格版和条形图版过程稿，不是两张不同的正式页。此前未清楚区分。条形图版因比例错误保持弃用；当前仅提供改换为双人培训画面的表格版，不再将旧单人图作为最新效果展示。

## 逐页安排

| 页 | 已备主体 | 素材文件 | 使用方式 |
|---|---|---|---|
| 1 | 冷藏车 | assets/gm-cold-chain-report/style-sample-v1/truck-01.png | 封面主视觉，后续正文不再复用 |
| 2 | 冷却罐与制冷机组 | assets/gm-cold-chain-report/enrichment-v1/milk-cooling-tank.png | 历史背景图表旁的小插画 |
| 3 | 冷库货架 | assets/gm-cold-chain-report/v1/warehouse.png | 企业基础与储运衔接的场景 |
| 4 | 计算器与砝码 | assets/gm-cold-chain-report/enrichment-v2/ife-calculation.png | IFE示例表与公式旁点缀，无实际显示值 |
| 5 | 精确的原生量表图 | 不额外复用其他页插画 | 数据和口径为主体，保持清楚 |
| 6 | 双人培训讨论 | assets/gm-cold-chain-report/enrichment-v2/staff-training.png | 支持人员能力与质量管理主题，替代旧单人检查画面 |
| 7 | 记录仪、探头与清单 | assets/gm-cold-chain-report/enrichment-v1/temperature-logger.png | 对应监测与改进措施，屏幕无数值 |
| 8 | 放大镜与文献 | assets/gm-cold-chain-report/enrichment-v2/evidence-review.png | 文献证据核查与研究评价 |
| 9 | 双箭头、勾选与齿轮 | assets/gm-cold-chain-report/enrichment-v2/feedback-loop.png | 反馈闭环的小型概念元素，实际流程继续用原生图形 |
| 10 | 致谢与原创背景 | assets/gm-cold-chain-report/v1/cover-background.png | 用户新增结束页，复用背景，不增加重复主插画 |

最新比例修订：第2、3、4、7、9页插画已经放大并重新分配图文区域。第7页从135×175图片框调整为415×415，主体等比显示；表格列宽与断行同时调整。第9页闭环画面成为右侧主要视觉，不再作为角落小图。最新版本见layout-v1-review.md。

## 已执行核对

- 8个独立文件全部存在，哈希各不相同，均为1254×1254 RGBA并包含0–255透明通道。
- 已查看生成输出：主体按页变化，统一白/银、深蓝、青绿及柔和光线；未添加品牌、实际温度读数或研究数据。
- 第6页最新图为1672×941，原生输出保存，16:9相对比例误差约0.0531%；人物换为双人培训，表格文字、10个数值、35.5%及来源目视核对，未见遮挡。没有执行OCR。
- 新素材不等于每页放大图；方法、结果和评价页以表格/图表为主，按剩余安全区调整图片比例，不硬塞。
- 最新预览：output/gm-cold-chain-report/enrichment-preview-v2/slide-06-preview.png。
- 完整提示词、输入与输出记录：同目录prompt-set.json、generation-record.json；实际工具为会话image_gen，底层型号未知。
- 用户回复“可以，继续推进”确认本表安排后，8类素材已全部装入9页增强可编辑稿，各页主体未重复；第5页继续以准确原生量表图为主。
- 最新可编辑稿、实际PDF预览和逐页图位于output/gm-cold-chain-report/enriched-v1/；具体版本与检查见[增强版检查说明](enriched-v1-review.md)。整套最终v2尚未生成。
