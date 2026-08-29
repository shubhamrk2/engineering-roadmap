/* Validates every sheet against the authoring contract.
   Run:  node check.mjs                                                     */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
 
const root = dirname(fileURLToPath(import.meta.url));
const nav = readFileSync(join(root, 'assets/js/nav-data.js'), 'utf8');
const expected = [...nav.matchAll(/no:\s*'(\d\d)'.*?f:\s*'([\w.-]+)'/g)].map(m => ({ no: m[1], f: m[2] }));
 
let problems = 0;
const report = [];
 
function fail(file, msg) { problems++; report.push(`  FAIL  ${file}  ${msg}`); }
function warn(file, msg) { report.push(`  warn  ${file}  ${msg}`); }
 
const pages = readdirSync(root).filter(f => f.endsWith('.html'));
 
for (const { no, f } of expected) {
  if (!existsSync(join(root, f))) { fail(f, `missing (sheet ${no})`); continue; }
  const src = readFileSync(join(root, f), 'utf8');
  const lines = src.split('\n').length;
 
  // --- skeleton -----------------------------------------------------------
  if (!src.includes(`data-sheet="${no}"`)) fail(f, `body is missing data-sheet="${no}"`);
  for (const need of [
    'assets/css/sheet.css', 'assets/js/nav-data.js', 'assets/js/sheet.js',
    'class="rail"', 'class="toc"', 'class="sheetbody"', 'class="sheethead"', 'id="main"',
  ]) if (!src.includes(need)) fail(f, `skeleton missing: ${need}`);
 
  // --- duplicate element ids ---------------------------------------------
  const ids = [...src.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  const dupIds = ids.filter((v, i) => ids.indexOf(v) !== i);
  if (dupIds.length) fail(f, `duplicate id: ${[...new Set(dupIds)].join(', ')}`);
 
  // --- headings need ids --------------------------------------------------
  const h2 = [...src.matchAll(/<h2(\s[^>]*)?>/g)];
  const h2NoId = h2.filter(m => !/\sid=/.test(m[1] || ''));
  if (h2NoId.length) fail(f, `${h2NoId.length} <h2> without an id`);
  const h3 = [...src.matchAll(/<h3(\s[^>]*)?>/g)];
  const h3NoId = h3.filter(m => !/\sid=/.test(m[1] || ''));
  if (h3NoId.length) warn(f, `${h3NoId.length} <h3> without an id`);
 
  // --- svg accessibility + markers ---------------------------------------
  const svgs = [...src.matchAll(/<svg\b[^>]*>/g)].map(m => m[0]);
  svgs.forEach((s, i) => {
    if (!s.includes('viewBox')) fail(f, `svg #${i + 1} has no viewBox`);
    if (!s.includes('aria-label')) fail(f, `svg #${i + 1} has no aria-label`);
  });
  const markers = [...src.matchAll(/<marker\s+id="([^"]+)"/g)].map(m => m[1]);
  const dupMarkers = markers.filter((v, i) => markers.indexOf(v) !== i);
  if (dupMarkers.length) fail(f, `duplicate marker id: ${[...new Set(dupMarkers)].join(', ')}`);
  const used = new Set([...src.matchAll(/url\(#([^)]+)\)/g)].map(m => m[1]));
  for (const u of used) if (!markers.includes(u)) fail(f, `arrow references missing marker #${u}`);
 
  // --- unescaped angle brackets inside code blocks ------------------------
  const codes = [...src.matchAll(/<pre><code>([\s\S]*?)<\/code><\/pre>/g)];
  codes.forEach((c, i) => {
    const bad = c[1].match(/<(?!\/?(span|br)\b)/g);
    if (bad) fail(f, `code block #${i + 1} has ${bad.length} unescaped "<" (use &lt;)`);
  });
  if (!codes.length && no !== '00') fail(f, 'no code blocks at all');
 
  // --- code blocks need a language ---------------------------------------
  const noLang = (src.match(/<div class="code">/g) || []).length;
  if (noLang) warn(f, `${noLang} code blocks without data-lang`);
 
  // --- internal links resolve --------------------------------------------
  for (const m of src.matchAll(/href="([\w-]+\.html)(#[^"]*)?"/g)) {
    if (!existsSync(join(root, m[1]))) fail(f, `dead link to ${m[1]}`);
  }
 
  // --- required sections --------------------------------------------------
  if (no !== '00') {
    if (!/id="connect"/.test(src)) warn(f, 'no "How the subtopics connect" section');
    if (!/id="drill"/.test(src) && no !== '14') warn(f, 'no drill book');
  }
  if (!/class="signoff"/.test(src)) fail(f, 'no sign-off block');
 
  // --- tag balance (rough) -----------------------------------------------
  for (const tag of ['div', 'figure', 'table', 'svg', 'details', 'section']) {
    const open = (src.match(new RegExp(`<${tag}[\\s>]`, 'g')) || []).length;
    const close = (src.match(new RegExp(`</${tag}>`, 'g')) || []).length;
    if (open !== close) fail(f, `<${tag}> unbalanced: ${open} open, ${close} close`);
  }
 
  // --- house style --------------------------------------------------------
  if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(src)) fail(f, 'contains emoji');
 
  const dwgs = (src.match(/class="dwg/g) || []).length;
  const drills = (src.match(/<details>/g) || []).length;
  const boxes = (src.match(/type="checkbox"/g) || []).length;
  const res = (src.match(/class="res"/g) || []).length;
  if (dwgs < 3 && no !== '00') warn(f, `only ${dwgs} diagrams`);
  report.push(`  ok    ${f.padEnd(20)} ${String(lines).padStart(5)} lines · ${String(dwgs).padStart(2)} drawings · ${String(h2.length).padStart(2)} sections · ${String(drills).padStart(2)} drills · ${String(boxes).padStart(2)} sign-offs · ${res} resource lists`);
}
 
const known = new Set(expected.map(e => e.f));
const orphans = pages.filter(p => !known.has(p));
if (orphans.length) warn('-', `html files not in the sheet index: ${orphans.join(', ')}`);
 
console.log(report.join('\n'));
console.log(problems ? `\n${problems} problem(s) found.` : '\nAll sheets pass.');
process.exit(problems ? 1 : 0);