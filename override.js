// SHIKI1255-Rules | Clash. Generated release replaces the two placeholders. Install guard.yaml FIRST.
// Rule mode only. Does not mutate ports, mode, TUN or the system proxy switch.
function main(config, profileName) {
  const sources = [{"id": "personal_direct", "policy": "DIRECT"}, {"id": "personal_proxy", "policy": "PROXY"}, {"id": "openai", "policy": "PROXY"}, {"id": "claude", "policy": "PROXY"}, {"id": "gemini", "policy": "PROXY"}, {"id": "voice", "policy": "PROXY"}, {"id": "copilot", "policy": "PROXY"}, {"id": "github", "policy": "PROXY"}, {"id": "telegram", "policy": "PROXY"}, {"id": "google", "policy": "PROXY"}, {"id": "twitter", "policy": "PROXY"}, {"id": "tiktok", "policy": "PROXY"}, {"id": "crypto", "policy": "PROXY"}, {"id": "steam_cn", "policy": "DIRECT"}, {"id": "steam", "policy": "PROXY"}, {"id": "apple", "policy": "DIRECT"}, {"id": "microsoft", "policy": "DIRECT"}, {"id": "bilibili", "policy": "DIRECT"}, {"id": "proxy", "policy": "PROXY"}, {"id": "china", "policy": "DIRECT"}];
  const baseline = ["IP-CIDR,127.0.0.0/8,DIRECT,no-resolve", "IP-CIDR,10.0.0.0/8,DIRECT,no-resolve", "IP-CIDR,100.64.0.0/10,DIRECT,no-resolve", "IP-CIDR,169.254.0.0/16,DIRECT,no-resolve", "IP-CIDR,172.16.0.0/12,DIRECT,no-resolve", "IP-CIDR,192.168.0.0/16,DIRECT,no-resolve", "IP-CIDR,224.0.0.0/4,DIRECT,no-resolve", "IP-CIDR,255.255.255.255/32,DIRECT,no-resolve", "IP-CIDR,::1/128,DIRECT,no-resolve", "IP-CIDR,fc00::/7,DIRECT,no-resolve", "IP-CIDR,fe80::/10,DIRECT,no-resolve", "IP-CIDR,ff00::/8,DIRECT,no-resolve", "DOMAIN-SUFFIX,localhost,DIRECT", "DOMAIN-SUFFIX,lan,DIRECT", "DOMAIN-SUFFIX,local,DIRECT", "DOMAIN-SUFFIX,home.arpa,DIRECT", "DOMAIN-SUFFIX,msftconnecttest.com,DIRECT", "DOMAIN-SUFFIX,msftncsi.com,DIRECT", "DOMAIN,dns.alidns.com,DIRECT", "DOMAIN,doh.pub,DIRECT", "DOMAIN,dns.pub,DIRECT", "DOMAIN-SUFFIX,pool.ntp.org,DIRECT"];
  const list = value => Array.isArray(value) ? value : [];
  const uniq = values => Array.from(new Set(values));
  const fail = message => { throw new Error('Personal routing: ' + message); };
  const nodes = list(config.proxies);
  const groups = list(config['proxy-groups']);
  const groupMap = new Map(groups.map(g => [g.name, g]));
  const nodeNames = new Set(nodes.map(p => p.name));
  if (groupMap.size !== groups.length || nodeNames.size !== nodes.length) fail('duplicate names');
  if (groups.some(g => nodeNames.has(g.name))) fail('node/group name collision');
  // Existing profiles use the same exact name as their main selector.
  // Unknown layouts stop under the native guard; never guess the first select group.
  const target = groupMap.get(profileName);
  if (!target || target.type !== 'select') fail('profile name must match one main select group');
  if (typeof target.name !== 'string' || /[,&\r\n#]/.test(target.name)) fail('unsafe selector name');
  const mainName = target.name;
  const builtin = new Set(['DIRECT', 'REJECT', 'REJECT-DROP', 'PASS', 'PASS-RULE']);
  const retained = new Set();
  function visit(name, stack) {
    if (builtin.has(name) || nodeNames.has(name)) return;
    if (stack.includes(name)) fail('group cycle');
    if (retained.has(name)) return;
    const group = groupMap.get(name);
    if (!group) fail('missing group reference');
    if (!list(group.proxies).length && !list(group.use).length && !group['include-all'] &&
        !group['include-all-proxies'] && !group['include-all-providers']) fail('empty selector');
    retained.add(name);
    list(group.proxies).forEach(next => visit(next, stack.concat(name)));
    list(group.use).forEach(id => { if (!(config['proxy-providers'] || {})[id]) fail('missing node provider'); });
  }
  visit(mainName, []);
  nodes.forEach(p => { if (p['dialer-proxy']) visit(p['dialer-proxy'], []); });
  Object.values(config['proxy-providers'] || {}).forEach(p => { if (p.proxy) visit(p.proxy, []); });
  const kept = groups.filter(g => retained.has(g.name));
  // The main selector keeps its members and choice; automatic groups own periodic checks.
  target.url = 'https://www.gstatic.com/generate_204';
  target['expected-status'] = 204; target.timeout = 5000; target.interval = 0;
  // Preserve metadata exclusion and periodic checks for automatic groups.
  const metadata = new Set(nodes.filter(p =>
    /^(剩余流量|距离下次重置|套餐到期|到期时间|长效[：:]|国内[：:])/.test(p.name) &&
    /^(127\.|0\.0\.0\.0$|localhost$|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)/i.test(String(p.server))
  ).map(p => p.name));
  kept.forEach(g => {
    if (!['url-test', 'fallback'].includes(g.type)) return;
    const real = list(g.proxies).filter(name => !metadata.has(name));
    if (real.length) g.proxies = real;
    g.url = 'https://www.gstatic.com/generate_204';
    g['expected-status'] = 204; g.interval = 300; g.timeout = 5000; g.lazy = true;
    if (g.type === 'url-test') g.tolerance = 100;
  });
  const oldDns = config.dns || {};
  const oldSniff = config.sniffer || {};
  const local = ['localhost', '+.localhost', '+.lan', '+.local', '+.home.arpa'];
  const ncsi = ['+.msftconnecttest.com', '+.msftncsi.com'];
  const domestic = ['https://dns.alidns.com/dns-query#DIRECT', 'https://doh.pub/dns-query#DIRECT'];
  const overseas = ['https://cloudflare-dns.com/dns-query#' + mainName, 'https://dns.google/dns-query#' + mainName];
  const policy = {};
  local.concat(['+.arpa']).forEach(d => { policy[d] = ['system']; });
  ncsi.forEach(d => { policy[d] = domestic; });
  const providers = {};
  sources.forEach(s => {
    const id = 'shiki_' + s.id;
    providers[id] = {type: 'http', behavior: 'classical', format: 'text',
      url: 'https://raw.githubusercontent.com/SHIKI1255/clash-config/release/rules/' + s.id + '.list',
      path: './ruleset/personal-clash/' + s.id + '.list', interval: 86400, proxy: mainName};
    // Domain matching only: process/IP entries do not become DNS selectors.
    // Ordered rule-set policies preserve SteamCN/Steam and Copilot/Microsoft precedence.
    // Official voice ranges contain only IP rules; keep their routing provider, not a DNS selector.
    if (s.id !== 'voice') policy['rule-set:' + id] = s.policy === 'DIRECT' ? domestic : overseas;
  });
  policy['geosite:cn'] = domestic;
  function nodeResolvers(value) {
    const values = typeof value === 'string' ? [value] : list(value);
    return uniq(values.filter(s => typeof s === 'string' &&
      /^(?:(?:https|tls|udp|tcp|quic):\/\/)?[a-zA-Z0-9][a-zA-Z0-9.:-]*(?:\/[^#]*)?(?:#DIRECT)?$/.test(s) &&
      !/^(?:[a-z]+:\/\/)?(?:192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|127\.|0\.0\.0\.0|localhost)/i.test(s)
    ).map(s => s.includes('#') ? s : s + '#DIRECT'));
  }
  const nodePolicy = {};
  Object.entries(oldDns['proxy-server-nameserver-policy'] || {}).forEach(([key, value]) => {
    const values = nodeResolvers(value);
    if (values.length && !/^(rule-set|geosite):/.test(key)) nodePolicy[key] = values;
  });
  Object.entries(oldDns['nameserver-policy'] || {}).forEach(([key, value]) => {
    if (/^(rule-set|geosite):/.test(key) || nodePolicy[key]) return;
    const d = key.replace(/^(\+\.|\*\.)/, '');
    if (!nodes.some(p => typeof p.server === 'string' && (p.server === d || p.server.endsWith('.' + d)))) return;
    const values = nodeResolvers(value);
    if (values.length) nodePolicy[key] = values;
  });
  const clean = xs => list(xs).filter(s => typeof s === 'string' && !s.includes('checkout.mzxnyysm.com') &&
    (!s.startsWith('rule-set:') || s === 'rule-set:shiki_personal_direct'));
  const dynamicDirect = 'rule-set:shiki_personal_direct';
  const ips = baseline.filter(r => r.startsWith('IP-CIDR,')).map(r => r.split(',')[1]);
  const resolvers = nodeResolvers(oldDns['proxy-server-nameserver']);
  const dns = {
    enable: true, listen: '127.0.0.1:1053', ipv6: config.ipv6 === true,
    'cache-algorithm': 'arc', 'enhanced-mode': 'fake-ip', 'fake-ip-range': '198.18.0.1/16',
    'fake-ip-filter-mode': 'blacklist', 'prefer-h3': false, 'respect-rules': false,
    'use-hosts': true, 'use-system-hosts': false,
    'default-nameserver': ['223.5.5.5', '119.29.29.29'], nameserver: overseas,
    'nameserver-policy': policy, 'proxy-server-nameserver': resolvers.length ? resolvers : domestic,
    'direct-nameserver': domestic, 'direct-nameserver-follow-policy': true,
    'fake-ip-filter': uniq(local.concat(['+.arpa', 'time.*.com', 'ntp.*.com', '+.pool.ntp.org',
      '+.market.xiaomi.com', 'localhost.ptlogin2.qq.com', dynamicDirect], ncsi,
      ['whitelist', 'rule'].includes(oldDns['fake-ip-filter-mode']) ? [] : clean(oldDns['fake-ip-filter'])))
  };
  if (Object.keys(nodePolicy).length) dns['proxy-server-nameserver-policy'] = nodePolicy;
  if (dns.ipv6) dns['fake-ip-range6'] = oldDns['fake-ip-range6'] || '2001:2::/64';
  config['proxy-groups'] = kept;
  config['rule-providers'] = providers;
  config.rules = baseline.concat(sources.map(s => 'RULE-SET,shiki_' + s.id + ',' +
    (s.policy === 'DIRECT' ? 'DIRECT' : mainName))).concat(['GEOIP,CN,DIRECT', 'MATCH,' + mainName]);
  config.dns = dns;
  config['tcp-concurrent'] = true;
  config['find-process-mode'] = 'strict';
  config.profile = Object.assign({}, config.profile, {'store-selected': true, 'store-fake-ip': true});
  ['keep-alive-interval', 'keep-alive-idle', 'disable-keep-alive'].forEach(k => { delete config[k]; });
  config.sniffer = {enable: true, 'override-destination': false, 'force-dns-mapping': true, 'parse-pure-ip': true,
    sniff: {HTTP: {ports: [80, '8080-8880'], 'override-destination': false},
      TLS: {ports: [443, 8443], 'override-destination': false}, QUIC: {ports: [443, 8443], 'override-destination': false}},
    'skip-domain': uniq(clean(oldSniff['skip-domain']).concat(['Mijia Cloud', '+.push.apple.com', dynamicDirect], local, ncsi)),
    'skip-dst-address': uniq(list(oldSniff['skip-dst-address']).concat(ips))};
  if (oldSniff['skip-src-address']) config.sniffer['skip-src-address'] = oldSniff['skip-src-address'];
  const geo = 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/';
  config['geo-auto-update'] = true; config['geo-update-interval'] = 24;
  config['geodata-mode'] = false; config['geodata-loader'] = 'memconservative';
  config['geox-url'] = {mmdb: geo + 'geoip.metadb', geosite: geo + 'geosite.dat', geoip: geo + 'geoip.dat', asn: geo + 'GeoLite2-ASN.mmdb'};
  return config;
}
