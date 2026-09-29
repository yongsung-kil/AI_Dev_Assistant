import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts"))
import paper_search  # noqa: E402
import papers_db  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "plugin", "scripts", "paper_search.py")
ATOM = ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
        '<entry><id>http://arxiv.org/abs/2301.00001v2</id><title>Title\n  One</title><summary> Abstract one </summary>'
        '<published>2023-01-05T00:00:00Z</published>'
        '<link title="pdf" href="http://arxiv.org/pdf/2301.00001v2" rel="related" type="application/pdf"/>'
        '<arxiv:journal_ref>J. X</arxiv:journal_ref></entry>'
        '<entry><id>http://arxiv.org/abs/2405.11111v1</id><title>Two</title><summary>B</summary>'
        '<published>2024-05-01T00:00:00Z</published></entry></feed>')
IEEE_CSV = ('"Document Title","Authors","Publication Title","Publication Year","Abstract","DOI","PDF Link"\n'
            '"Low Power Decoder","A; B","IEEE Trans. X","2024","We propose ...","10.1109/X.2024.1","https://ieeexplore.ieee.org/stamp/1"\n')
PATENT_CSV = ('id,title,assignee,inventor/author,priority date,filing/creation date,publication date,grant date,result link\n'
              'US-1234-B2,Error correction apparatus,Corp,Kim,2020-01-01,2020-06-01,2022-03-10,2022-03-10,https://patents.google.com/patent/US1234B2/en\n')


def test_parse_arxiv_atom_fixture():
    rows = paper_search.parse_arxiv_atom(ATOM)
    assert [r["id"] for r in rows] == ["arxiv:2301.00001", "arxiv:2405.11111"]
    first = rows[0]
    assert first["title"] == "Title One" and first["abstract"] == "Abstract one" and first["year"] == 2023
    assert first["pdf_url"] == "http://arxiv.org/pdf/2301.00001v2" and first["venue"] == "J. X"
    assert first["url"] == "http://arxiv.org/abs/2301.00001v2" and first["source"] == "arxiv"


def test_import_ieee_csv_column_names_normalized(tmp_path):
    p = tmp_path / "ieee.csv"
    p.write_text(IEEE_CSV, encoding="utf-8-sig")
    rows = paper_search.import_csv(str(p), "ieee")
    assert len(rows) == 1
    r = rows[0]
    assert r["title"] == "Low Power Decoder" and r["year"] == 2024 and r["doi"] == "10.1109/X.2024.1"
    assert r["venue"] == "IEEE Trans. X" and r["pdf_url"].startswith("https://") and r["abstract"].startswith("We propose")
    assert papers_db.make_id(r) == "doi:10.1109/X.2024.1"


def test_import_patent_csv_without_abstract(tmp_path):
    p = tmp_path / "patents.csv"
    p.write_text(PATENT_CSV, encoding="utf-8")
    rows = paper_search.import_csv(str(p), "patent")
    assert rows[0]["title"] == "Error correction apparatus" and rows[0]["year"] == 2022
    assert rows[0]["abstract"] == "" and rows[0]["url"].startswith("https://patents.google.com")
    assert papers_db.make_id(rows[0]) == "patent:US-1234-B2"


def test_cli_init_import_stats(tmp_path):
    (tmp_path / "ieee.csv").write_text(IEEE_CSV, encoding="utf-8-sig")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env["PYTHONUTF8"] = "0"
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(tmp_path), "init"], capture_output=True, env=env)
    assert r.returncode == 0 and (tmp_path / "papers" / "README.md").is_file()
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(tmp_path), "import", str(tmp_path / "ieee.csv"),
                        "--source", "ieee"], capture_output=True, env=env)
    assert r.returncode == 0 and "들여옴 1" in r.stdout.decode("utf-8")
    r = subprocess.run([sys.executable, SCRIPT, "--root", str(tmp_path), "stats"], capture_output=True, env=env)
    assert "전체 1" in r.stdout.decode("utf-8")
