"""표준 라이브러리만 쓰는 작은 md 변환기.

지원: 머리말(---), 제목(#부터 ####), 문단, 목록(-, *, 1. 들여쓰기 2칸 중첩, [ ]와 [x] 상자), 표(|),
코드 울타리(백틱과 물결표 3개 이상), 인라인 코드, **굵게**, *기울임*, 링크 [t](u), > 인용, --- 가로줄, <br>.
링크의 href는 link_rewrite 함수로 바꿀 수 있다 (예: .md를 .html로).
"""
import html as htmllib
import re

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?(\s*:?-{3,}:?\s*\|)*\s*:?-{3,}:?\s*\|?\s*$")
INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*([^*]+?)\*(?![*\w])")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def parse_frontmatter(text):
    """맨 앞 --- 사이의 key: value를 dict로. [a, b] 꼴은 목록으로. 머리말이 없으면 ({}, 원문)."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        return {}, text
    meta = {}
    for i in range(1, len(lines)):
        line = lines[i].rstrip("\r\n")
        if line.strip() == "---":
            return meta, "".join(lines[i + 1:])
        if ":" in line:
            key, value = line.split(":", 1)
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            meta[key.strip()] = value
    return {}, text


def slug(text):
    """제목을 id로. 한글은 그대로, 공백은 붙임표, 그 밖의 기호는 뺀다."""
    cleaned = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"\s+", "-", cleaned)


def _marks(segment, link_rewrite):
    s = htmllib.escape(segment, quote=False)
    for raw in ("&lt;br&gt;", "&lt;br/&gt;", "&lt;br /&gt;"):
        s = s.replace(raw, "<br>")

    def link(m):
        href = m.group(2)
        if link_rewrite:
            href = link_rewrite(href)
        return f'<a href="{href.replace(chr(34), "&quot;")}">{m.group(1)}</a>'

    s = LINK.sub(link, s)
    s = BOLD.sub(r"<strong>\1</strong>", s)
    s = ITALIC.sub(r"<em>\1</em>", s)
    return s


def inline(text, link_rewrite=None):
    """인라인 코드를 먼저 떼어 두고 나머지에 링크, 굵게, 기울임을 적용한다."""
    out, pos = [], 0
    for m in INLINE_CODE.finditer(text):
        out.append(_marks(text[pos:m.start()], link_rewrite))
        out.append("<code>" + htmllib.escape(m.group(1), quote=False) + "</code>")
        pos = m.end()
    out.append(_marks(text[pos:], link_rewrite))
    return "".join(out)


def _split_row(line):
    cells = line.strip()
    if cells.startswith("|"):
        cells = cells[1:]
    if cells.endswith("|"):
        cells = cells[:-1]
    return [c.strip() for c in cells.split("|")]


def _render_table(header, rows, link_rewrite):
    head = "".join(f"<th>{inline(c, link_rewrite)}</th>" for c in header)
    body = "".join("<tr>" + "".join(f"<td>{inline(c, link_rewrite)}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _list_tree(items, start, indent):
    """(들여쓰기, 표시, 글) 목록을 트리로. 노드는 [표시, 글, 하위 리스트들]."""
    nodes, i = [], start
    while i < len(items):
        ind, marker, text = items[i]
        if ind < indent:
            break
        if ind > indent:
            children, i = _list_tree(items, i, ind)
            if not nodes:
                nodes.append(["-", "", []])
            nodes[-1][2].append(children)
            continue
        nodes.append([marker, text, []])
        i += 1
    return nodes, i


def _render_nodes(nodes, link_rewrite):
    tag = "ol" if nodes and nodes[0][0][0].isdigit() else "ul"
    parts = [f"<{tag}>"]
    for _marker, text, subs in nodes:
        if text.startswith("[ ] "):
            text = "☐ " + text[4:]
        elif text[:4].lower() == "[x] ":
            text = "☑ " + text[4:]
        parts.append("<li>" + inline(text, link_rewrite))
        for sub in subs:
            parts.append(_render_nodes(sub, link_rewrite))
        parts.append("</li>")
    parts.append(f"</{tag}>")
    return "".join(parts)


def _render_list(items, link_rewrite):
    nodes, _ = _list_tree(items, 0, items[0][0])
    return _render_nodes(nodes, link_rewrite)


def iter_blocks(lines):
    """줄 목록을 (종류, 내용) 블록으로. 종류: fence, heading, hr, quote, table, list, blank, text."""
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        fm = FENCE.match(line)
        if fm:
            marker = fm.group(1)
            i += 1
            code = []
            while i < n:
                cm = FENCE.match(lines[i])
                if cm and cm.group(1)[0] == marker[0] and len(cm.group(1)) >= len(marker):
                    break
                code.append(lines[i])
                i += 1
            i += 1
            yield "fence", "\n".join(code)
            continue
        if not line.strip():
            yield "blank", ""
            i += 1
            continue
        hm = HEADING.match(line)
        if hm:
            yield "heading", (len(hm.group(1)), hm.group(2).strip())
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            yield "hr", ""
            i += 1
            continue
        if line.lstrip().startswith(">"):
            quote = []
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(lines[i].lstrip()[1:].strip())
                i += 1
            yield "quote", "\n".join(quote)
            continue
        if line.lstrip().startswith("|") and i + 1 < n and TABLE_SEP.match(lines[i + 1]):
            header = _split_row(line)
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            yield "table", (header, rows)
            continue
        if LIST_ITEM.match(line):
            items = []
            while i < n:
                m2 = LIST_ITEM.match(lines[i])
                if not m2:
                    break
                items.append((len(m2.group(1).replace("\t", "    ")), m2.group(2), m2.group(3)))
                i += 1
            yield "list", items
            continue
        yield "text", line.strip()
        i += 1


def md_to_html(body, link_rewrite=None):
    out, para = [], []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para), link_rewrite) + "</p>")
            para.clear()

    for kind, content in iter_blocks(body.splitlines()):
        if kind == "text":
            para.append(content)
            continue
        flush()
        if kind == "fence":
            out.append("<pre><code>" + htmllib.escape(content, quote=False) + "</code></pre>")
        elif kind == "heading":
            level, text = content
            out.append(f'<h{level} id="{slug(text)}">{inline(text, link_rewrite)}</h{level}>')
        elif kind == "hr":
            out.append("<hr>")
        elif kind == "quote":
            out.append("<blockquote>" + md_to_html(content, link_rewrite).strip() + "</blockquote>")
        elif kind == "table":
            out.append(_render_table(content[0], content[1], link_rewrite))
        elif kind == "list":
            out.append(_render_list(content, link_rewrite))
    flush()
    return "\n".join(out) + "\n"


def extract_headings(body):
    """(수준, 글, id) 목록. 코드 울타리 안은 뺀다."""
    return [(c[0], c[1], slug(c[1])) for kind, c in iter_blocks(body.splitlines()) if kind == "heading"]
