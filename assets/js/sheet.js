/* ============================================================================
   Page runtime for the drawing set.
   Builds the sheet index, the contents rail, the title block, syntax
   highlighting and the sign-off tracker. No dependencies, no build step.
   ==========================================================================*/
(function () {
  'use strict';
 
  var SHEETS = window.SHEETS || [];
  var body = document.body;
  var NO = body.getAttribute('data-sheet') || '00';
  var me = SHEETS.filter(function (s) { return s.no === NO; })[0] || SHEETS[0];
  var STORE = 'bd:';
 
  /* Sub-pages (the DSA topic and problem views) share a sheet number so the
     rail highlights correctly, but they render their own contents and
     prev/next, and must never write the sheet's sign-off count. */
  var SUB = body.hasAttribute('data-subpage');
 
  /* ---------------------------------------------------------------- store */
  function get(k) { try { return localStorage.getItem(STORE + k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(STORE + k, v); } catch (e) {} }
 
  /* ----------------------------------------------------------- sheet index */
  function buildRail() {
    var rail = document.querySelector('.rail');
    if (!rail) return;
    var h = '';
    h += '<div class="brand"><b>Badge<i>Desk</i></b><span>Engineering drawing set &middot; rev 1</span></div>';
    h += '<div class="searchbox"><input id="q" type="search" placeholder="Search sheets  (press /)" autocomplete="off" aria-label="Search sheets"></div>';
    var g = null;
    SHEETS.forEach(function (s) {
      if (s.g !== g) { g = s.g; h += '<h6>' + g + '</h6>'; }
      h += '<a href="' + s.f + '" data-kw="' + (s.t + ' ' + s.kw).toLowerCase() + '"' +
           (s.no === NO ? ' class="on"' : '') + '><em>' + s.no + '</em><span>' + s.t + '</span></a>';
    });
    rail.innerHTML = h;
 
    var q = document.getElementById('q');
    q.addEventListener('input', function () {
      var v = q.value.trim().toLowerCase();
      rail.querySelectorAll('a[data-kw]').forEach(function (a) {
        a.classList.toggle('hide', !!v && a.getAttribute('data-kw').indexOf(v) < 0);
      });
      rail.querySelectorAll('h6').forEach(function (hd) {
        var n = 0, el = hd.nextElementSibling;
        while (el && el.tagName === 'A') { if (!el.classList.contains('hide')) n++; el = el.nextElementSibling; }
        hd.style.display = n ? '' : 'none';
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT') { e.preventDefault(); q.focus(); }
      if (e.key === 'Escape' && document.activeElement === q) { q.value = ''; q.dispatchEvent(new Event('input')); q.blur(); }
      if ((e.key === '[' || e.key === ']') && document.activeElement.tagName !== 'INPUT') {
        var i = SHEETS.indexOf(me), n = e.key === '[' ? i - 1 : i + 1;
        if (SHEETS[n]) location.href = SHEETS[n].f;
      }
    });
  }
 
  /* ------------------------------------------------------------ zone ruler */
  function buildZoneRuler() {
    var main = document.querySelector('main');
    if (!main) return;
    var z = document.createElement('div');
    z.className = 'zoner';
    z.setAttribute('aria-hidden', 'true');
    var s = '';
    for (var i = 1; i <= 12; i++) s += '<span>' + i + '</span>';
    z.innerHTML = s;
    main.insertBefore(z, main.firstChild);
  }
 
  /* ------------------------------------------------------- contents + spy */
  function buildToc() {
    var toc = document.querySelector('.toc');
    if (!toc) return;
    var hs = document.querySelectorAll('main h2[id], main h3[id]');
    if (!hs.length) { toc.style.display = 'none'; return; }
    var h = '<h6>On this sheet</h6>';
    hs.forEach(function (el) {
      var txt = el.getAttribute('data-toc') || el.textContent.trim();
      h += '<a href="#' + el.id + '" class="' + (el.tagName === 'H3' ? 'lvl3' : '') + '">' + txt + '</a>';
    });
    toc.innerHTML = h;
 
    var links = {};
    toc.querySelectorAll('a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var current = null;
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        if (current) current.classList.remove('on');
        current = links[en.target.id];
        if (current) { current.classList.add('on'); }
      });
    }, { rootMargin: '-80px 0px -72% 0px', threshold: 0 });
    hs.forEach(function (el) { obs.observe(el); });
  }
 
  /* ---------------------------------------------------------- title block */
  function buildTitleBlock() {
    var tb = document.createElement('aside');
    tb.className = 'titleblock';
    tb.innerHTML =
      '<div><span>Sheet</span><span>' + me.no + ' / ' + SHEETS[SHEETS.length - 1].no + '</span></div>' +
      '<div><span>Title</span><span>' + me.t + '</span></div>' +
      '<div><span>Week</span><span>' + me.w + '</span></div>' +
      '<div><span>Signed off</span><span id="tbp">0 / 0</span></div>' +
      '<div class="tb-bar"><i id="tbb"></i></div>';
    document.body.appendChild(tb);
  }
 
  /* ------------------------------------------------------------- sign-off */
  function buildSignoff() {
    var boxes = document.querySelectorAll('.signoff input[type=checkbox]');
    boxes.forEach(function (b, i) {
      var k = 'c:' + NO + ':' + i;
      b.checked = get(k) === '1';
      b.addEventListener('change', function () { set(k, b.checked ? '1' : '0'); paint(); });
    });
    // A sub-page has no sign-off block; writing 0 here would erase the
    // parent sheet's box count from the roadmap-wide total.
    if (!SUB) set('n:' + NO, String(boxes.length));
    paint();
 
    function paint() {
      var done = 0, total = 0;
      SHEETS.forEach(function (s) {
        var n = parseInt(get('n:' + s.no) || '0', 10);
        total += n;
        for (var i = 0; i < n; i++) if (get('c:' + s.no + ':' + i) === '1') done++;
      });
      var p = document.getElementById('tbp'), bar = document.getElementById('tbb');
      if (p) p.textContent = done + ' / ' + total;
      if (bar) bar.style.width = (total ? (done / total) * 100 : 0) + '%';
      document.querySelectorAll('[data-progress-sheet]').forEach(function (el) {
        var no = el.getAttribute('data-progress-sheet');
        var n = parseInt(get('n:' + no) || '0', 10), d = 0;
        for (var i = 0; i < n; i++) if (get('c:' + no + ':' + i) === '1') d++;
        el.textContent = n ? d + '/' + n : '—';
        el.style.color = n && d === n ? 'var(--moss)' : '';
      });
    }
  }
 
  /* ------------------------------------------------------------- prev/next */
  function buildNext() {
    var main = document.querySelector('.sheetbody') || document.querySelector('main');
    if (!main || document.querySelector('.next')) return;
    var i = SHEETS.indexOf(me), p = SHEETS[i - 1], n = SHEETS[i + 1];
    if (!p && !n) return;
    var d = document.createElement('nav');
    d.className = 'next';
    d.innerHTML =
      (p ? '<a href="' + p.f + '"><em>&larr; Sheet ' + p.no + '</em><b>' + p.t + '</b></a>' : '<span style="flex:1"></span>') +
      (n ? '<a class="rt" href="' + n.f + '"><em>Sheet ' + n.no + ' &rarr;</em><b>' + n.t + '</b></a>' : '<span style="flex:1"></span>');
    main.appendChild(d);
  }
 
  /* ------------------------------------------------------------ copy code */
  function buildCopy() {
    document.querySelectorAll('.code').forEach(function (c) {
      var hd = c.querySelector('header');
      if (!hd) {
        hd = document.createElement('header');
        hd.innerHTML = '<b>' + (c.getAttribute('data-lang') || 'code') + '</b>';
        c.insertBefore(hd, c.firstChild);
      }
      if (hd.querySelector('.cp')) return;
      var b = document.createElement('button');
      b.className = 'cp'; b.type = 'button'; b.textContent = 'Copy';
      b.addEventListener('click', function () {
        var t = c.querySelector('code').textContent;
        var ok = function () {
          b.textContent = 'Copied';
          setTimeout(function () { b.textContent = 'Copy'; }, 1400);
        };
        // navigator.clipboard is unavailable on file://, which is how this set
        // is meant to open, so fall back to the old selection trick.
        if (navigator.clipboard && location.protocol !== 'file:') {
          navigator.clipboard.writeText(t).then(ok, function () { legacyCopy(t, ok, b); });
        } else legacyCopy(t, ok, b);
      });
      hd.appendChild(b);
    });
  }
 
  function legacyCopy(text, ok, btn) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); ok(); }
    catch (e) { btn.textContent = 'Select + copy'; }
    document.body.removeChild(ta);
  }
 
  /* ----------------------------------------------------------- highlighter */
  var KW = ('auto define include inline namespace nullptr operator override short signed sizeof template typename unsigned virtual ' +
    'abstract and as assert async await begin bool boolean break by case catch char class commit const constructor ' +
    'continue create data declare def default defer del delete distinct do double drop elif else end enum except export ' +
    'extends false final finally float fn for foreign from func function global go group having if impl implements import ' +
    'in index inner insert instanceof int integer interface into is join key lambda left let limit long match mod module ' +
    'mut new nil none nonlocal not null nullable of offset on or order outer package pass primary print private protected ' +
    'public raise readonly record references return right select self set static string struct super switch synchronized ' +
    'table this throw throws true try type typeof union unique update use using values var varchar void volatile when ' +
    'where while with yield undefined require module.exports FROM RUN COPY WORKDIR EXPOSE CMD ENTRYPOINT ENV ARG LABEL USER VOLUME HEALTHCHECK'
  ).split(/\s+/);
  var KWSET = {}; KW.forEach(function (k) { KWSET[k.toLowerCase()] = 1; });
 
  var HASHLANG = { python: 1, py: 1, bash: 1, shell: 1, sh: 1, yaml: 1, yml: 1, dockerfile: 1, hcl: 1, terraform: 1, toml: 1, ini: 1, powershell: 1, ps1: 1, graphql: 1, r: 1, make: 1 };
  var SLASHLANG = { javascript: 1, js: 1, typescript: 1, ts: 1, tsx: 1, jsx: 1, java: 1, c: 1, cpp: 1, go: 1, rust: 1, css: 1, scss: 1, json5: 1, hcl: 1, terraform: 1, prisma: 1, proto: 1 };
 
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
 
  function highlight(src, lang) {
    lang = (lang || '').toLowerCase();
    var alts = [];
    if (lang === 'sql') alts.push('--[^\\n]*');
    else if (lang === 'html' || lang === 'xml' || lang === 'vue') alts.push('<!--[\\s\\S]*?-->');
    else {
      if (HASHLANG[lang]) alts.push('#[^\\n]*');
      if (SLASHLANG[lang]) alts.push('//[^\\n]*', '/\\*[\\s\\S]*?\\*/');
    }
    var parts = [];
    if (alts.length) parts.push('(?<com>' + alts.join('|') + ')');
    parts.push('(?<str>"""[\\s\\S]*?"""|\'\'\'[\\s\\S]*?\'\'\'|`(?:\\\\.|[^`\\\\])*`|"(?:\\\\.|[^"\\\\\\n])*"|\'(?:\\\\.|[^\'\\\\\\n])*\')');
    if (lang === 'html' || lang === 'xml') parts.push('(?<tag></?[A-Za-z][\\w:-]*)');
    parts.push('(?<num>\\b\\d[\\d_]*(?:\\.\\d+)?(?:[eE][+-]?\\d+)?\\b)');
    parts.push('(?<dec>@[A-Za-z_][\\w.]*)');
    parts.push('(?<word>[A-Za-z_$][\\w$]*)');
 
    var re, out = '', last = 0, m;
    try { re = new RegExp(parts.join('|'), 'g'); }
    catch (e) { return esc(src); }
 
    while ((m = re.exec(src)) !== null) {
      var g = m.groups || {};
      out += esc(src.slice(last, m.index));
      last = m.index + m[0].length;
      var tok = m[0];
      if (g.com) out += '<span class="c-com">' + esc(tok) + '</span>';
      else if (g.str) out += '<span class="c-str">' + esc(tok) + '</span>';
      else if (g.tag) out += '<span class="c-key">' + esc(tok) + '</span>';
      else if (g.num) out += '<span class="c-num">' + esc(tok) + '</span>';
      else if (g.dec) out += '<span class="c-typ">' + esc(tok) + '</span>';
      else if (g.word) {
        var nx = src.charAt(last);
        var lw = tok.toLowerCase();
        if (KWSET[lw] && (lang !== 'sql' ? tok === lw || tok === tok.toUpperCase() : true)) {
          out += '<span class="c-key">' + esc(tok) + '</span>';
        } else if (nx === '(') {
          out += '<span class="c-fn">' + esc(tok) + '</span>';
        } else if (/^[A-Z][a-z]/.test(tok)) {
          out += '<span class="c-typ">' + esc(tok) + '</span>';
        } else out += esc(tok);
      } else out += esc(tok);
    }
    out += esc(src.slice(last));
    return out;
  }
 
  function paintCode() {
    document.querySelectorAll('.code').forEach(function (c) {
      var el = c.querySelector('code');
      if (!el || el.hasAttribute('data-hl')) return;
      var lang = c.getAttribute('data-lang') || '';
      if (lang === 'text' || lang === 'none') { el.setAttribute('data-hl', '1'); return; }
      el.innerHTML = highlight(el.textContent.replace(/^\n/, '').replace(/\s+$/, ''), lang);
      el.setAttribute('data-hl', '1');
    });
  }
 
  /* --------------------------------------------------------------- number */
  function numberSections() {
    document.querySelectorAll('main h2[id]').forEach(function (h, i) {
      if (!h.hasAttribute('data-n')) {
        h.setAttribute('data-n', NO + '.' + String(i + 1).padStart(2, '0'));
      }
    });
  }
 
  /* ------------------------------------------------------------------ go */
  function init() {
    buildRail();
    buildZoneRuler();
    buildTitleBlock();
    buildSignoff();
    if (SUB) return;              // dsa.js owns the contents, code and prev/next
    numberSections();
    buildToc();
    buildCopy();
    paintCode();
    buildNext();
    document.title = 'Sheet ' + me.no + ' — ' + me.t + ' — BadgeDesk Roadmap';
  }
 
  /* Shared with dsa.js so the DSA pages use the same highlighter, copy button
     and progress store rather than a second copy of all three. */
  window.SheetRuntime = {
    esc: esc,
    highlight: highlight,
    paintCode: paintCode,
    buildCopy: buildCopy,
    get: get,
    set: set,
    sheet: me
  };
 
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();