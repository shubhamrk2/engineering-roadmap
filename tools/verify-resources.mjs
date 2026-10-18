/* Verifies resource links for the Applied AI track.

   Usage:   node tools/verify-resources.mjs <file.json> [--quiet]

   Input JSON:
     { "days": { "29": { "text": [{"t":"Title","u":"https://..."}], "video": [{"t":"Title","u":"https://www.youtube.com/watch?v=ID"}] } } }
   or any object with arrays under "text" / "video" at the top level, or a bare array of {t,u}.

   What it checks
     text   the page loads (2xx after redirects) and is HTML; prints the page <title> so you can judge relevance
     video  the id exists, via YouTube oEmbed; prints the REAL title and channel so you can judge relevance

   A passing link only proves it exists. Whether it teaches the right thing is a human judgement:
   read the printed titles. Exit code 1 if anything fails to load.                                     */
import { readFileSync } from 'node:fs';

const file = process.argv[2];
const quiet = process.argv.includes('--quiet');
if (!file) { console.error('usage: node tools/verify-resources.mjs <file.json> [--quiet]'); process.exit(2); }

const data = JSON.parse(readFileSync(file, 'utf8'));
const items = [];
function add(kind, arr, where) { (arr || []).forEach(r => items.push({ kind, where, t: r.t, u: r.u })); }
if (Array.isArray(data)) add('auto', data, 'list');
else if (data.days) for (const [d, v] of Object.entries(data.days)) { add('text', v.text, 'day ' + d); add('video', v.video, 'day ' + d); }
else { add('text', data.text, 'top'); add('video', data.video, 'top'); }

const ytId = u => { try { const x = new URL(u); if (x.hostname === 'youtu.be') return x.pathname.slice(1); return x.searchParams.get('v'); } catch { return null; } };
const isYT = u => /(^|\.)youtube\.com|youtu\.be/.test(new URL(u).hostname);

async function get(u, ms = 20000) {
  const c = new AbortController(); const id = setTimeout(() => c.abort(), ms);
  try { return await fetch(u, { redirect: 'follow', signal: c.signal, headers: { 'user-agent': 'Mozilla/5.0 (resource-verifier)', 'accept-language': 'en' } }); }
  finally { clearTimeout(id); }
}

async function check(it) {
  const out = { ...it, ok: false, note: '' };
  try {
    const youtube = isYT(it.u);
    if (it.kind === 'video' || (it.kind === 'auto' && youtube)) {
      const id = ytId(it.u);
      if (!id) { out.note = 'not a watch?v= or youtu.be link (channel/playlist/search links are not accepted as a video)'; return out; }
      const r = await get('https://www.youtube.com/oembed?format=json&url=' + encodeURIComponent('https://www.youtube.com/watch?v=' + id));
      if (r.status !== 200) { out.note = 'oEmbed HTTP ' + r.status + ' (video missing, private, or embedding disabled)'; return out; }
      const j = await r.json(); out.ok = true; out.note = `"${j.title}" by ${j.author_name}`; return out;
    }
    const r = await get(it.u);
    if (r.status < 200 || r.status >= 300) { out.note = 'HTTP ' + r.status; return out; }
    const ct = r.headers.get('content-type') || '';
    const body = ct.includes('html') ? (await r.text()).slice(0, 60000) : '';
    const m = body.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    out.ok = true; out.note = (m ? m[1].replace(/\s+/g, ' ').trim() : ct) + (r.url !== it.u ? '  -> ' + r.url : '');
  } catch (e) { out.note = 'error: ' + (e.name === 'AbortError' ? 'timeout' : e.message); }
  return out;
}

const results = []; let i = 0;
async function worker() { while (i < items.length) { const it = items[i++]; results.push(await check(it)); } }
await Promise.all(Array.from({ length: 6 }, worker));

results.sort((a, b) => (a.where + a.u).localeCompare(b.where + b.u, undefined, { numeric: true }));
let bad = 0;
for (const r of results) {
  if (!r.ok) bad++;
  if (!r.ok || !quiet) console.log(`${r.ok ? 'ok  ' : 'FAIL'}  ${r.where.padEnd(8)} ${r.u}\n        declared: ${r.t}\n        actual:   ${r.note}`);
}
console.log(`\n${results.length - bad}/${results.length} links verified${bad ? `, ${bad} FAILED` : ''}.`);
process.exit(bad ? 1 : 0);
