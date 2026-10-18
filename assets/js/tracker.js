/* ============================================================================
   Skills tracker + weekly review. Renders into #tracker and #reviewform.
   Levels 4 and 5 are blocked until the evidence box has text: a level is a claim,
   and a claim needs something checkable behind it (repo link, test run, date).
   Storage (localStorage, 'bd:' prefix shared with sheet.js):
     bd:tr:l:<id>      level 0-5
     bd:tr:e:<id>      evidence text
     bd:tr:r:<w>:<f>   weekly review field f for week w
   ==========================================================================*/
(function () {
  'use strict';
  var root = document.getElementById('tracker');
  if (!root) return;

  var P = 'bd:tr:';
  function get(k) { try { return localStorage.getItem(P + k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(P + k, v); } catch (e) {} }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

  var LEVELS = [
    ['0', 'Not started'],
    ['1', 'Read / watched'],
    ['2', 'Understand'],
    ['3', 'With guidance'],
    ['4', 'Independent'],
    ['5', 'Debug + trade-offs']
  ];

  var SKILLS = [
    { id: 'python', t: 'Python independence', g: 'Gate 1: count_errors plus 3 tests from a blank file in 30 minutes, no AI, no search.' },
    { id: 'debug', t: 'Debugging', g: 'Find the root cause of 3 unfamiliar bugs aloud using reproduce, isolate, hypothesise, one change at a time.' },
    { id: 'dsa', t: 'DSA', g: 'Solve an unseen medium in 30 minutes in each of: hash map, two pointers, sliding window, tree, graph BFS.' },
    { id: 'sql', t: 'SQL', g: 'From memory: LEFT JOIN with GROUP BY and HAVING on your own schema; read an EXPLAIN plan and say what an index changed.' },
    { id: 'api', t: 'API development', g: 'A FastAPI + Pydantic service with validation, correct status codes, and tests for every route including failures.' },
    { id: 'backend', t: 'Backend engineering', g: 'Gate 2: mock vendor integration survives timeout, duplicate and bad-signature scenarios; you can explain why.' },
    { id: 'testing', t: 'Testing', g: 'pytest with fixtures and parametrize; fakes for external services; a test for every failure mode you listed.' },
    { id: 'rag', t: 'RAG', g: 'Project 1: configurable chunking, hybrid retrieval, citations, refusal, and an eval script with recall@k.' },
    { id: 'agents', t: 'Agent workflows', g: 'Agent loop built from scratch with validation, limits and a persisted approval step; written view on workflow vs agent.' },
    { id: 'mcp', t: 'MCP', g: 'Gate 4: build, test and secure a small MCP server; explain client, server, tool, and what blocks a bad tool call.' },
    { id: 'security', t: 'Security', g: 'OWASP API and LLM reviews of your own two projects, with one injection attack demonstrated and mitigated.' },
    { id: 'deploy', t: 'Deployment', g: 'Docker Compose brings up each project from a clean clone using only the README.' },
    { id: 'projects', t: 'Project completion', g: 'Project 1 and Project 2 each have README, tests, architecture doc, demo script and honest limitations.' },
    { id: 'interview', t: 'Interview readiness', g: 'Two full mock loops with written feedback, and the top 3 feedback items visibly improved in the second.' }
  ];

  function level(id) { var v = parseInt(get('l:' + id) || '0', 10); return isNaN(v) ? 0 : v; }

  function skillHTML(s) {
    var lv = level(s.id), ev = get('e:' + s.id) || '';
    var h = '<div class="skill" data-id="' + s.id + '"><div><h4>' + esc(s.t) + '</h4><p class="gate"><b>Verified by</b> ' + esc(s.g) + '</p></div><div>';
    h += '<div class="lv" role="radiogroup" aria-label="' + esc(s.t) + ' level">';
    LEVELS.forEach(function (L) {
      var n = parseInt(L[0], 10);
      h += '<label class="' + (lv === n ? 'sel' : '') + '"><input type="radio" name="lv-' + s.id + '" value="' + L[0] + '"' + (lv === n ? ' checked' : '') + '><b>' + L[0] + '</b>' + esc(L[1]) + '</label>';
    });
    h += '</div><textarea class="evid" data-id="' + s.id + '" rows="2" placeholder="Evidence (required for 4 and 5): repo or commit link, the test run, the date, what you did with no AI help." aria-label="Evidence for ' + esc(s.t) + '">' + esc(ev) + '</textarea>';
    h += '<p class="evnote" id="en-' + s.id + '">Levels 4 and 5 stay locked until evidence is written.</p></div></div>';
    return h;
  }

  root.innerHTML =
    '<div class="stats"><div class="stat"><div class="sk">At level 4 or 5</div><div class="sv" id="trsum">0 / ' + SKILLS.length + '</div><div class="ss">Evidence-backed only</div></div>' +
    '<div class="stat"><div class="sk">Average level</div><div class="sv" id="travg">0.0</div><div class="ss">Across all ' + SKILLS.length + ' areas</div></div>' +
    '<div class="stat"><div class="sk">Lowest area</div><div class="sv" id="trlow" style="font-size:20px">-</div><div class="ss">Where to look first</div></div>' +
    '<div class="stat"><div class="sk">Missing evidence</div><div class="sv" id="trmiss">0</div><div class="ss">Level 3+ with no evidence text</div></div></div>' +
    '<div class="skills">' + SKILLS.map(skillHTML).join('') + '</div>';

  function summary() {
    var hi = 0, sum = 0, low = null, miss = 0;
    SKILLS.forEach(function (s) {
      var l = level(s.id); sum += l; if (l >= 4) hi++;
      if (low === null || l < low.l) low = { l: l, t: s.t };
      if (l >= 3 && !(get('e:' + s.id) || '').trim()) miss++;
    });
    document.getElementById('trsum').textContent = hi + ' / ' + SKILLS.length;
    document.getElementById('travg').textContent = (sum / SKILLS.length).toFixed(1);
    document.getElementById('trlow').textContent = low.t + ' (' + low.l + ')';
    document.getElementById('trmiss').textContent = miss;
  }
  summary();

  function paint(id) {
    var box = root.querySelector('.skill[data-id="' + id + '"]'), lv = level(id);
    box.querySelectorAll('.lv label').forEach(function (lb, i) { lb.classList.toggle('sel', i === lv); });
    box.querySelectorAll('.lv input').forEach(function (inp, i) { inp.checked = i === lv; });
  }
  function need(id, on) {
    var ta = root.querySelector('.evid[data-id="' + id + '"]'), n = document.getElementById('en-' + id);
    ta.classList.toggle('need', on); n.classList.toggle('need', on);
    n.textContent = on ? 'Write the evidence first, then choose level 4 or 5.' : 'Levels 4 and 5 stay locked until evidence is written.';
  }

  root.addEventListener('change', function (e) {
    var t = e.target;
    if (!t.matches('.lv input')) return;
    var id = t.name.replace('lv-', ''), v = parseInt(t.value, 10);
    var ev = (get('e:' + id) || '').trim();
    if (v >= 4 && !ev) { paint(id); need(id, true); root.querySelector('.evid[data-id="' + id + '"]').focus(); return; }
    need(id, false); set('l:' + id, String(v)); paint(id); summary();
  });
  root.addEventListener('input', function (e) {
    var t = e.target;
    if (!t.matches('.evid')) return;
    var id = t.getAttribute('data-id');
    set('e:' + id, t.value);
    if (level(id) >= 4 && !t.value.trim()) { set('l:' + id, '3'); paint(id); need(id, true); }
    else need(id, false);
    summary();
  });

  /* ------------------------------------------------------------------ weekly review */
  var rv = document.getElementById('reviewform');
  if (!rv) return;
  var START = new Date(2026, 10, 1), now = new Date(), T = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var cw = Math.floor(Math.round((T - START) / 864e5) / 7) + 1;
  if (cw < 1) cw = 1; if (cw > 22) cw = 22;

  var F = [
    ['done', 'What I completed this week'],
    ['stuck', 'What I still struggle with (specific, not "Python")'],
    ['revise', 'What I should revise'],
    ['next', 'What I should build next'],
    ['changes', 'What should change in the following week']
  ];

  var sel = '<label><span>Week</span><select id="rvweek">';
  for (var w = 1; w <= 22; w++) sel += '<option value="' + w + '"' + (w === cw ? ' selected' : '') + '>Week ' + w + '</option>';
  sel += '</select></label>';
  var body = F.map(function (f) { return '<label><span>' + f[1] + '</span><textarea data-f="' + f[0] + '" rows="2"></textarea></label>'; }).join('');
  body += '<label><span>On schedule?</span><select data-f="sched"><option value="">Choose</option><option>Yes</option><option>Slightly behind</option><option>Behind: re-plan needed</option></select></label>';
  rv.innerHTML = sel + body + '<div class="toolbar"><button class="btn pri" id="rvcopy" type="button">Copy this review as text</button><span class="evnote" id="rvmsg"></span></div>';

  function week() { return document.getElementById('rvweek').value; }
  function load() {
    rv.querySelectorAll('[data-f]').forEach(function (el) { el.value = get('r:' + week() + ':' + el.getAttribute('data-f')) || ''; });
  }
  load();
  document.getElementById('rvweek').addEventListener('change', load);
  rv.addEventListener('input', function (e) { var f = e.target.getAttribute('data-f'); if (f) set('r:' + week() + ':' + f, e.target.value); });
  rv.addEventListener('change', function (e) { var f = e.target.getAttribute('data-f'); if (f) set('r:' + week() + ':' + f, e.target.value); });

  document.getElementById('rvcopy').addEventListener('click', function () {
    var lines = ['Weekly review - week ' + week()];
    F.concat([['sched', 'On schedule?']]).forEach(function (f) {
      var el = rv.querySelector('[data-f="' + f[0] + '"]'); lines.push(f[1] + ': ' + (el.value || '-'));
    });
    lines.push('', 'Skill levels:');
    SKILLS.forEach(function (s) { lines.push('- ' + s.t + ': ' + level(s.id) + ((get('e:' + s.id) || '').trim() ? ' (evidence given)' : '')); });
    var text = lines.join('\n'), msg = document.getElementById('rvmsg');
    var ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); msg.textContent = 'Copied. Paste it into the chat for your weekly review.'; }
    catch (err) { msg.textContent = 'Could not copy automatically.'; }
    document.body.removeChild(ta);
  });
})();
