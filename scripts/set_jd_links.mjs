#!/usr/bin/env node
/**
 * 京东联盟链接批量替换工具
 *
 * 现状：站内绝大多数京东链接形如
 *   https://union-click.jd.com/jdc?keyword=<关键词>&enc=utf-8
 * 这种链接不含你的推广位 ID（PID），京东后台无法跟单计佣。
 *
 * 用法：
 *   1) 列出需要生成的链接清单：
 *        node scripts/set_jd_links.mjs
 *   2) 到 union.jd.com 后台按清单生成推广链接，
 *      把结果填进 config/jd-links.json（格式见该文件 _example）
 *   3) 应用到全站：
 *        node scripts/set_jd_links.mjs --apply
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MAP_FILE = path.join(ROOT, 'config', 'jd-links.json');
const APPLY = process.argv.includes('--apply');

const SKIP_DIRS = new Set(['.git', '__pycache__', 'node_modules', 'reports', 'scripts']);

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(e.name)) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (p.endsWith('.html')) out.push(p);
  }
  return out;
}

/** 提取 href 中 union-click 链接的 keyword 参数（已 URL 解码） */
function keywordsIn(html) {
  const found = new Map(); // decoded keyword -> count
  for (const m of html.matchAll(/href="https:\/\/union-click\.jd\.com\/jdc\?([^"]*)"/g)) {
    const params = new URLSearchParams(m[1].replace(/&amp;/g, '&'));
    const kw = params.get('keyword');
    if (!kw) continue;
    const hasPid = /[?&]p=/.test(m[1]);
    found.set(kw, (found.get(kw) || 0) + (hasPid ? -1 : 1));
  }
  return found;
}

const files = walk(ROOT);
const totals = new Map();

for (const f of files) {
  for (const [kw, n] of keywordsIn(fs.readFileSync(f, 'utf8'))) {
    totals.set(kw, (totals.get(kw) || 0) + n);
  }
}

const missing = [...totals.entries()].filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]);

if (!APPLY) {
  console.log('需要在京东联盟后台生成推广链接的商品关键词：\n');
  let total = 0;
  for (const [kw, n] of missing) {
    console.log(`  ${String(n).padStart(3)} 处   ${kw}`);
    total += n;
  }
  console.log(`\n合计 ${missing.length} 个关键词 / ${total} 处链接，目前全部不含 PID。`);
  console.log(`\n下一步：把生成的链接填入 config/jd-links.json，然后运行：`);
  console.log(`  node scripts/set_jd_links.mjs --apply`);
  process.exit(0);
}

if (!fs.existsSync(MAP_FILE)) {
  console.error(`缺少 ${path.relative(ROOT, MAP_FILE)}，请先创建。`);
  console.error('格式：{ "_example": "见下", "智能体脂秤": "https://u.jd.com/xxxxxx" }');
  process.exit(1);
}

const map = JSON.parse(fs.readFileSync(MAP_FILE, 'utf8'));
const rules = Object.entries(map).filter(([k, v]) => !k.startsWith('_') && /^https?:\/\//.test(v));

if (!rules.length) {
  console.error('config/jd-links.json 里没有任何有效链接（值需以 http 开头）。');
  process.exit(1);
}

let changedFiles = 0;
const perRule = new Map(rules.map(([k]) => [k, 0]));
const unmatched = new Set();

for (const f of files) {
  let src = fs.readFileSync(f, 'utf8');
  const before = src;

  for (const [kw, url] of rules) {
    const enc = encodeURIComponent(kw);
    // 同时匹配已编码与未编码两种写法
    for (const needle of [`keyword=${enc}`, `keyword=${kw}`]) {
      const re = new RegExp(
        `https://union-click\\.jd\\.com/jdc\\?keyword=${needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}&(?:amp;)?enc=utf-8`,
        'g'
      );
      const hits = src.match(re);
      if (hits) {
        src = src.replace(re, url);
        perRule.set(kw, perRule.get(kw) + hits.length);
      }
    }
  }

  // 记录仍然残留的、未配置映射的旧链接
  for (const m of src.matchAll(/href="https:\/\/union-click\.jd\.com\/jdc\?([^"]*)"/g)) {
    const kw = new URLSearchParams(m[1].replace(/&amp;/g, '&')).get('keyword');
    if (kw && !/[?&]p=/.test(m[1])) unmatched.add(kw);
  }

  if (src !== before) {
    fs.writeFileSync(f, src, 'utf8');
    changedFiles++;
  }
}

console.log(`已更新 ${changedFiles} 个文件：`);
for (const [kw, n] of perRule) console.log(`  ${String(n).padStart(3)} 处   ${kw}`);
if (unmatched.size) {
  console.log(`\n仍无 PID 的关键词（本次未配置映射）：`);
  for (const kw of unmatched) console.log(`  - ${kw}`);
}
