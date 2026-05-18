#!/usr/bin/env python3
"""Convert DOCX files in the repository to readable Markdown.

This intentionally avoids heavyweight dependencies so it can run in GitHub Actions
without pip installs. It extracts paragraphs and tables from WordprocessingML.
"""
from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def qn(tag: str) -> str:
    prefix, local = tag.split(":", 1)
    return f"{{{NS[prefix]}}}{local}"


def text_from_node(node: ET.Element) -> str:
    parts: list[str] = []
    for elem in node.iter():
        if elem.tag == qn("w:t"):
            parts.append(elem.text or "")
        elif elem.tag == qn("w:tab"):
            parts.append("\t")
        elif elem.tag == qn("w:br"):
            parts.append("\n")
    return "".join(parts)


def paragraph_style(paragraph: ET.Element) -> str:
    ppr = paragraph.find("w:pPr", NS)
    if ppr is None:
        return ""
    pstyle = ppr.find("w:pStyle", NS)
    if pstyle is None:
        return ""
    return pstyle.attrib.get(qn("w:val"), "")


def is_bold_run(run: ET.Element) -> bool:
    rpr = run.find("w:rPr", NS)
    if rpr is None:
        return False
    return rpr.find("w:b", NS) is not None


def paragraph_markdown(paragraph: ET.Element) -> str:
    text = text_from_node(paragraph).strip()
    if not text:
        return ""
    style = paragraph_style(paragraph).lower()
    m = re.search(r"heading(\d+)|标题\s*(\d+)", style, re.I)
    if m:
        level = int(m.group(1) or m.group(2))
        level = max(1, min(level, 6))
        return f"{'#' * level} {text}"
    if style in {"title", "标题"}:
        return f"# {text}"
    if style in {"subtitle", "副标题"}:
        return f"## {text}"
    # Conservative heuristic for numbered headings that lost styles.
    if re.match(r"^(摘要|关键词|引言|结论|参考文献|致谢)[:：]?$", text):
        return f"## {text}"
    if re.match(r"^\d+(\.\d+)*[、.．]\s*\S+", text) and len(text) < 120:
        depth = min(text.count(".") + text.count("．") + 2, 6)
        return f"{'#' * depth} {text}"
    return text


def escape_cell(text: str) -> str:
    return html.unescape(text).replace("|", "\\|").replace("\n", "<br>").strip()


def table_markdown(table: ET.Element) -> str:
    rows: list[list[str]] = []
    for tr in table.findall("w:tr", NS):
        row: list[str] = []
        for tc in tr.findall("w:tc", NS):
            row.append(escape_cell(text_from_node(tc)))
        if row:
            rows.append(row)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def convert_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        document_xml = zf.read("word/document.xml")
    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        return ""

    chunks: list[str] = []
    for child in list(body):
        if child.tag == qn("w:p"):
            md = paragraph_markdown(child)
        elif child.tag == qn("w:tbl"):
            md = table_markdown(child)
        else:
            md = ""
        if md:
            chunks.append(md)
    out = "\n\n".join(chunks).strip() + "\n"
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out


def main() -> None:
    repo = Path.cwd()
    docx_files = sorted(p for p in repo.glob("*.docx") if not p.name.startswith("~$"))
    if not docx_files:
        print("No DOCX files found at repository root.")
        return
    for docx in docx_files:
        md_path = docx.with_suffix(".md")
        md = convert_docx(docx)
        header = f"<!-- Auto-converted from {docx.name}. Edit the DOCX source or regenerate this file. -->\n\n"
        md_path.write_text(header + md, encoding="utf-8")
        print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
