'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const guard = JSON.parse(fs.readFileSync(path.join(root, 'config/bootstrap.json'), 'utf8'));
const conf = JSON.parse(fs.readFileSync(path.join(root, 'config/sources.yaml'), 'utf8'));
const descriptors = [{id: 'personal_direct', policy: 'DIRECT'}, {id: 'personal_proxy', policy: 'PROXY'}]
  .concat(conf.sources.map(s => ({id: s.id, policy: s.policy})));
const source = fs.readFileSync(path.join(root, 'config/override.js'), 'utf8')
  .replace('__PROVIDERS_JSON__', JSON.stringify(descriptors))
  .replace('__BASELINE_JSON__', JSON.stringify(guard.rules.slice(0, -1)));
function apply(input, name, script = source) {
  const protectedInput = {...structuredClone(input), ...structuredClone(guard)};
  const ctx = {config: structuredClone(protectedInput), profileName: name};
  vm.createContext(ctx);
  try {
    vm.runInContext(script + ';result=main(config,profileName);', ctx, {timeout: 2000});
    return {config: JSON.parse(JSON.stringify(ctx.result)), failed: false};
  } catch (_) {
    // Same fallback contract as Verge 2.5.8: native guard survives JS errors.
    return {config: protectedInput, failed: true};
  }
}
function fixture(name) {
  return {mode: 'rule', ipv6: false, 'mixed-port': 7897, tun: {enable: false},
    proxies: [{name: 'Fixture A', type: 'ss', server: 'entry.example', port: 9, cipher: 'aes-128-gcm', password: 'test-fixture-only', udp: true}],
    hosts: {'entry.example': '192.0.2.8'},
    'proxy-groups': [{name, type: 'select', proxies: ['Auto', 'Fixture A']},
      {name: 'Auto', type: 'url-test', proxies: ['Fixture A']},
      {name: 'Microsoft', type: 'select', proxies: ['DIRECT', name]},
      {name: 'PROXY', type: 'select', proxies: [name]}],
    'rule-providers': {Vendor: {type: 'http', behavior: 'classical', url: 'https://example.invalid/rules'}},
    rules: ['RULE-SET,Vendor,Microsoft', 'MATCH,' + name],
    dns: {'proxy-server-nameserver': ['https://doh.pub/dns-query'],
      'nameserver-policy': {'entry.example': '223.5.5.5', '+.checkout.mzxnyysm.com': '223.5.5.5'},
      'fake-ip-filter': ['+.provider.example', '+.checkout.mzxnyysm.com']}};
}
let count = 0;
function test(name, fn) { fn(); count++; }
for (const name of ['GeekSpeed极客加速器', '雪橇云']) {
  test(name + ' replacement and preservation', () => {
    const old = fixture(name), result = apply(old, name); assert.equal(result.failed, false);
    const c = result.config;
    assert.deepEqual(c.proxies, old.proxies); assert.deepEqual(c.hosts, old.hosts);
    assert.deepEqual(c.tun, old.tun); assert.equal(c['mixed-port'], old['mixed-port']);
    assert.deepEqual(c['proxy-groups'].map(g => g.name), [name, 'Auto']);
    assert.equal(c.rules.at(-1), 'MATCH,' + name);
    assert.equal(JSON.stringify(c).includes('Vendor'), false);
    assert.equal(JSON.stringify(c).includes('checkout.mzxnyysm.com'), false);
    assert.equal(JSON.stringify(c).includes('#PROXY'), false);
    assert.equal(c.dns.nameserver.every(s => s.endsWith('#' + name)), true);
    assert.equal(Object.values(c['rule-providers']).every(p => p.proxy === name), true);
    assert.equal(c.dns['nameserver-policy']['rule-set:personal_clash_personal_direct'][0].endsWith('#DIRECT'), true);
    assert.equal(c.dns['fake-ip-filter'].includes('rule-set:personal_clash_personal_direct'), true);
    assert.deepEqual(c.dns['proxy-server-nameserver-policy']['entry.example'], ['223.5.5.5#DIRECT']);
    assert.deepEqual(apply(c, name).config, c);
  });
  test(name + ' node refresh', () => {
    const a = fixture(name); a.proxies[0].server = '192.0.2.99';
    assert.equal(apply(a, name).config.proxies[0].server, '192.0.2.99');
  });
  test(name + ' main checks change only the four approved fields', () => {
    const input = fixture(name);
    const main = input['proxy-groups'][0];
    main.proxies.push('Backup');
    if (name === '雪橇云') {
      Object.assign(main, {url: 'http://www.gstatic.com/generate_204', interval: 600, lazy: true});
      main.proxies.push('DIRECT');
    }
    main['default-selected'] = 'Fixture A';
    input['proxy-groups'].push({name: 'Backup', type: 'fallback', proxies: ['Fixture A']});
    const result = apply(input, name);
    assert.equal(result.failed, false);
    assert.deepEqual(result.config['proxy-groups'][0], {...main,
      url: 'https://www.gstatic.com/generate_204', 'expected-status': 204, timeout: 5000, interval: 0});
    for (const g of result.config['proxy-groups'].slice(1)) {
      assert.equal(g.interval, 300); assert.equal(g.timeout, 5000);
      assert.equal(g.url, 'https://www.gstatic.com/generate_204');
      assert.equal(g['expected-status'], 204); assert.equal(g.lazy, true);
      if (g.type === 'url-test') assert.equal(g.tolerance, 100);
    }
    assert.deepEqual(apply(result.config, name).config, result.config);
  });
}
test('unknown main fails under guard', () => {
  const r = apply(fixture('Provider'), 'Missing'); assert.equal(r.failed, true);
  assert.deepEqual(r.config.rules, guard.rules);
});
test('syntax failure retains native guard', () => {
  const r = apply(fixture('Provider'), 'Provider', 'function main( {');
  assert.equal(r.failed, true); assert.deepEqual(r.config.rules, guard.rules);
});
test('runtime failure retains native guard', () => {
  const r = apply(fixture('Provider'), 'Provider', 'function main(){throw new Error("fault")}');
  assert.equal(r.failed, true); assert.equal(r.config.rules.at(-1), 'MATCH,REJECT');
});
test('unknown group cannot silently disappear', () => {
  const c = fixture('Provider'); c['proxy-groups'][0].proxies.push('Missing'); assert.equal(apply(c, 'Provider').failed, true);
});
test('cycle stops', () => {
  const c = fixture('Provider'); c['proxy-groups'][1].proxies.push('Provider'); assert.equal(apply(c, 'Provider').failed, true);
});
test('node providers and dependent groups survive', () => {
  const c = fixture('Provider'); c['proxy-providers'] = {nodes: {type: 'file', path: './nodes.yaml'}};
  c['proxy-groups'][0].use = ['nodes']; assert.deepEqual(apply(c, 'Provider').config['proxy-providers'], c['proxy-providers']);
});
test('missing node provider stops', () => {
  const c = fixture('Provider'); c['proxy-groups'][0].use = ['missing']; assert.equal(apply(c, 'Provider').failed, true);
});
test('IPv6 follows app-owned flag', () => {
  const c = fixture('Provider'); c.ipv6 = true; const d = apply(c, 'Provider').config.dns;
  assert.equal(d.ipv6, true); assert.equal(d['fake-ip-range6'], '2001:2::/64');
});
test('no direct fallback injected into selector', () => {
  const c = apply(fixture('Provider'), 'Provider').config;
  assert.equal(c['proxy-groups'][0].proxies.includes('DIRECT'), false);
});
test('provider main DIRECT choice is preserved', () => {
  const c = fixture('Provider'); c['proxy-groups'][0].proxies.push('DIRECT');
  assert.equal(apply(c, 'Provider').config['proxy-groups'][0].proxies.includes('DIRECT'), true);
});
test('DNS policy order follows business rule sources', () => {
  const c = apply(fixture('Provider'), 'Provider').config;
  const a = Object.keys(c.dns['nameserver-policy']);
  assert.ok(a.indexOf('rule-set:personal_clash_copilot') < a.indexOf('rule-set:personal_clash_microsoft'));
  assert.ok(a.indexOf('rule-set:personal_clash_steam_cn') < a.indexOf('rule-set:personal_clash_steam'));
});
test('voice stays in routing while only its DNS selector disappears', () => {
  const c = apply(fixture('Provider'), 'Provider').config;
  assert.deepEqual(Object.keys(c['rule-providers']), descriptors.map(s => 'personal_clash_' + s.id));
  assert.deepEqual(c.rules.slice(guard.rules.length - 1, -2), descriptors.map(s =>
    'RULE-SET,personal_clash_' + s.id + ',' + (s.policy === 'DIRECT' ? 'DIRECT' : 'Provider')));
  const keys = Object.keys(c.dns['nameserver-policy']);
  assert.deepEqual(keys.filter(k => k.startsWith('rule-set:')),
    descriptors.filter(s => s.id !== 'voice').map(s => 'rule-set:personal_clash_' + s.id));
  const voice = c['rule-providers'].personal_clash_voice;
  assert.equal(voice.url, 'https://raw.githubusercontent.com/SHIKI1255/clash-config/release/rules/voice.list');
  assert.equal(voice.path, './ruleset/personal-clash/voice.list');
  assert.equal(voice.interval, 86400); assert.equal(voice.proxy, 'Provider');
});
console.log(JSON.stringify({adapter_tests: count, status: 'passed'}));
