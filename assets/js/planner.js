/* ============================================================================
   Daily planner renderer. Reads window.WEEKS / window.RES / PLAN_START / PLAN_END
   from daily-plan.js and draws one card per day. Must load BEFORE sheet.js so the
   week headings exist when sheet.js builds the contents rail.
   State lives in localStorage under the same 'bd:' prefix sheet.js uses:
     bd:pl:d:<n>  '1' when day n is done        bd:pl:n:<n>  free-text note
   ==========================================================================*/
(function () {
  'use strict';
  var root = document.getElementById('planner');
  if (!root || !window.WEEKS) return;

  var P = 'bd:pl:';
  function get(k) { try { return localStorage.getItem(P + k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(P + k, v); } catch (e) {} }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  var DAY = 864e5;
  function ymd(s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  var START = ymd(window.PLAN_START), END = ymd(window.PLAN_END);
  var now = new Date(), TODAY = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function fmt(d) { return DOW[d.getDay()] + ' ' + d.getDate() + ' ' + MON[d.getMonth()] + (d.getFullYear() !== 2026 ? ' ' + d.getFullYear() : ''); }
  function dayIndex(d) { return Math.round((d - START) / DAY); }

  var HRS = {
    1: [['Learn', 2], ['Practice', 2.5], ['Review', 0.5]],
    2: [['Learn', 1.5], ['Build', 2.25], ['DSA', 0.75], ['Review', 0.5]],
    3: [['Learn', 1.5], ['Build', 2.25], ['DSA', 0.75], ['Review', 0.5]],
    4: [['Learn', 1.5], ['Build', 2.25], ['DSA', 0.75], ['Review', 0.5]],
    5: [['Practice / mocks', 2.5], ['DSA', 0.75], ['Applications + review', 1.75]],
    sat: [['Checkpoint', 2], ['Catch-up', 2], ['Job log', 1]]
  };

  /* ---- flatten to a day list so every card knows its absolute day number ---- */
  var days = [];
  window.WEEKS.forEach(function (w, wi) {
    w.days.forEach(function (d, di) {
      var date = new Date(START.getTime() + days.length * DAY);
      days.push({ n: days.length + 1, w: wi, di: di, date: date, d: d, ph: w.ph });
    });
  });
  var TOTAL = days.length;

  /* ---- stats --------------------------------------------------------------- */
  function doneCount(upTo) {
    var c = 0;
    days.forEach(function (x) { if (get('d:' + x.n) === '1' && (upTo == null || x.n <= upTo)) c++; });
    return c;
  }
  function stats() {
    var idx = dayIndex(TODAY);                    // 0-based; <0 before start
    var done = doneCount();
    var cards = '';
    function card(k, v, s, cls) {
      return '<div class="stat ' + (cls || '') + '"><div class="sk">' + k + '</div><div class="sv">' + v + '</div><div class="ss">' + s + '</div></div>';
    }
    var dayLabel, sub, status, scls;
    if (idx < 0) {
      dayLabel = 'Day 0'; sub = 'Starts ' + fmt(START) + ' (in ' + (-idx) + ' day' + (-idx === 1 ? '' : 's') + ')';
      status = 'Not started'; scls = '';
    } else if (idx >= TOTAL) {
      dayLabel = 'Done'; sub = 'The plan window ended ' + fmt(END); status = doneCount() + ' / ' + TOTAL; scls = 'warn';
    } else {
      dayLabel = 'Day ' + (idx + 1); sub = 'of ' + TOTAL + ' &middot; ' + fmt(TODAY);
      var missed = 0;
      for (var i = 0; i < idx; i++) if (get('d:' + days[i].n) !== '1') missed++;
      if (missed === 0) { status = 'On schedule'; scls = 'ok'; }
      else if (missed <= 3) { status = missed + ' day' + (missed > 1 ? 's' : '') + ' open'; scls = 'warn'; }
      else { status = missed + ' days open'; scls = 'bad'; }
    }
    var left = Math.round((END - TODAY) / DAY);
    cards += card('Today', dayLabel, sub, '');
    cards += card('Completed', done + ' / ' + TOTAL, Math.round(done / TOTAL * 100) + '% of all days ticked', '');
    cards += card('Schedule', status, idx >= 0 && scls !== 'ok' && idx < TOTAL ? 'Do not cram: use Saturdays, drop DSA before dropping the build' : 'Compared with days before today', scls);
    cards += card('Deadline', left >= 0 ? left + ' days' : 'passed', 'to ' + fmt(END), '');
    document.getElementById('plstats').innerHTML = cards;
  }

  /* ---- resource chips: text = "Read", video = "Watch" ---------------------- */
  function chip(r, cls) {
    var label = r.t + (r.by ? ' — ' + r.by : '');
    return '<a class="' + cls + '" href="' + esc(r.u) + '" target="_blank" rel="noopener" title="' + esc(r.why || r.t) + '">' + esc(label) + '</a>';
  }

  /* ---- one day card --------------------------------------------------------- */
  function dayCard(x) {
    var dres = (window.DAYRES || {})[x.n] || {};
    var d = x.d, isSat = x.date.getDay() === 6;
    var done = get('d:' + x.n) === '1';
    var isToday = x.date.getTime() === TODAY.getTime();
    var past = x.date < TODAY;
    var cls = 'day' + (isToday ? ' today' : '') + (done ? ' done' : '') + (past && !done ? ' past-open' : '') + (isSat ? ' check' : '');
    var hrs = (isSat ? HRS.sat : HRS[x.ph]).map(function (h) { return '<span>' + h[0] + ' ' + h[1] + 'h</span>'; }).join('');
    var h = '<article class="' + cls + '" id="day-' + x.n + '" data-n="' + x.n + '">';
    h += '<div class="dh2"><span class="dd">' + fmt(x.date) + (isToday ? ' &middot; today' : '') + '</span><span class="dn">DAY ' + x.n + ' / ' + TOTAL + '</span></div>';
    h += '<h4>' + esc(d.t) + '</h4>';
    h += '<div class="hrs">' + hrs + '</div>';
    h += '<div class="dl">Learn</div><ul>' + d.l.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>';
    h += '<div class="dl">Do</div><ul>' + d.b.map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') + '</ul>';
    if (d.s) {
      h += '<div class="dl">DSA &middot; 45 min</div><ul><li>' + esc(d.s) + '</li></ul>';
      var ds = dres.dsa;
      if (ds && ((ds.text || []).length || (ds.video || []).length)) {
        h += '<div class="refs dsa">' + (ds.text || []).map(function (r) { return chip(r, 'rd'); }).join('') +
             (ds.video || []).map(function (r) { return chip(r, 'vid'); }).join('') + '</div>';
      }
    }
    h += '<div class="dw"><b>Done when</b>' + esc(d.d) + '</div>';
    var reads = d.r.map(function (k) { return window.RES[k]; }).filter(Boolean).map(function (r) { return chip(r, 'rd'); })
      .concat((dres.text || []).map(function (r) { return chip(r, 'rd'); }));
    var vids = (dres.video || []).map(function (r) { return chip(r, 'vid'); });
    if (reads.length) h += '<div class="dl">Read</div><div class="refs">' + reads.join('') + '</div>';
    if (vids.length) h += '<div class="dl">Watch</div><div class="refs">' + vids.join('') + '</div>';
    h += '<div class="dfoot"><label class="dchk"><input type="checkbox" data-n="' + x.n + '"' + (done ? ' checked' : '') + '><span>Done and I could do it again without help</span></label>';
    h += '<textarea class="dnote" data-n="' + x.n + '" rows="1" placeholder="Where I got stuck / what to revise" aria-label="Notes for day ' + x.n + '">' + esc(get('n:' + x.n) || '') + '</textarea></div>';
    return h + '</article>';
  }

  /* ---- week blocks ------------------------------------------------------------ */
  var curIdx = dayIndex(TODAY);
  var curWeek = curIdx < 0 ? 0 : (curIdx >= TOTAL ? window.WEEKS.length - 1 : days[curIdx].w);

  var html = '<div class="stats" id="plstats"></div>';
  html += '<div class="toolbar">' +
    '<button class="btn pri" id="jump" type="button">Jump to today</button>' +
    '<button class="btn" id="expand" type="button">Expand all weeks</button>' +
    '<button class="btn" id="collapse" type="button">Collapse all</button>' +
    '<button class="btn" id="export" type="button">Export progress</button>' +
    '<button class="btn" id="import" type="button">Import progress</button>' +
    '<input id="importfile" type="file" accept="application/json" hidden></div>';

  window.WEEKS.forEach(function (w, wi) {
    var ws = days.filter(function (x) { return x.w === wi; });
    var a = ws[0].date, b = ws[ws.length - 1].date;
    html += '<details class="wk" id="wk-' + (wi + 1) + '"' + (wi === curWeek ? ' open' : '') + (w.gate ? ' data-gate="1"' : '') + '>';
    html += '<summary><span class="wn">WEEK ' + String(wi + 1).padStart(2, '0') + '</span>' +
      '<h3 id="w' + (wi + 1) + '" data-toc="W' + (wi + 1) + ' &middot; ' + esc(w.t.split(':')[0]) + '">' + esc(w.t) +
      '<span class="wd">' + fmt(a) + ' &rarr; ' + fmt(b) + ' &middot; days ' + ws[0].n + '&ndash;' + ws[ws.length - 1].n + (w.gate ? ' &middot; GATE' : '') + '</span></h3>' +
      '<span class="wp" id="wp-' + wi + '">0 / ' + ws.length + '<i><b></b></i></span></summary>';
    html += '<p class="wgoal">' + esc(w.goal) + '</p>';
    if ((w.sheets && w.sheets.length) || (w.labs && w.labs.length)) {
      html += '<p class="wlinks">';
      if (w.sheets && w.sheets.length) html += '<span>Read</span>' + w.sheets.map(function (s) { return '<a href="' + s[0] + '">' + esc(s[1]) + '</a>'; }).join('');
      if (w.labs && w.labs.length) html += '<span>Lab</span>' + w.labs.map(function (l) { return '<code>pytest ' + l + '</code>'; }).join(' ');
      html += '</p>';
    }
    if (w.gate) html += '<div class="wgate"><b>Gate</b>' + esc(w.gate) + '</div>';
    html += '<div class="days">' + ws.map(dayCard).join('') + '</div></details>';
  });
  root.innerHTML = html;

  function weekProgress() {
    window.WEEKS.forEach(function (w, wi) {
      var ws = days.filter(function (x) { return x.w === wi; });
      var d = ws.filter(function (x) { return get('d:' + x.n) === '1'; }).length;
      var el = document.getElementById('wp-' + wi);
      if (!el) return;
      el.firstChild.nodeValue = d + ' / ' + ws.length;
      el.querySelector('b').style.width = (d / ws.length * 100) + '%';
    });
  }
  stats(); weekProgress();

  /* ---- events -------------------------------------------------------------------- */
  root.addEventListener('change', function (e) {
    var t = e.target;
    if (t.matches('.dchk input')) {
      var n = t.getAttribute('data-n');
      set('d:' + n, t.checked ? '1' : '0');
      var card = document.getElementById('day-' + n);
      var x = days[n - 1];
      card.classList.toggle('done', t.checked);
      card.classList.toggle('past-open', !t.checked && x.date < TODAY);
      stats(); weekProgress();
    }
  });
  root.addEventListener('input', function (e) {
    var t = e.target;
    if (t.matches('.dnote')) set('n:' + t.getAttribute('data-n'), t.value);
  });

  document.getElementById('jump').addEventListener('click', function () {
    var idx = dayIndex(TODAY), n = idx < 0 ? 1 : Math.min(idx + 1, TOTAL);
    var wk = document.getElementById('wk-' + (days[n - 1].w + 1));
    wk.open = true;
    document.getElementById('day-' + n).scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  document.getElementById('expand').addEventListener('click', function () { root.querySelectorAll('details.wk').forEach(function (d) { d.open = true; }); });
  document.getElementById('collapse').addEventListener('click', function () { root.querySelectorAll('details.wk').forEach(function (d) { d.open = false; }); });

  /* ---- export / import ------------------------------------------------------------- */
  function collect() {
    var out = {};
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k.indexOf('bd:pl:') === 0 || k.indexOf('bd:tr:') === 0) out[k] = localStorage.getItem(k);
      }
    } catch (e) {}
    return out;
  }
  document.getElementById('export').addEventListener('click', function () {
    var blob = new Blob([JSON.stringify({ exported: new Date().toISOString(), data: collect() }, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'roadmap-progress-' + TODAY.getFullYear() + '-' + (TODAY.getMonth() + 1) + '-' + TODAY.getDate() + '.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  });
  document.getElementById('import').addEventListener('click', function () { document.getElementById('importfile').click(); });
  document.getElementById('importfile').addEventListener('change', function (e) {
    var f = e.target.files[0]; if (!f) return;
    var r = new FileReader();
    r.onload = function () {
      try {
        var obj = JSON.parse(r.result).data, n = 0;
        Object.keys(obj).forEach(function (k) {
          if (k.indexOf('bd:pl:') === 0 || k.indexOf('bd:tr:') === 0) { localStorage.setItem(k, String(obj[k])); n++; }
        });
        alert('Imported ' + n + ' entries. The page will reload.');
        location.reload();
      } catch (err) { alert('That file is not a valid progress export.'); }
    };
    r.readAsText(f);
  });
})();

/* ---- week-by-week table on the plan sheet (same data, no second copy) ------ */
(function () {
  'use strict';
  var tb = document.getElementById('weektable');
  if (!tb || !window.WEEKS) return;
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var p = window.PLAN_START.split('-'), start = new Date(+p[0], +p[1] - 1, +p[2]);
  function f(d) { return d.getDate() + ' ' + MON[d.getMonth()]; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  var n = 0, h = '';
  window.WEEKS.forEach(function (w, i) {
    var a = new Date(start.getFullYear(), start.getMonth(), start.getDate() + n);
    var b = new Date(start.getFullYear(), start.getMonth(), start.getDate() + n + w.days.length - 1);
    n += w.days.length;
    var deliver = (w.days[5] || w.days[w.days.length - 1]).d;
    h += '<tr><td>W' + (i + 1) + (w.gate ? ' <span class="chip on">gate</span>' : '') + '</td><td>' + f(a) + ' &ndash; ' + f(b) + '</td><td>' + esc(w.t) + '</td><td>' + esc(deliver) + '</td></tr>';
  });
  tb.innerHTML = h;
})();
