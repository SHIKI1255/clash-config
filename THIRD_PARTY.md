# Sources and licensing

The shared producer resolves immutable upstream commits before downloading. See
`sources.lock.json`, `licenses/`, and `SHA256SUMS` in each release.

- `v2fly/domain-list-community`: MIT (`licenses/v2fly.txt`); AI, GitHub, Telegram domains,
  Google, X, TikTok, Crypto, Steam, Apple, Microsoft, BiliBili, curated overseas domains, and `cn`.
- `MetaCubeX/meta-rules-dat`: GPL-3.0 (`licenses/metacubex.txt`); `meta` branch `geo/geosite/gfw.list`.
- `https://openai.com/chatgpt-voice.json`: official published OpenAI voice IP data. Archived without
  asserting a license grant.
- `https://core.telegram.org/resources/cidr.txt`: official published Telegram IPv4/IPv6 CIDR data.
  Archived without asserting a license grant.

Original generator, orchestration scripts, and documentation are licensed under `GPL-3.0-or-later`.
Generated collections remain source-attributed. No provider subscription or private node information
is an input to CI.
