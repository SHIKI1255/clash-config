# SHIKI1255-Rules | Clash

公共域名、上游来源、分类、顺序和回归用例集中在[唯一维护入口](https://github.com/SHIKI1255/shadowrocket-config/tree/main/shared)。本仓库保留客户端模板和发布；不要另建一份个人规则清单。

适用 Clash Verge Rev 2.5.8 / Mihomo 1.19.32。在规则模式完整替换机场业务规则，保留节点、凭据、Hosts、订阅更新及主组选择。GeekSpeed 使用 GeekSpeed极客加速器；雪橇云使用雪橇云，选择 DIRECT 时该组也直连。不创建额外 PROXY。

下载[无凭据覆写包](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/clash-overlay.zip)，按[安装说明](docs/install.md)复制缓存，先装 guard.yaml 再装 override.js，由你手动激活。它不是 Verge 原生完整备份 ZIP。

新版加载 20 个 shiki_ 分类资源。23 份缓存文件中包含 3 个旧地址兼容文件；不增加节点组。脚本失败或未知主组时保留本地保护并拒绝其他业务，不能恢复机场分流。

保留 Fake-IP、国内/境外 DNS 路径、节点独立解析、MetaCubeX geodata。Clash 的 classical DNS 域名提示为预期提示；语音 IP 不参与 DNS 选择。局域网共享、端口、TUN、IPv6 均由客户端界面管理。

## 维护与更新

公共修改只在 https://github.com/SHIKI1255/shadowrocket-config/tree/main/shared 进行。平台 DNS/基础模板在本仓库 config 中；config/shared.json 是协议/分类结构契约，结构变化需要审阅后同步本地模板。

GitHub 每日北京时间 07:17、main 修改及手动触发构建。消费者固定公共发布 SHA 并校验数据，只读取资源，不执行远程代码。[当前发布清单](https://raw.githubusercontent.com/SHIKI1255/clash-config/release/manifest.json)中的 shared_version 用于核对三端版本。沿用 30 天维护记录；不承诺构建后手机立即刷新。

下载失败、未知语法/协议、异常增删、未知冲突或用例失败均保留上一版。首次无缓存失败不算安装成功；Clash 必须核对缓存加载。

普通域名规则自动刷新；主配置、资源结构、DNS 架构及适配脚本变化需手动同步。机场订阅和 Hosts 模块仍独立维护，不把私有订阅放到 GitHub。

## 验证与回退

Python 3.12 标准库，Windows 使用 PowerShell 7；Clash 还运行 Node 适配和隔离 Mihomo 检查。

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/build.py --output <新的仓库外目录> --previous-release
python -B scripts/build.py --replay <构建目录> --output <新的离线目录>
```

两次 SHA256SUMS 必须一致。固定版本将 release 替换为发布 SHA；完全冻结还需冻结内部资源地址。恢复本地备份由使用者操作，不自动重载应用。手机解析、实际联网、语音与后台刷新另行验收。

[公共规则与必要平台差异](https://github.com/SHIKI1255/shadowrocket-config/tree/main/shared) · [第三方许可](docs/third_party.md)
