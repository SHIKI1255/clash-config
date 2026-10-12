# Sources and licensing

The builder resolves immutable upstream commits before downloading. See
sources.lock.json, snapshots/, licenses/ and SHA256SUMS in each release.

- blackmatrix7/ios_rule_script: GPL-2.0; native Clash lists and domain-only lists.
- v2fly/domain-list-community: MIT; OpenAI, Anthropic, Google DeepMind and TikTok.
- OpenAI chatgpt-voice.json: official published network data. Archived without
  asserting a license grant; official endpoint/domain documentation belongs to OpenAI.

Builder and publication code adapted from SHIKI1255/shadowrocket-config; no online
dependency on its release branch. Generated collections remain source-attributed.
No provider subscription or private node information is an input to CI.
