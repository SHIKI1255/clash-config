# Clash 自有远程分流

适配 Clash Verge Rev 2.5.8 / Mihomo 1.19.32。保留机场节点、凭据、Hosts 和订阅更新；在规则模式下完整替换机场业务规则及 rule-providers。代理出口直接引用机场主选择组，无需新增 PROXY。

| 原订阅 | 代理规则、DNS、下载所用主组 |
|---|---|
| GeekSpeed | GeekSpeed极客加速器 |
| 雪橇云 | 雪橇云 |

主组及其依赖的自动选择、故障转移组保留。雪橇云主组主动选 DIRECT 时，这些流量也直连。订阅名称与主组名称不匹配或脚本异常时，在已安装原生保护覆写的前提下保留基础直连、其余业务拒绝。全局/直连模式不受这套分流保护。

## 安装

- [下载无凭据覆写包](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/clash-overlay.zip)
- [原生保护 guard.yaml](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/guard.yaml)
- [已生成适配脚本 override.js](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/override.js)
- [发布清单与规则计数](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/manifest.json)
- [文件哈希](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/SHA256SUMS)

**这是覆写包，不是 Verge 原生备份 ZIP，也不是节点订阅。** 备份当前全局 Merge/Script，把包内规则缓存复制到配置目录，然后依次替换全局 Merge 和 Script，由使用者手动激活订阅。完整步骤见 [安装、更新与回退](docs/install.md)。不要直接安装 `config/override.js` 模板。

当前两份订阅的专属覆写为空。后置专属 Merge/Script 能覆盖全局结果，新增此类设置后必须核对最终生成配置。仓库不控制客户端界面、端口、系统代理和 TUN 开关。

## 规则能力与顺序

22 条本地保护 → 个人直连 → 个人代理保障 → AI / GitHub / Telegram / Google / Twitter / TikTok / Crypto → SteamCN → Steam → Apple → Microsoft → BiliBili → 通用代理 → 国内集合 → 国内 GeoIP → 主组兜底。

21 个来源条目：blackmatrix7 通用分类、v2fly OpenAI / Anthropic / Google DeepMind / TikTok、OpenAI 官方语音 IP。生成 23 个原生 classical 资源（含两个个人集合）；每个集合只对应一个出口。v2fly 正则原样转为 DOMAIN-REGEX。

远程个人规则包括 15 条进程规则、办公/远控/游戏直连、国内字节例外、GitHub 下载保障、Copilot、OpenAI 登录辅助端点和历史兼容。删除不明 checkout 直连；OpenAI 核心域名与常规 GitHub 域名交由上游。原 GeekSpeed 广告拦截不再默认加载。

只对完全相同且同策略记录去重，保留首次出现位置；不按字母排序，不随意合并不同类型或策略。同选择器的跨策略冲突登记于基线，跨类型的关键优先级由回归用例约束，不能声称穷尽任意正则或进程与域名的所有交集。[逐条手写规则处理](docs/custom-rule-review.md) · [迁移及冲突说明](docs/migration.md)

## DNS

保留 Fake-IP、国内 AliDNS/DoH.pub、境外 Cloudflare/Google 经主组、节点独立直连解析、局域网系统 DNS。域名的 DNS 策略按同一批规则集及顺序匹配；远程个人直连域名同时用于 Fake-IP 和嗅探排除，进程/IP 条目不作为域名解析规则。内核提示 classical 仅匹配域名属于预期提示。

IPv6 跟随传入界面设置；原有 geodata 体系保留。`respect-rules: false`，显式代理 DNS 不会因为切到直连模式自动改为直连。PROCESS-NAME,DIRECT 也不代表绕过 TUN。

## 维护

| 文件 | 用途 |
|---|---|
| `rules/custom.list` | 个人前置规则及原因；DIRECT 块在 PROXY 块之前。PROXY 只是生成器内部标签 |
| `config/sources.yaml` | 来源、策略、顺序、过滤和异常阈值；JSON 形式的 YAML 1.2 |
| `config/override.js` | 主组适配、DNS、资源引用模板 |
| `config/bootstrap.json` | 独立于脚本的本地保护覆写 |
| `tests/routing_cases.json` | 关键策略及实际命中规则检查 |
| `tests/source_baseline.json` | 人工审核的来源数量和冲突基线；不得自动放宽 |

源码在 main；发布文件、来源快照、固定提交、哈希和许可证在 release。规则缓存地址形如 `https://raw.githubusercontent.com/SHIKI1255/clash-config/release/rules/personal_direct.list`，其他地址由发布脚本引用。

GitHub 在 main 修改、手动触发和每日北京时间 06:17 构建；内核每 86400 秒刷新规则。先解析上游提交再固定下载，失败保留上一发布。规则下载失败有旧缓存时沿用；**首次无缓存失败可导致空集合**，必须先放置随包快照、核对加载计数，不能只看“运行中”。各集合客户端刷新不是原子操作。

域名/IP/进程内容可自动更新；集合数量、策略、顺序、DNS 架构及脚本修改需手动同步覆写包。机场节点订阅更新独立运行，GitHub 不接触私有订阅。

每 30 天提交真实维护检查结果，失败也如实记录；仅受信任 main 工作流可写，遇并发主分支变化跳过，不强推。维护提交不递归构建。若 GitHub 已停用定时任务，需要手动启用和运行；调度也可能延迟。

## 验证与回退

Python 3.12 标准库、Node.js。Windows 使用 PowerShell 7。构建目录必须在源码仓库外：

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/build.py --output <新的外部构建目录> --previous-release
python -B scripts/build.py --replay <构建目录> --output <新的外部复建目录>
```

比较两份 SHA256SUMS。CI 还用固定且验证哈希的 Mihomo 1.19.32 在无真实节点、无流量接管的环境检查规则解析、下载失败缓存保留及首次缺失缓存行为。公开 CI 只包含合成数据。

`--audit` 仅生成不可发布候选，不能自动批准新基线。`--replay-commit <完整发布SHA>` 重放旧输入，仍受当前检查约束。恢复旧适配结构必须同时恢复对应源码/包。

回退安装前配置使用本机备份。固定版本把 Raw URL 的 release 换成发布 SHA；需完全冻结规则时，还应按安装文档修改包内引用。首次发布没有更早的本仓库发布版。

本地和 CI 验证证明生成、加载及发布链路；实际网页、游戏、远控、语音和首次自动刷新由使用者另行验收。来源许可及官方资料见 [第三方说明](docs/third_party.md)。
