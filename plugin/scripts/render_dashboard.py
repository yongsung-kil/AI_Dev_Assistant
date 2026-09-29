"""status.json과 md 문서로 정적 대시보드(dashboard/)를 만든다.

사용: python render_dashboard.py [프로젝트 폴더]
산출: dashboard/index.html, dashboard/docs/{md 경로}.html, dashboard/assets/{style.css, app.js, search.js}, dashboard/status.json
규격: docs/html_guide.md (왼쪽 사이드바 접기, 위 검색, 오른쪽 "이 페이지의 차례", 상대 링크만, 외부 자원 없음).
렌더 뒤 상대 링크가 가리키는 파일이 없으면 보고하고 종료 코드 1.
"""
import html as htmllib
import io
import json
import os
import re
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

STYLE = """:root {
  --bg: #ffffff; --surface: #f6f8fa; --text: #24292f; --muted: #57606a; --border: #d0d7de;
  --accent: #0969da; --ok: #1a7f37; --warn: #bf8700;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0d1117; --surface: #161b22; --text: #e6edf3; --muted: #8b949e; --border: #30363d;
          --accent: #58a6ff; --ok: #3fb950; --warn: #d29922; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font-size: 16px; line-height: 1.7; word-break: keep-all; overflow-wrap: anywhere;
       font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: Consolas, "D2Coding", monospace; font-size: 0.9em; background: var(--surface); padding: 0.15em 0.4em; border-radius: 4px; }
pre { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 12px 16px; overflow-x: auto; }
pre code { background: none; padding: 0; }
.top { position: sticky; top: 0; z-index: 5; display: flex; gap: 16px; align-items: center; padding: 10px 16px;
       background: var(--surface); border-bottom: 1px solid var(--border); }
.brand { font-weight: 600; white-space: nowrap; }
#search { flex: 1; max-width: 520px; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px;
          background: var(--bg); color: var(--text); font-size: 15px; }
#search-results { position: absolute; top: 48px; left: 16px; right: 16px; max-width: 720px; background: var(--bg);
                  border: 1px solid var(--border); border-radius: 6px; box-shadow: 0 6px 24px rgba(0,0,0,.15); padding: 6px; }
#search-results a { display: block; padding: 6px 8px; border-radius: 4px; }
#search-results a:hover { background: var(--surface); text-decoration: none; }
#search-results .snippet { color: var(--muted); font-size: 0.85em; }
.layout { display: grid; grid-template-columns: 260px minmax(0, 880px) 220px; gap: 24px; padding: 16px; }
.sidebar { position: sticky; top: 56px; align-self: start; max-height: calc(100vh - 72px); overflow-y: auto; font-size: 0.95em; }
.sidebar details { margin: 4px 0; }
.sidebar summary { cursor: pointer; font-weight: 600; padding: 4px 0; }
.sidebar ul { list-style: none; margin: 0 0 4px 0; padding-left: 12px; }
.sidebar li { margin: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sidebar a.current { font-weight: 600; color: var(--text); }
.sidebar .nav-home { display: block; font-weight: 600; margin-bottom: 8px; }
.sidebar .done { color: var(--muted); }
.content { min-width: 0; }
.content h1 { font-size: 1.9em; border-bottom: 2px solid var(--border); padding-bottom: 0.3em; margin-top: 0.4em; }
.content h2 { font-size: 1.45em; border-bottom: 1px solid var(--border); padding-bottom: 0.25em; margin-top: 1.6em; }
.content h3 { font-size: 1.15em; }
.content table { border-collapse: collapse; margin: 1em 0; display: block; overflow-x: auto; }
.content th, .content td { border: 1px solid var(--border); padding: 6px 12px; text-align: left; vertical-align: top; }
.content th { background: var(--surface); }
.content tr:nth-child(even) td { background: var(--surface); }
.content blockquote { margin: 0.8em 0; padding: 0.4em 1em; border-left: 4px solid var(--border); color: var(--muted); background: var(--surface); }
.toc { position: sticky; top: 56px; align-self: start; font-size: 0.9em; color: var(--muted); }
.toc-title { font-weight: 600; margin-bottom: 6px; }
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc li.h3 { padding-left: 12px; }
.toc a { color: var(--muted); }
.toc a.active { color: var(--accent); font-weight: 600; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { display: block; border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: var(--surface); color: var(--text); }
a.card:hover { border-color: var(--accent); text-decoration: none; }
.card-title { font-weight: 600; margin-bottom: 6px; }
.progress { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress .bar { height: 100%; background: var(--ok); }
.card-meta { color: var(--muted); font-size: 0.85em; margin-top: 4px; }
.card-notes { color: var(--muted); font-size: 0.85em; margin-top: 6px; }
.badge { display: inline-block; padding: 0 8px; border-radius: 10px; font-size: 0.8em; color: #fff; }
.badge.warn { background: var(--warn); } .badge.ok { background: var(--ok); }
.orphan { color: var(--warn); }
.foot { color: var(--muted); font-size: 0.85em; padding: 16px; border-top: 1px solid var(--border); }
@media (max-width: 1100px) { .layout { grid-template-columns: 240px minmax(0, 1fr); } .toc { display: none; } }
@media (max-width: 700px) { .layout { grid-template-columns: 1fr; } .sidebar { position: static; max-height: none; } }
"""

APP_JS = """(function () {
  var prefix = window.DASH_PREFIX || "";
  var input = document.getElementById("search");
  var box = document.getElementById("search-results");
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
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
  }
  var here = decodeURIComponent(location.pathname.split("/").slice(-1)[0]);
  var links = document.querySelectorAll(".sidebar a");
  for (var j = 0; j < links.length; j++) {
    var h = decodeURIComponent(links[j].getAttribute("href") || "").split("#")[0].split("/").slice(-1)[0];
    if (h && h === here && links[j].className.indexOf("nav-home") < 0) {
      links[j].classList.add("current");
      var det = links[j].closest("details"); while (det) { det.open = true; det = det.parentElement.closest("details"); }
    }
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
})();
"""

FRAME = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="top">
<a class="brand" href="{prefix}index.html">{project}</a>
<input id="search" type="search" placeholder="검색 (제목과 본문)" autocomplete="off">
<div id="search-results" hidden></div>
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
"""


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


def build_groups(status):
    """사이드바 장. 항목은 (label, target dashboard 경로 또는 None, anchor, done)."""
    doc_paths = {d["path"] for d in status["docs"]}
    groups = []
    todo_items = []
    for t in status["todo"]:
        doc = find_detail_doc(t["detail"], doc_paths)
        todo_items.append((t["title"], html_path(doc) if doc else None, "", t["done"]))
    groups.append(("작업", todo_items, []))
    groups.append(("결정", [(d["title"], html_path(d["file"]), "", all(q["answered"] for q in d["questions"]))
                            for d in status["decisions"]], []))
    groups.append(("아이디어", [(f"{i['no']}. {i['title']} ({i['status']})", None, "", False) for i in status["ideas"]], []))
    groups.append(("실험", [(e["title"], html_path(e["file"]), md_to_html.slug(e["title"]), False) for e in status["experiments"]], []))
    by_folder = {}
    for d in status["docs"]:
        top = d["path"].split("/")[0] if "/" in d["path"] else "루트"
        by_folder.setdefault(top, []).append((d["title"], html_path(d["path"]), "", False))
    children = [(name, items, []) for name, items in sorted(by_folder.items(), key=lambda kv: (kv[0] != "루트", kv[0]))]
    groups.append(("문서", [], children))
    return groups


def render_group(name, items, children, page_dir, current, open_it):
    lines = [f'<details{" open" if open_it else ""}><summary>{esc(name)}</summary>']
    if items:
        lines.append("<ul>")
        for label, target, anchor, done in items:
            cls = ' class="done"' if done else ""
            if target:
                lines.append(f'<li{cls}><a href="{href_from(page_dir, target, anchor)}">{esc(label)}</a></li>')
            else:
                lines.append(f"<li{cls}>{esc(label)}</li>")
        lines.append("</ul>")
    for child in children:
        lines.append(render_group(child[0], child[1], child[2], page_dir, current, current and any(t == current for _l, t, _a, _d in child[1])))
    lines.append("</details>")
    return "\n".join(lines)


def render_sidebar(groups, page_dir, current):
    parts = [f'<a class="nav-home" href="{href_from(page_dir, "index.html")}">대시보드</a>']
    for i, (name, items, children) in enumerate(groups):
        contains = any(t == current for _l, t, _a, _d in items) or any(
            t == current for c in children for _l, t, _a, _d in c[1])
        parts.append(render_group(name, items, children, page_dir, current, contains or (current is None and i == 0)))
    return "\n".join(parts)


def page(status, title, body, headings, page_dir, sidebar_html, prefix):
    return FRAME.format(title=esc(title), project=esc(status["project"]), prefix=prefix, sidebar=sidebar_html,
                        body=body, toc=toc_html(headings), generated=esc(status["generated"]),
                        prefix_json=json.dumps(prefix))


def index_body(status, doc_paths):
    out = [f"<h1 id=\"대시보드\">{esc(status['project'])} 대시보드</h1>"]
    out.append('<h2 id="진행-중">진행 중</h2>')
    open_items = [t for t in status["todo"] if not t["done"]]
    if not open_items:
        out.append("<p>진행 중인 작업 없음</p>")
    else:
        out.append('<div class="cards">')
        for t in open_items:
            total = len(t["subtasks"])
            done = sum(1 for s in t["subtasks"] if s["done"])
            pct = int(done * 100 / total) if total else 0
            doc = find_detail_doc(t["detail"], doc_paths)
            tag = "a" if doc else "div"
            href = f' href="{href_from("", html_path(doc))}"' if doc else ""
            notes = " ".join(t["notes"][:2])
            out.append(f'<{tag} class="card"{href}><div class="card-title">{esc(t["title"])}</div>'
                       f'<div class="progress"><div class="bar" style="width:{pct}%"></div></div>'
                       f'<div class="card-meta">{done}/{total} 단계</div>'
                       + (f'<div class="card-notes">{esc(notes)}</div>' if notes else "") + f"</{tag}>")
        out.append("</div>")
    out.append('<h2 id="결정-대기">결정 대기</h2>')
    pending = [d for d in status["decisions"] if any(not q["answered"] for q in d["questions"])]
    if not pending:
        out.append("<p>답을 기다리는 물음 없음</p>")
    else:
        out.append("<ul>")
        for d in pending:
            n = sum(1 for q in d["questions"] if not q["answered"])
            out.append(f'<li><a href="{href_from("", html_path(d["file"]))}">{esc(d["title"])}</a> '
                       f'<span class="badge warn">미답 {n}건</span> / 전체 {len(d["questions"])}건</li>')
        out.append("</ul>")
    out.append('<h2 id="최근-완료">최근 완료</h2>')
    if not status["done"]:
        out.append("<p>없음</p>")
    else:
        out.append("<table><thead><tr><th>날짜</th><th>작업</th><th>요약</th></tr></thead><tbody>")
        for e in status["done"][:5]:
            out.append(f"<tr><td>{esc(e['date'])}</td><td>{esc(e['title'])}</td><td>{esc(e['summary'])}</td></tr>")
        out.append("</tbody></table>")
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
        for e in status["experiments"][-5:][::-1]:
            out.append(f'<li><a href="{href_from("", html_path(e["file"]), md_to_html.slug(e["title"]))}">{esc(e["title"])}</a> '
                       f'<span class="snippet">({esc(e["file"])})</span></li>')
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


def make_rewrite(doc_path, doc_paths):
    doc_dir = os.path.dirname(doc_path)

    def rewrite(href):
        if re.match(r"[a-z]+:", href) or href.startswith("#"):
            return href
        base, _sep, anchor = href.partition("#")
        target = unquote(base)
        if not target.endswith(".md"):
            return href
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


def render(root, status):
    root = os.path.abspath(root)
    out_dir = os.path.join(root, OUT)
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    written = []
    doc_paths = {d["path"] for d in status["docs"]}
    groups = build_groups(status)
    index_headings = [(2, "진행 중", "진행-중"), (2, "결정 대기", "결정-대기"), (2, "최근 완료", "최근-완료"),
                      (2, "아이디어 현황", "아이디어-현황"), (2, "최근 실험", "최근-실험"), (2, "문서 지도", "문서-지도")]
    index = page(status, f"{status['project']} 대시보드", index_body(status, doc_paths), index_headings, "",
                 render_sidebar(groups, "", None), "")
    written.append(_write(os.path.join(out_dir, "index.html"), index))
    search_index = []
    for d in status["docs"]:
        text = collect_status.read_text(os.path.join(root, d["path"]))
        _meta, body = md_to_html.parse_frontmatter(text)
        target = html_path(d["path"])
        page_dir = os.path.dirname(target)
        depth = target.count("/")
        prefix = "../" * depth
        body_html = md_to_html.md_to_html(body, make_rewrite(d["path"], doc_paths))
        headings = md_to_html.extract_headings(body)
        html = page(status, d["title"], body_html, headings, page_dir, render_sidebar(groups, page_dir, target), prefix)
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
                if target and not os.path.isfile(os.path.normpath(os.path.join(r, target))):
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
