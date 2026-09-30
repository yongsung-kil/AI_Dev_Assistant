"""status.json과 md 문서로 정적 대시보드(dashboard/)를 만든다.

사용: python render_dashboard.py [프로젝트 폴더]
산출: dashboard/index.html, dashboard/changelog.html, dashboard/docs/{md 경로}.html,
      dashboard/assets/{style.css, app.js, search.js}, dashboard/status.json
규격: docs/html_guide.md (왼쪽 사이드바는 일 갈래 묶음과 그 아래 폴더를 단계별로 접고 편다, 위 검색,
      오른쪽 "이 페이지의 차례", 첫 화면은 계획, 진행 중, 완료 세 칸의 보드, 변경 이력은 완료 작업 단위. 상대 링크만, 외부 자원 없음).
사이드바 묶음은 dashboard/config.json의 "sidebar" 목록이 정한다 (없으면 DEFAULT_SIDEBAR).
렌더 뒤 상대 링크가 가리키는 파일이 없으면 보고하고 종료 코드 1.
"""
import html as htmllib
import io
import json
import os
import re
import shutil
import sys
from urllib.parse import quote, unquote

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_status  # noqa: E402
import md_to_html  # noqa: E402

OUT = "dashboard"
HREF = re.compile(r'(?:href|src)="([^"]+)"')

# 사이드바 묶음: 이름과 그 묶음에 드는 경로(폴더 또는 md 파일). 폴더 경로가 하나뿐인 묶음은 그 폴더의 내용이 묶음 바로 아래에 오고,
# 폴더 경로가 둘 이상이면 폴더마다 항목이 된다. 어느 묶음에도 들지 않는 문서는 "기타 문서"로 간다.
DEFAULT_SIDEBAR = [
    {"name": "온보딩", "paths": ["README.md", "CLAUDE.md", "docs/profile", "docs/explore", "docs/adr"]},
    {"name": "작업 관리", "paths": ["_pm"]},
    {"name": "논문", "paths": ["papers"]},
    {"name": "아이디어 적용", "paths": ["ideas"]},
    {"name": "최적화", "paths": ["docs/speed_opt", "docs/robustness", "optim"]},
    {"name": "위키", "paths": ["_wiki"]},
]
OTHER_GROUP = "기타 문서"
FOLDER_LABELS = {"profile": "프로파일", "explore": "탐색 결과", "adr": "설계 기록", "tasks": "진행 중 작업", "done": "완료 작업",
                 "decisions": "결정", "trials": "시도", "assets": "자산", "tech": "기술", "_templates": "양식", "_template": "양식",
                 "_inbox": "대기함", "speed_opt": "속도 최적화", "robustness": "안정성 검사", "optim": "파라미터 최적화",
                 "analysis": "분석 문서", "screened": "선별 결과"}
FIRST_FILES = ["README.md", "TODO.md", "DONE.md", "manual.md", "MOC.md", "checklist.md", "overview.md"]

DARK_VARS = """--bg: #0d1117; --surface: #161b22; --text: #e6edf3; --muted: #8b949e; --border: #30363d;
  --accent: #58a6ff; --accent-soft: rgba(88, 166, 255, 0.16); --ok: #3fb950; --warn: #d29922;
  --planned: #60a5fa; --doing: #c084fc;"""

STYLE = """:root {
  --bg: #ffffff; --surface: #f6f8fa; --text: #24292f; --muted: #57606a; --border: #d0d7de;
  --accent: #0969da; --accent-soft: #ddf4ff; --ok: #1a7f37; --warn: #bf8700;
  --planned: #2563eb; --doing: #7c3aed;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { DARK } }
:root[data-theme="dark"] { DARK }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font-size: 16px; line-height: 1.7; word-break: keep-all; overflow-wrap: anywhere;
       font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: Consolas, "D2Coding", monospace; font-size: 0.9em; background: var(--surface); padding: 0.15em 0.4em; border-radius: 4px; }
pre { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 12px 16px; overflow-x: auto; }
pre code { background: none; padding: 0; }
svg { display: inline-block; vertical-align: middle; }
.top { position: sticky; top: 0; z-index: 5; display: flex; gap: 12px; align-items: center; padding: 8px 16px;
       background: var(--surface); border-bottom: 1px solid var(--border); }
.brand { font-weight: 700; white-space: nowrap; color: var(--text); }
.icon-btn { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: 1px solid var(--border);
            border-radius: 6px; background: var(--bg); color: var(--muted); cursor: pointer; padding: 0; }
.icon-btn:hover { color: var(--text); border-color: var(--muted); }
.seg { display: inline-flex; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-left: auto; }
.seg button { border: 0; background: var(--bg); color: var(--muted); width: 32px; height: 30px; cursor: pointer; padding: 0; }
.seg button.on { background: var(--accent-soft); color: var(--accent); }
.search-wrap { position: relative; flex: 1; max-width: 520px; }
#search { width: 100%; padding: 6px 10px 6px 32px; border: 1px solid var(--border); border-radius: 8px;
          background: var(--bg); color: var(--text); font-size: 15px; }
.search-wrap .lens { position: absolute; left: 10px; top: 9px; color: var(--muted); pointer-events: none; }
#search-results { position: absolute; top: 40px; left: 0; right: 0; background: var(--bg); z-index: 6;
                  border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,.15); padding: 6px; }
#search-results a { display: block; padding: 6px 8px; border-radius: 4px; }
#search-results a:hover { background: var(--surface); text-decoration: none; }
#search-results .snippet { color: var(--muted); font-size: 0.85em; }
.layout { display: grid; grid-template-columns: 270px minmax(0, 880px) 220px; gap: 28px; padding: 16px; }
html.nav-closed .layout { grid-template-columns: minmax(0, 880px) 220px; }
html.nav-closed .sidebar { display: none; }
.sidebar { position: sticky; top: 52px; align-self: start; max-height: calc(100vh - 68px); overflow-y: auto; padding-right: 6px; font-size: 13px; }
.sidebar .nav-top { margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.sidebar .nav-top a { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 6px; font-weight: 600; font-size: 14.5px; color: var(--text); }
.sidebar a:hover, .sidebar summary:hover { background: var(--surface); text-decoration: none; }
.sidebar details { margin: 1px 0; }
.sidebar summary { list-style: none; display: flex; align-items: center; justify-content: space-between; gap: 6px; cursor: pointer;
                   padding: 6px 10px; border-radius: 6px; line-height: 1.35; }
.sidebar summary::-webkit-details-marker { display: none; }
.sidebar summary a { color: inherit; }
.sidebar .chev { flex: none; width: 14px; height: 14px; color: var(--muted); transition: transform 0.15s ease; }
.sidebar details[open] > summary .chev { transform: rotate(90deg); }
.sidebar ul { list-style: none; margin: 0 0 2px 16px; padding: 0 0 0 8px; border-left: 1px solid var(--border); }
.sidebar li { margin: 0; }
.sidebar li > a, .sidebar li > span { display: flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 6px; color: var(--muted);
                                       line-height: 1.35; }
details.nav-l1 > summary { font-size: 15px; font-weight: 700; color: var(--text); }
details.nav-l2 > summary, li.nav-l2 { font-size: 14px; font-weight: 500; }
details.nav-l2 > summary { color: var(--text); }
details.nav-l3 > summary, li.nav-l3 { font-size: 13.5px; font-weight: 400; }
details.nav-l4 > summary, li.nav-l4, details.nav-l5 > summary, li.nav-l5, details.nav-l6 > summary, li.nav-l6 { font-size: 13px; font-weight: 400; }
.sidebar a.current, .sidebar summary.current { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.sidebar .done { opacity: 0.7; }
.content { min-width: 0; }
.content h1 { font-size: 1.9em; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; margin-top: 0.4em; }
.content h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; margin-top: 1.6em; }
.content h3 { font-size: 1.15em; }
.content table { border-collapse: collapse; margin: 1em 0; display: block; overflow-x: auto; }
.content th, .content td { border: 1px solid var(--border); padding: 6px 12px; text-align: left; vertical-align: top; }
.content th { background: var(--surface); }
.content tr:nth-child(even) td { background: var(--surface); }
.content blockquote { margin: 0.8em 0; padding: 0.4em 1em; border-left: 4px solid var(--border); color: var(--muted); background: var(--surface); }
.lead { color: var(--muted); margin-top: -0.4em; }
.toc { position: sticky; top: 52px; align-self: start; font-size: 0.88em; max-height: calc(100vh - 68px); overflow-y: auto; }
.toc-title { font-weight: 600; margin-bottom: 8px; color: var(--text); }
.toc ul { list-style: none; padding: 0; margin: 0; border-left: 1px solid var(--border); }
.toc li a { display: block; padding: 3px 12px; margin-left: -1px; border-left: 2px solid transparent; color: var(--muted); }
.toc li.h3 a { padding-left: 24px; }
.toc a:hover { color: var(--text); text-decoration: none; }
.toc a.active { border-left-color: var(--accent); color: var(--text); font-weight: 500; }
.board { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 16px 0; }
.col { --col: var(--muted); border: 1px solid var(--border); border-bottom: 3px solid var(--col); border-radius: 12px; padding: 12px;
       background: var(--surface); min-height: 120px; }
.col-planned { --col: var(--planned); } .col-doing { --col: var(--doing); } .col-done { --col: var(--ok); }
.col-head { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
            color: var(--col); margin: 2px 4px 12px; }
.col-head .count { color: var(--muted); font-weight: 500; letter-spacing: 0; }
.col .empty { color: var(--muted); font-size: 0.9em; padding: 4px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { display: block; border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; background: var(--bg); color: var(--text); }
.col .card { margin-bottom: 10px; }
.col .card:last-child { margin-bottom: 0; }
a.card:hover { border-color: var(--accent); text-decoration: none; }
.card-title { font-weight: 600; margin-bottom: 4px; line-height: 1.4; }
.card-desc { color: var(--muted); font-size: 0.88em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-foot { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 10px; font-size: 12px; color: var(--muted); }
.card-foot .ok { color: var(--ok); display: inline-flex; align-items: center; gap: 4px; }
.progress { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress .bar { height: 100%; background: var(--col, var(--ok)); }
.pill { flex: none; border: 1px solid var(--border); border-radius: 6px; padding: 0 8px; background: var(--surface); color: var(--text); }
.card-meta { color: var(--muted); font-size: 0.85em; margin-top: 4px; }
.badge { display: inline-block; padding: 0 8px; border-radius: 10px; font-size: 0.78em; line-height: 1.6; color: #fff; white-space: nowrap; }
.badge.warn { background: var(--warn); } .badge.ok { background: var(--ok); }
.badge.tag { background: var(--accent-soft); color: var(--accent); border: 1px solid var(--accent); }
.review { display: flex; gap: 14px; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid var(--border); }
.review .vote { flex: none; width: 46px; border: 1px solid var(--border); border-radius: 8px; text-align: center; padding: 4px 0; line-height: 1.3;
                font-weight: 700; background: var(--surface); }
.review .vote small { display: block; font-weight: 400; font-size: 11px; color: var(--muted); }
.review-title { font-weight: 600; font-size: 1.05em; }
.range { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; background: var(--surface); margin: 16px 0; }
.range label { display: block; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
.range select { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text); font-size: 15px; }
.tabs { display: flex; flex-wrap: wrap; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin: 12px 0 20px; }
.tab { flex: 1 1 auto; border: 0; border-right: 1px solid var(--border); background: var(--surface); color: var(--muted); padding: 10px 14px;
       cursor: pointer; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
.tab:last-child { border-right: 0; }
.tab .count { border-radius: 10px; padding: 0 8px; font-size: 12px; background: var(--border); color: var(--text); }
.tab.active { background: var(--bg); color: var(--text); font-weight: 600; box-shadow: inset 0 -2px 0 var(--accent); }
.tab.active .count { background: var(--accent); color: #fff; }
.ver { margin: 20px 0 8px; font-size: 1.15em; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
.changes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.change { border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; background: var(--surface); }
.change-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px; color: var(--muted); }
.change-title { font-weight: 600; margin-bottom: 4px; }
.change p { margin: 0 0 6px; color: var(--muted); font-size: 0.92em; }
.change ul { margin: 0; padding-left: 18px; font-size: 0.85em; color: var(--muted); }
.hidden { display: none !important; }
.orphan { color: var(--warn); }
.foot { color: var(--muted); font-size: 0.85em; padding: 16px; border-top: 1px solid var(--border); }
@media (max-width: 1100px) { .layout { grid-template-columns: 250px minmax(0, 1fr); } html.nav-closed .layout { grid-template-columns: minmax(0, 1fr); }
                             .toc { display: none; } .board { grid-template-columns: 1fr; } .changes { grid-template-columns: 1fr; } }
@media (max-width: 700px) { .layout { grid-template-columns: 1fr; } .sidebar { position: static; max-height: none; } .range { grid-template-columns: 1fr; } }
""".replace("DARK", DARK_VARS)

APP_JS = """(function () {
  var prefix = window.DASH_PREFIX || "";
  var root = document.documentElement;
  function store(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
  var input = document.getElementById("search");
  var box = document.getElementById("search-results");
  if (input && box) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      if (!q || !window.DASH_INDEX) { box.hidden = true; box.innerHTML = ""; return; }
      var hits = [];
      for (var i = 0; i < window.DASH_INDEX.length && hits.length < 20; i++) {
        var d = window.DASH_INDEX[i];
        var t = d.title.toLowerCase(), b = d.text.toLowerCase();
        var at = t.indexOf(q) >= 0 ? -1 : b.indexOf(q);
        if (t.indexOf(q) >= 0 || at >= 0) {
          var snip = at >= 0 ? d.text.substring(Math.max(0, at - 40), at + 60) : d.text.substring(0, 80);
          hits.push('<a href="' + prefix + d.path + '">' + esc(d.title) + '<div class="snippet">' + esc(snip) + '</div></a>');
        }
      }
      box.innerHTML = hits.length ? hits.join("") : '<div class="snippet">결과 없음</div>';
      box.hidden = false;
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target) && e.target !== input) { box.hidden = true; } });
    document.addEventListener("keydown", function (e) { if ((e.ctrlKey || e.metaKey) && e.key === "k") { e.preventDefault(); input.focus(); } });
  }
  var navToggle = document.getElementById("nav-toggle");
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var closed = root.classList.toggle("nav-closed");
      store("dash-nav", closed ? "closed" : "open");
    });
  }
  var themeBox = document.getElementById("theme-toggle");
  if (themeBox) {
    var buttons = themeBox.querySelectorAll("button");
    function mark() {
      var cur = root.getAttribute("data-theme") || "";
      for (var i = 0; i < buttons.length; i++) { buttons[i].classList.toggle("on", buttons[i].getAttribute("data-theme") === cur); }
    }
    for (var j = 0; j < buttons.length; j++) {
      buttons[j].addEventListener("click", function () {
        var v = this.getAttribute("data-theme");
        if (v) { root.setAttribute("data-theme", v); } else { root.removeAttribute("data-theme"); }
        store("dash-theme", v);
        mark();
      });
    }
    mark();
  }
  var heads = document.querySelectorAll(".content h2, .content h3");
  var tocLinks = document.querySelectorAll(".toc a");
  if (heads.length && tocLinks.length && "IntersectionObserver" in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          for (var k = 0; k < tocLinks.length; k++) { tocLinks[k].classList.toggle("active", tocLinks[k].getAttribute("href") === "#" + en.target.id); }
        }
      });
    }, { rootMargin: "0px 0px -70% 0px" });
    for (var m = 0; m < heads.length; m++) { obs.observe(heads[m]); }
  }
  var from = document.getElementById("range-from"), to = document.getElementById("range-to");
  if (from && to) {
    var month = "";
    function applyFilter() {
      var lo = from.value, hi = to.value;
      if (lo > hi) { var tmp = lo; lo = hi; hi = tmp; }
      var changes = document.querySelectorAll(".change");
      var shown = {};
      for (var i = 0; i < changes.length; i++) {
        var d = changes[i].getAttribute("data-date");
        var ok = d >= lo && d <= hi && (!month || changes[i].getAttribute("data-month") === month);
        changes[i].classList.toggle("hidden", !ok);
        if (ok) { shown[d] = true; }
      }
      var vers = document.querySelectorAll(".ver");
      for (var v = 0; v < vers.length; v++) { vers[v].classList.toggle("hidden", !shown[vers[v].getAttribute("data-date")]); }
      var grids = document.querySelectorAll(".changes");
      for (var g = 0; g < grids.length; g++) { grids[g].classList.toggle("hidden", !shown[grids[g].getAttribute("data-date")]); }
    }
    from.addEventListener("change", applyFilter);
    to.addEventListener("change", applyFilter);
    var tabs = document.querySelectorAll(".tab");
    for (var t = 0; t < tabs.length; t++) {
      tabs[t].addEventListener("click", function () {
        month = this.getAttribute("data-month") || "";
        for (var u = 0; u < tabs.length; u++) { tabs[u].classList.toggle("active", tabs[u] === this); }
        applyFilter();
      });
    }
    applyFilter();
  }
})();
"""

ICON_PANEL = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
              '<rect x="3" y="4" width="18" height="16" rx="2"/><line x1="9" y1="4" x2="9" y2="20"/></svg>')
ICON_LENS = ('<svg class="lens" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
             '<circle cx="11" cy="11" r="7"/><line x1="20" y1="20" x2="16.5" y2="16.5"/></svg>')
ICON_SYSTEM = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
               '<rect x="3" y="4" width="18" height="12" rx="2"/><line x1="8" y1="20" x2="16" y2="20"/><line x1="12" y1="16" x2="12" y2="20"/></svg>')
ICON_SUN = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
            '<circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="2" y1="12" x2="5" y2="12"/>'
            '<line x1="19" y1="12" x2="22" y2="12"/><line x1="4.9" y1="4.9" x2="7" y2="7"/><line x1="17" y1="17" x2="19.1" y2="19.1"/>'
            '<line x1="4.9" y1="19.1" x2="7" y2="17"/><line x1="17" y1="7" x2="19.1" y2="4.9"/></svg>')
ICON_MOON = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>')
ICON_CHEV = ('<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
             '<polyline points="9 6 15 12 9 18"/></svg>')
ICON_HOME = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/>'
             '<rect x="13" y="13" width="8" height="8" rx="1.5"/></svg>')
ICON_LOG = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
            '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15.5 14"/></svg>')
ICON_PLANNED = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
                '<rect x="3" y="5" width="18" height="16" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="3" x2="8" y2="7"/><line x1="16" y1="3" x2="16" y2="7"/></svg>')
ICON_DOING = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M14.5 5.5a4 4 0 0 0 5 5L9 21l-4-4z"/><path d="M19.5 10.5l-5-5"/></svg>')
ICON_DONE = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<circle cx="12" cy="12" r="9"/><polyline points="8 12 11 15 16 9"/></svg>')
ICON_CHECK = ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
              '<polyline points="5 12 10 17 19 8"/></svg>')

FRAME = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
<script>try {{ var t = localStorage.getItem("dash-theme"); if (t) document.documentElement.setAttribute("data-theme", t);
if (localStorage.getItem("dash-nav") === "closed") document.documentElement.classList.add("nav-closed"); }} catch (e) {{}}</script>
</head>
<body>
<header class="top">
<button id="nav-toggle" class="icon-btn" type="button" title="사이드바 접기와 펴기" aria-label="사이드바 접기와 펴기">PANEL</button>
<a class="brand" href="{prefix}index.html">{project}</a>
<div class="search-wrap">LENS<input id="search" type="search" placeholder="검색 (제목과 본문, Ctrl K)" autocomplete="off">
<div id="search-results" hidden></div></div>
<div id="theme-toggle" class="seg" title="테마">
<button type="button" data-theme="" title="시스템 설정 따름">SYSTEM</button><button type="button" data-theme="light" title="밝게">SUN</button><button type="button" data-theme="dark" title="어둡게">MOON</button>
</div>
</header>
<div class="layout">
<nav class="sidebar">
{sidebar}
</nav>
<main class="content">
{body}
</main>
<aside class="toc"><div class="toc-title">이 페이지의 차례</div>
{toc}
</aside>
</div>
<footer class="foot">생성: {generated}</footer>
<script>window.DASH_PREFIX = {prefix_json};</script>
<script src="{prefix}assets/search.js"></script>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
""".replace("PANEL", ICON_PANEL).replace("LENS", ICON_LENS).replace("SYSTEM", ICON_SYSTEM).replace("SUN", ICON_SUN).replace("MOON", ICON_MOON)


def esc(text):
    return htmllib.escape(str(text), quote=True)


def html_path(doc_path):
    """md 상대 경로를 dashboard/ 기준 html 경로로."""
    return "docs/" + doc_path[:-3] + ".html"


def href_from(page_dir, target, anchor=""):
    """page_dir(dashboard 기준 폴더)에서 target(dashboard 기준 경로)으로 가는 퍼센트 인코딩 상대 링크."""
    relative = os.path.relpath(target, page_dir or ".").replace(os.sep, "/")
    return quote(relative, safe="/") + (f"#{anchor}" if anchor else "")


def find_detail_doc(detail, doc_paths):
    """TODO의 상세 폴더에서 대표 md를 고른다 (폴더 이름과 같은 md, 없으면 첫 md)."""
    if not detail:
        return None
    folder = detail.strip("/")
    candidates = sorted(p for p in doc_paths if p.startswith(folder + "/") and p.endswith(".md"))
    if not candidates:
        return None
    main_doc = folder + "/" + os.path.basename(folder) + ".md"
    return main_doc if main_doc in candidates else candidates[0]


def toc_html(headings):
    if not headings:
        return "<p class=\"snippet\">없음</p>"
    items = [f'<li class="h{level}"><a href="#{esc(hid)}">{esc(text)}</a></li>' for level, text, hid in headings if level in (2, 3)]
    return "<ul>" + "".join(items) + "</ul>"


# ---------------------------------------------------------------- 사이드바 트리

def _node(label, key=None, doc=None, target=None):
    return {"label": label, "key": key, "doc": doc, "target": target, "anchor": "", "children": [], "badge": None, "done": False}


def _decision_state(doc_path, decisions):
    d = decisions.get(doc_path)
    if not d:
        return None, False
    pending = sum(1 for q in d["questions"] if not q["answered"])
    return (f"미답 {pending}" if pending else None), pending == 0


def _insert(folder, parts, doc, decisions):
    """folder 노드 아래에 parts(폴더 이름들과 마지막 파일 이름) 경로로 문서 잎을 넣는다."""
    for name in parts[:-1]:
        child = next((c for c in folder["children"] if c["key"] == name), None)
        if child is None:
            child = _node(FOLDER_LABELS.get(name, name), key=name)
            folder["children"].append(child)
        folder = child
    leaf = _node(doc["title"], doc=doc, target=html_path(doc["path"]))
    leaf["badge"], leaf["done"] = _decision_state(doc["path"], decisions)
    folder["children"].append(leaf)


MOC_FILE = re.compile(r"MOC([-_ .].*)?\.md$")


def _representative_rank(doc, folder_key):
    """폴더 대표 문서의 우선순위. 폴더 이름.md, README.md, index.md, MOC 파일 순. 대표가 아니면 None."""
    name = os.path.basename(doc["path"])
    if name == os.path.basename(folder_key) + ".md":
        return 0
    if name == "README.md":
        return 1
    if name == "index.md":
        return 2
    if MOC_FILE.match(name):
        return 3
    return None


def _finalize(folder, is_group):
    """자식을 정렬하고, 폴더의 대표 문서(폴더 이름.md, README.md, index.md, MOC 파일 순)를 폴더 항목의 링크로 올린다.
    대표 문서만 있던 폴더는 잎이 된다."""
    docs = [c for c in folder["children"] if c["doc"] is not None]
    folders = [c for c in folder["children"] if c["doc"] is None]
    for f in folders:
        _finalize(f, False)

    def doc_order(c):
        name = os.path.basename(c["doc"]["path"])
        return (FIRST_FILES.index(name) if name in FIRST_FILES else len(FIRST_FILES), c["label"])

    docs.sort(key=doc_order)
    folders.sort(key=lambda c: c["label"])
    if not is_group:
        ranked = [(rank, c) for c in docs for rank in [_representative_rank(c["doc"], folder["key"])] if rank is not None]
        if ranked:
            rep = min(ranked, key=lambda rc: rc[0])[1]
            docs.remove(rep)
            if os.path.basename(folder["key"]) not in FOLDER_LABELS:  # 이름이 정해진 폴더는 그 이름을 지키고, 아니면 대표 문서 제목을 쓴다
                folder["label"] = rep["label"]
            folder["doc"], folder["target"] = rep["doc"], rep["target"]
            folder["badge"], folder["done"] = rep["badge"], rep["done"]
    folder["children"] = docs + folders


def _match(path, groups):
    """문서 경로에 가장 길게 맞는 (묶음 번호, 경로 항목)을 돌려준다. 없으면 None."""
    best = None
    for gi, g in enumerate(groups):
        for entry in g.get("paths", []):
            entry = entry.strip("/")
            if entry and (path == entry or path.startswith(entry + "/")):
                if best is None or len(entry) > len(best[1]):
                    best = (gi, entry)
    return best


def build_nav(status, config):
    """config["sidebar"](없으면 DEFAULT_SIDEBAR) 묶음대로 문서를 트리로 묶는다. 비어 있는 묶음은 뺀다."""
    groups = config.get("sidebar") or DEFAULT_SIDEBAR
    decisions = {d["file"]: d for d in status["decisions"]}
    buckets = [[] for _ in groups]
    other = []
    for d in status["docs"]:
        hit = _match(d["path"], groups)
        if hit is None:
            other.append(("", d))
        else:
            buckets[hit[0]].append((hit[1], d))
    nav = []
    for gi, g in enumerate(groups):
        if not buckets[gi]:
            continue
        folder_entries = [p.strip("/") for p in g.get("paths", []) if not p.endswith(".md")]
        merge = len(folder_entries) <= 1
        basenames = [os.path.basename(e) for e in folder_entries]
        root = _node(g["name"])
        for entry, d in buckets[gi]:
            if entry == d["path"]:
                _insert(root, [os.path.basename(d["path"])], d, decisions)
                continue
            parts = d["path"][len(entry) + 1:].split("/")
            if merge:
                _insert(root, parts, d, decisions)
                continue
            base = os.path.basename(entry)  # 폴더 경로가 여럿이면 폴더마다 항목. 끝 이름이 겹치면 전체 경로를 이름표로
            label = FOLDER_LABELS.get(base, base if basenames.count(base) == 1 else entry)
            child = next((c for c in root["children"] if c["key"] == entry), None)
            if child is None:
                child = _node(label, key=entry)
                root["children"].append(child)
            _insert(child, parts, d, decisions)
        _finalize(root, True)
        nav.append(root)
    if other:
        root = _node(OTHER_GROUP)
        for _entry, d in other:
            _insert(root, d["path"].split("/"), d, decisions)
        _finalize(root, True)
        nav.append(root)
    return nav


def _contains(node, current):
    if current is None:
        return False
    if node["target"] == current:
        return True
    return any(_contains(c, current) for c in node["children"])


def _label_html(node, page_dir, current):
    cls = ' class="current"' if node["target"] and node["target"] == current else ""
    badge = f' <span class="badge warn">{esc(node["badge"])}</span>' if node["badge"] else ""
    if node["target"]:
        return f'<a{cls} href="{href_from(page_dir, node["target"], node["anchor"])}"><span class="lbl">{esc(node["label"])}</span>{badge}</a>'
    return f'<span><span class="lbl">{esc(node["label"])}</span>{badge}</span>'


def render_node(node, page_dir, current, level):
    if not node["children"]:
        done = " done" if node["done"] else ""
        return f'<li class="nav-l{level}{done}">{_label_html(node, page_dir, current)}</li>'
    open_it = (level == 1) or _contains(node, current)
    cls = ' class="current"' if node["target"] and node["target"] == current else ""
    summary = f'<summary{cls}>{_label_html(node, page_dir, current)}{ICON_CHEV}</summary>'
    inner = "\n".join(render_node(c, page_dir, current, level + 1) for c in node["children"])
    details = f'<details class="nav-l{level}"{" open" if open_it else ""}>{summary}\n<ul>\n{inner}\n</ul></details>'
    return details if level == 1 else f"<li>{details}</li>"


def render_sidebar(nav, page_dir, current):
    home = ' class="current"' if current is None else ""
    log = ' class="current"' if current == "changelog.html" else ""
    parts = ['<div class="nav-top">',
             f'<a{home} href="{href_from(page_dir, "index.html")}">{ICON_HOME}<span class="lbl">대시보드</span></a>',
             f'<a{log} href="{href_from(page_dir, "changelog.html")}">{ICON_LOG}<span class="lbl">변경 이력</span></a>',
             "</div>"]
    parts.extend(render_node(g, page_dir, current, 1) for g in nav)
    return "\n".join(parts)


# ---------------------------------------------------------------- 페이지

def page(status, title, body, headings, page_dir, sidebar_html, prefix):
    return FRAME.format(title=esc(title), project=esc(status["project"]), prefix=prefix, sidebar=sidebar_html,
                        body=body, toc=toc_html(headings), generated=esc(status["generated"]),
                        prefix_json=json.dumps(prefix))


def _todo_card(t, doc_paths):
    total = len(t["subtasks"])
    done = sum(1 for s in t["subtasks"] if s["done"])
    pct = int(done * 100 / total) if total else 0
    doc = find_detail_doc(t["detail"], doc_paths)
    tag = "a" if doc else "div"
    href = f' href="{href_from("", html_path(doc))}"' if doc else ""
    desc = t["notes"][0] if t["notes"] else (t["subtasks"][0]["title"] if t["subtasks"] else "")
    desc_html = f'<div class="card-desc">{esc(desc)}</div>' if desc else ""
    if total:
        foot = (f'<div class="card-foot"><div class="progress"><div class="bar" style="width:{pct}%"></div></div>'
                f'<span>{done}/{total} 단계</span><span class="pill">{pct}%</span></div>')
    else:
        foot = '<div class="card-foot"><span>하위 단계 없음</span></div>'
    return f'<{tag} class="card"{href}><div class="card-title">{esc(t["title"])}</div>{desc_html}{foot}</{tag}>'


def _done_card(e):
    desc = e["summary"] or (e["details"][0] if e.get("details") else "")
    return (f'<div class="card"><div class="card-title">{esc(e["title"])}</div><div class="card-desc">{esc(desc)}</div>'
            f'<div class="card-foot"><span class="ok">{ICON_CHECK} 완료 {esc(e["date"])}</span></div></div>')


def _column(cls, icon, label, cards, empty):
    body = "\n".join(cards) if cards else f'<div class="empty">{esc(empty)}</div>'
    return (f'<div class="col {cls}"><div class="col-head">{icon}<span>{esc(label)}</span><span class="count">({len(cards)})</span></div>'
            f'{body}</div>')


def index_body(status, doc_paths):
    out = [f"<h1 id=\"대시보드\">{esc(status['project'])} 대시보드</h1>",
           '<p class="lead">계획, 진행 중, 완료를 한눈에. 카드를 누르면 그 작업의 문서로 간다.</p>',
           '<h2 id="작업-보드">작업 보드</h2>']
    open_items = [t for t in status["todo"] if not t["done"]]
    doing = [t for t in open_items if any(s["done"] for s in t["subtasks"]) or t["notes"]]
    planned = [t for t in open_items if t not in doing]
    out.append('<div class="board">')
    out.append(_column("col-planned", ICON_PLANNED, "계획", [_todo_card(t, doc_paths) for t in planned], "계획한 작업 없음"))
    out.append(_column("col-doing", ICON_DOING, "진행 중", [_todo_card(t, doc_paths) for t in doing], "진행 중인 작업 없음"))
    out.append(_column("col-done", ICON_DONE, "완료", [_done_card(e) for e in status["done"][:8]], "완료한 작업 없음"))
    out.append("</div>")
    if not open_items:
        out.append("<p>진행 중인 작업 없음</p>")
    out.append('<h2 id="결정-대기">결정 대기</h2>')
    pending = [d for d in status["decisions"] if any(not q["answered"] for q in d["questions"])]
    if not pending:
        out.append("<p>답을 기다리는 물음 없음</p>")
    else:
        for d in pending:
            n = sum(1 for q in d["questions"] if not q["answered"])
            titles = ", ".join(q["title"] for q in d["questions"] if not q["answered"])
            out.append(f'<div class="review"><div class="vote">{n}<small>물음</small></div><div>'
                       f'<a class="review-title" href="{href_from("", html_path(d["file"]))}">{esc(d["title"])}</a>'
                       f'<div class="card-meta">미답 {n}건 / 전체 {len(d["questions"])}건: {esc(titles)}</div></div></div>')
    out.append('<h2 id="아이디어-현황">아이디어 현황</h2>')
    if not status["ideas"]:
        out.append("<p>현황표 없음</p>")
    else:
        out.append("<table><thead><tr><th>#</th><th>제목</th><th>출처</th><th>상태</th><th>디렉토리</th></tr></thead><tbody>")
        for i in status["ideas"]:
            out.append(f"<tr><td>{esc(i['no'])}</td><td>{esc(i['title'])}</td><td>{esc(i['source'])}</td>"
                       f"<td>{esc(i['status'])}</td><td><code>{esc(i['dir'])}</code></td></tr>")
        out.append("</tbody></table>")
    out.append('<h2 id="최근-실험">최근 실험</h2>')
    if not status["experiments"]:
        out.append("<p>실험로그 없음</p>")
    else:
        out.append("<ul>")
        for e in status["experiments"][:5]:  # 실험로그는 최신이 위
            if e["file"] in doc_paths:
                label = f'<a href="{href_from("", html_path(e["file"]), md_to_html.slug(e["title"]))}">{esc(e["title"])}</a>'
            else:
                label = esc(e["title"])
            out.append(f'<li>{label} <span class="snippet">({esc(e["file"])})</span></li>')
        out.append("</ul>")
    out.append('<h2 id="문서-지도">문서 지도</h2>')
    if not status["docs"]:
        out.append("<p>문서 없음</p>")
    else:
        out.append("<table><thead><tr><th>문서</th><th>태그</th><th>들어오는 링크</th><th>나가는 링크</th></tr></thead><tbody>")
        for d in status["docs"]:
            orphan = ' <span class="orphan">(고아)</span>' if not d["links_in"] else ""
            out.append(f'<tr><td><a href="{href_from("", html_path(d["path"]))}">{esc(d["title"])}</a>'
                       f'<br><code>{esc(d["path"])}</code></td><td>{esc(", ".join(d["tags"]))}</td>'
                       f'<td>{len(d["links_in"])}{orphan}</td><td>{len(d["links_out"])}</td></tr>')
        out.append("</tbody></table>")
    return "\n".join(out)


INDEX_HEADINGS = [(2, "작업 보드", "작업-보드"), (2, "결정 대기", "결정-대기"), (2, "아이디어 현황", "아이디어-현황"),
                  (2, "최근 실험", "최근-실험"), (2, "문서 지도", "문서-지도")]


def _inline_strong(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(text))


def changelog_body(status):
    entries = status["done"]
    out = ['<h1 id="변경-이력">변경 이력</h1>',
           '<p class="lead">완료한 작업 단위로 본다 (커밋 단위가 아니다). 기간을 고르면 그 사이의 변경만 보인다.</p>']
    if not entries:
        out.append("<p>완료한 작업 없음</p>")
        return "\n".join(out), []
    dates = sorted({e["date"] for e in entries})
    months = sorted({e["date"][:7] for e in entries}, reverse=True)
    numbers = {}
    for k, e in enumerate(reversed(entries), start=1):  # 오래된 것이 1번
        numbers[id(e)] = k
    out.append('<div class="range"><div><label for="range-from">from</label><select id="range-from">'
               + "".join(f'<option value="{esc(d)}"{" selected" if i == 0 else ""}>{esc(d)}</option>' for i, d in enumerate(dates))
               + '</select></div><div><label for="range-to">to</label><select id="range-to">'
               + "".join(f'<option value="{esc(d)}"{" selected" if i == len(dates) - 1 else ""}>{esc(d)}</option>' for i, d in enumerate(dates))
               + "</select></div></div>")
    tabs = [f'<button type="button" class="tab active" data-month="">전체 <span class="count">{len(entries)}</span></button>']
    for m in months:
        n = sum(1 for e in entries if e["date"].startswith(m))
        tabs.append(f'<button type="button" class="tab" data-month="{esc(m)}">{esc(m)} <span class="count">{n}</span></button>')
    out.append('<div class="tabs">' + "".join(tabs) + "</div>")
    headings = []
    for d in sorted(dates, reverse=True):
        hid = "d-" + d
        headings.append((2, d, hid))
        out.append(f'<h2 class="ver" id="{hid}" data-date="{esc(d)}">{esc(d)}</h2>')
        out.append(f'<div class="changes" data-date="{esc(d)}">')
        for e in [x for x in entries if x["date"] == d]:
            details = "".join(f"<li>{_inline_strong(line)}</li>" for line in e.get("details", []))
            out.append(f'<article class="change" data-date="{esc(d)}" data-month="{esc(d[:7])}">'
                       f'<div class="change-head"><span class="badge tag">완료</span><span>#{numbers[id(e)]}</span></div>'
                       f'<div class="change-title">{esc(e["title"])}</div>'
                       + (f'<p>{esc(e["summary"])}</p>' if e["summary"] else "")
                       + (f"<ul>{details}</ul>" if details else "") + "</article>")
        out.append("</div>")
    return "\n".join(out), headings


def make_rewrite(root, doc_path, doc_paths):
    doc_dir = os.path.dirname(doc_path)

    def rewrite(href):
        if re.match(r"[a-z]+:", href) or href.startswith("#"):
            return href
        base, _sep, anchor = href.partition("#")
        target = unquote(base)
        if not target.endswith(".md"):
            full = os.path.normpath(os.path.join(doc_dir, target)).replace(os.sep, "/")
            if full.startswith("./"):
                full = full[2:]
            if not os.path.exists(os.path.join(root, full)):
                return href
            page_dir_root = "dashboard/docs/" + doc_dir if doc_dir else "dashboard/docs"
            rel_path = os.path.relpath(full, page_dir_root).replace(os.sep, "/")
            return quote(rel_path, safe="/") + (f"#{anchor}" if anchor else "")
        full = os.path.normpath(os.path.join(doc_dir, target)).replace(os.sep, "/")
        if full.startswith("./"):
            full = full[2:]
        if full not in doc_paths:
            return href
        return href_from("docs/" + doc_dir if doc_dir else "docs", html_path(full), anchor)

    return rewrite


def plain_text(body):
    text = re.sub(r"```.*?```", " ", body, flags=re.S)
    text = re.sub(r"[#*`>|\[\]()-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def render(root, status, config=None):
    root = os.path.abspath(root)
    config = config or collect_status.load_config(root)
    out_dir = os.path.join(root, OUT)
    shutil.rmtree(os.path.join(out_dir, "docs"), ignore_errors=True)  # 지워지거나 옮긴 md의 옛 html을 남기지 않는다
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    written = []
    doc_paths = {d["path"] for d in status["docs"]}
    nav = build_nav(status, config)
    index = page(status, f"{status['project']} 대시보드", index_body(status, doc_paths), INDEX_HEADINGS, "",
                 render_sidebar(nav, "", None), "")
    written.append(_write(os.path.join(out_dir, "index.html"), index))
    log_body, log_headings = changelog_body(status)
    changelog = page(status, f"{status['project']} 변경 이력", log_body, log_headings, "",
                     render_sidebar(nav, "", "changelog.html"), "")
    written.append(_write(os.path.join(out_dir, "changelog.html"), changelog))
    search_index = []
    for d in status["docs"]:
        text = collect_status.read_text(os.path.join(root, d["path"]))
        _meta, body = md_to_html.parse_frontmatter(text)
        target = html_path(d["path"])
        page_dir = os.path.dirname(target)
        depth = target.count("/")
        prefix = "../" * depth
        body_html = md_to_html.md_to_html(body, make_rewrite(root, d["path"], doc_paths))
        headings = md_to_html.extract_headings(body)
        html = page(status, d["title"], body_html, headings, page_dir, render_sidebar(nav, page_dir, target), prefix)
        written.append(_write(os.path.join(out_dir, target), html))
        search_index.append({"title": d["title"], "path": quote(target, safe="/"), "text": plain_text(body)[:2000]})
    written.append(_write(os.path.join(out_dir, "assets", "style.css"), STYLE))
    written.append(_write(os.path.join(out_dir, "assets", "app.js"), APP_JS))
    written.append(_write(os.path.join(out_dir, "assets", "search.js"),
                          "window.DASH_INDEX = " + json.dumps(search_index, ensure_ascii=False) + ";\n"))
    return written


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return path


def check_links(root):
    """dashboard/ 안 html의 상대 href와 src가 가리키는 파일이 없는 것을 (html 경로, href)로 돌려준다."""
    root = os.path.abspath(root)
    out_dir = os.path.join(root, OUT)
    broken = []
    for r, _dirs, files in os.walk(out_dir):
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            path = os.path.join(r, name)
            for href in HREF.findall(collect_status.read_text(path)):
                if re.match(r"[a-z]+:", href) or href.startswith("#"):
                    continue
                target = unquote(href.split("#")[0])
                if target and not os.path.exists(os.path.normpath(os.path.join(r, target))):
                    broken.append((collect_status.rel(root, path), href))
    return broken


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = os.path.abspath(argv[0]) if argv else os.getcwd()
    collect_status.main([root])
    with io.open(os.path.join(root, OUT, "status.json"), encoding="utf-8") as f:
        status = json.load(f)
    written = render(root, status)
    broken = check_links(root)
    print(f"대시보드: 파일 {len(written)}개 ({os.path.join(root, OUT, 'index.html')})")
    for path, href in broken:
        print(f"깨진 링크: {path} -> {href}")
    print(f"깨진 링크 {len(broken)}건")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
