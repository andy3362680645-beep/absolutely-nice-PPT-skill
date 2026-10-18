# fonts 字体目录

字体文件较大（单个 10MB+），**不纳入 git**（.gitignore 已排除）。请按下面清单下载后放入本目录，或在统一配置中指向系统字体路径。

## 测量/渲染/PPT 三处字体必须一致

`src/text_fit.py` 测量用的字体文件、LibreOffice 渲染用的系统字体、PPT 中指定的字体名，必须是同一套字体，否则字号计算失效。

## 推荐首批下载（稳妥办公型，先跑通）

| 字体 | 建议文件名（放入本目录） | 授权 | 获取 |
|---|---|---|---|
| 思源黑体 Regular | `SourceHanSansSC-Regular.otf` | SIL OFL | github.com/adobe-fonts/source-han-sans/releases |
| 思源黑体 Bold | `SourceHanSansSC-Bold.otf` | SIL OFL | 同上 |

> 首推单家族（思源黑体，靠字重分层），投影与打印最稳。跑通后可按 `.ai/knowledge/fonts.md` 扩展商务型/发布会型搭配。

## 白名单（可商用，使用前到官网核对最新授权）

思源黑体、得意黑、阿里巴巴普惠体、庞门正道标题体（免费版）、优设标题黑、站酷高端黑、MiSans、OPPO Sans、HarmonyOS Sans、阿里妈妈数黑体。

## 授权登记（每引入一款字体必须登记）

| 字体全名 | 协议类型 | 获取日期 | 来源 URL | 授权截图位置 | 是否允许分发 |
|---|---|---|---|---|---|
| Source Han Sans SC Regular / Bold，2.005R 静态 OTF | SIL OFL 1.1 | 2026-10-18 | [Adobe 固定版本](https://github.com/adobe-fonts/source-han-sans/releases/tag/2.005R)、[许可证原文](https://raw.githubusercontent.com/adobe-fonts/source-han-sans/2.005R/LICENSE.txt) | `fonts/SourceHanSans-license-evidence-01.png`、`-02.png`（下载原文的忠实渲染留证，非网页截图）；原文 `fonts/SourceHanSans-LICENSE.txt` | 本任务只输出 PPT/图片，不随产物分发字体 |
|  |  |  |  |  |  |

### M1 实际字体记录（2026-10-18）

- 内部家族名：`Source Han Sans SC`；字重 `Regular` / `Bold`，Pillow 已读回确认。
- 下载路径：官方 `2.005R/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf` 与 `SourceHanSansSC-Bold.otf`，均来自 `raw.githubusercontent.com/adobe-fonts/source-han-sans/`。
- Regular SHA256：`F1D8611151880C6C336AABEAC4640EF434FA13CBFBF1FFE82D0A71B2A5637256`。
- Bold SHA256：`DF2B90F5BCC6D01DFC964CEC5F6D535D6B6AEBD26ED7FD79A9C1B3F2112FCB6B`。
- 许可证原文 SHA256：`FCAC737E761EC63DBFBDCE11030A1780161920D80315EDBA9C8BEFF1C2BAC5A2`。
- 已安装至当前用户字体目录，未修改系统共享字体目录；实际 LibreOffice PDF 中的字体仍需由渲染 spike 核实。
|  |  |  |  |  |  |

## 合规提醒

- **免费商用 ≠ 可分发**：可以用字体输出商业 PPT；把字体文件随模板/产品打包分发，通常需要单独确认。
- SIL OFL 允许修改与再分发，但衍生字体必须改名。
- 引入字体三步走：确认全名 → 查协议并截图留证 → 核对使用场景（仅输出画面 vs 分发）。
- 详见 `.ai/knowledge/fonts.md`。

## 提示

- Windows 安装字体后，LibreOffice 可直接使用字体名；未安装的字体需通过本目录字体文件进行测量，并在 v2 渲染环境中确保字体可用。
- v1 交付给他人时，若对方电脑未安装字体，可编辑版可能回退默认字体；v2 整图版不受影响。
