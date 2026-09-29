import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import md_to_html as m  # noqa: E402


def test_frontmatter_parsed_and_removed():
    meta, body = m.parse_frontmatter("---\ntitle: 개요\ntags: [a, b]\n---\n# 제목\n")
    assert meta == {"title": "개요", "tags": ["a", "b"]}
    assert body.startswith("# 제목")
    assert m.parse_frontmatter("# 그냥\n") == ({}, "# 그냥\n")


def test_headings_get_ids_and_toc():
    body = "## 첫 절\n본문\n### 둘째 절\n"
    html = m.md_to_html(body)
    assert '<h2 id="첫-절">첫 절</h2>' in html and '<h3 id="둘째-절">둘째 절</h3>' in html
    assert m.extract_headings(body) == [(2, "첫 절", "첫-절"), (3, "둘째 절", "둘째-절")]


def test_fenced_code_is_escaped_and_not_parsed():
    html = m.md_to_html("```\na < b & **c**\n```\n")
    assert "<pre><code>a &lt; b &amp; **c**</code></pre>" in html
    html2 = m.md_to_html("~~~\n# 제목 아님\n~~~\n")
    assert "<h1" not in html2 and "# 제목 아님" in html2


def test_table_keeps_br_and_inline_code():
    html = m.md_to_html("| 열1 | 열2 |\n|---|---|\n| 가<br>나 | `x` |\n")
    assert "<table>" in html and "<th>열1</th>" in html
    assert "가<br>나" in html and "<code>x</code>" in html


def test_lists_nested_and_checkboxes():
    html = m.md_to_html("- a\n  - b\n- [x] c\n- [ ] d\n")
    flat = html.replace("\n", "")
    assert flat.count("<ul>") == 2 and "<li>a<ul><li>b</li></ul></li>" in flat
    assert "☑ c" in flat and "☐ d" in flat


def test_links_rewritten_only_for_md():
    html = m.md_to_html("[a](b.md) [c](https://x.y)\n",
                        link_rewrite=lambda h: h[:-3] + ".html" if h.endswith(".md") else h)
    assert 'href="b.html"' in html and 'href="https://x.y"' in html


def test_paragraph_and_inline_marks():
    html = m.md_to_html("굵게 **a** 코드 `b` 기울임 *c*\n")
    assert "<p>굵게 <strong>a</strong> 코드 <code>b</code> 기울임 <em>c</em></p>" in html


def test_blockquote_and_rule():
    html = m.md_to_html("> 인용\n\n---\n")
    assert "<blockquote>" in html and "<hr>" in html
