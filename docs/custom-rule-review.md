# 原全局脚本逐条迁移记录

核对日期：2026-10-12。原脚本通用前缀 80 条；旧服务组出口在此统一记为 PROXY，发布脚本直接使用机场主组。新远程个人规则 52 条，其中进程规则 15 条；本地保护 22 条。

| 原规则 | 本轮处理 |
|---|---|
| `IP-CIDR,127.0.0.0/8,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,10.0.0.0/8,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,100.64.0.0/10,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,169.254.0.0/16,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,172.16.0.0/12,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,192.168.0.0/16,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,224.0.0.0/4,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR,255.255.255.255/32,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR6,::1/128,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR6,fc00::/7,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR6,fe80::/10,DIRECT,no-resolve` | 保留：本地基础保护 |
| `IP-CIDR6,ff00::/8,DIRECT,no-resolve` | 保留：本地基础保护 |
| `DOMAIN,localhost,DIRECT` | 精简：本地 DOMAIN-SUFFIX,localhost 同范围覆盖 |
| `DOMAIN-SUFFIX,localhost,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,lan,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,local,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,home.arpa,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,msftconnecttest.com,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,msftncsi.com,DIRECT` | 保留：本地基础保护 |
| `DOMAIN-SUFFIX,erp.lingxing.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,feishu.cn,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,feishu.net,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,larkoffice.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,feishucdn.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,ziniao.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,uuyc.163.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,uu.163.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,snssdk.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,bytedapm.com,DIRECT` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,checkout.mzxnyysm.com,DIRECT` | 删除：不明个人例外及其派生解析记录 |
| `PROCESS-NAME,Feishu.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,Lark.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,ziniao.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,ziniaobrowser.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,ziniao-gateway.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,GameViewer.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,GameViewerHealthd.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,GameViewerServer.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,GameViewerService.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,biubiu.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,bbupdate.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,EpicSeven.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,DQJL.exe,DIRECT` | 保留：远程个人规则 |
| `PROCESS-NAME,Twitch Drops Miner (by DevilXD).exe,PROXY` | 保留：远程个人规则 |
| `PROCESS-NAME,Codex.exe,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,github.com,PROXY` | 交给上游：github |
| `DOMAIN-SUFFIX,githubusercontent.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,githubassets.com,PROXY` | 交给上游：github |
| `DOMAIN-SUFFIX,github.io,PROXY` | 交给上游：github |
| `DOMAIN,ghcr.io,PROXY` | 交给 GitHub 上游后缀规则 |
| `DOMAIN-SUFFIX,chatgpt.com,PROXY` | 交给上游：openai |
| `DOMAIN-SUFFIX,openai.com,PROXY` | 交给上游：openai |
| `DOMAIN-SUFFIX,oaistatic.com,PROXY` | 交给上游：openai |
| `DOMAIN-SUFFIX,oaiusercontent.com,PROXY` | 交给上游：openai |
| `DOMAIN-SUFFIX,ct.sendgrid.net,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,intercom.io,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,intercomcdn.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,cdn.openaimerge.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,cdn.workos.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,challenges.cloudflare.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,forwarder.workos.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,humb.apple.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,images.workoscdn.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,js.stripe.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,o207216.ingest.sentry.io,PROXY` | 保留：远程个人规则 |
| `DOMAIN,o33249.ingest.sentry.io,PROXY` | 保留：远程个人规则 |
| `DOMAIN,rum.browser-intake-datadoghq.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,setup.workos.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,workos.imgix.net,PROXY` | 保留：远程个人规则 |
| `DOMAIN,openai-api.arkoselabs.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,client-api.arkoselabs.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,api.statsig.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN,events.statsigapi.net,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,featuregates.org,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,copilot.com,PROXY` | 保留：远程个人规则 |
| `DOMAIN-SUFFIX,copilot.cloud.microsoft,PROXY` | 保留：远程个人规则 |
| `GEOSITE,openai,PROXY` | 交给对应远程专项集合，保留原生正则 |
| `GEOSITE,anthropic,PROXY` | 交给对应远程专项集合，保留原生正则 |
| `GEOSITE,google-deepmind,PROXY` | 交给对应远程专项集合，保留原生正则 |
| `GEOSITE,tiktok,PROXY` | 交给对应远程专项集合，保留原生正则 |

## 新增或补强

- 精确 WorkOS 登录端点 `frontend-apps-multi-region.workos.com`。
- AliDNS、DoH.pub、DNS.pub 和 NTP 的基础解析保障。
- Cloudflare、Google 代理 DNS 入口。
- `ipstatp.com` 保留原雪橇云 TikTok / GlobalMedia 集合中的后缀覆盖，避免替换来源后丢失。
- ChatGPT 语音改用官方 IP 清单。上游规则及旧机场广告规则的行为变化见 migration.md。
