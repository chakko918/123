# -*- coding: utf-8 -*-
"""把 reports/*.md 转成同名 .docx（宋体正文 + 黑体标题 + 表格）。

用法：python scripts/md2docx.py
"""
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn

EAST_BODY = "宋体"
EAST_HEAD = "黑体"
ASCII_BODY = "Calibri"


def set_font(run, east=EAST_BODY, size=12, bold=False):
    run.font.name = ASCII_BODY
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east)
    run.font.size = Pt(size)
    run.bold = bold


def add_inline(paragraph, text, east=EAST_BODY, size=12):
    """处理行内 **加粗** 与 `代码`。"""
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = paragraph.add_run(part[2:-2])
            set_font(r, east, size, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            r = paragraph.add_run(part[1:-1])
            set_font(r, east, size)
            r.font.name = "Consolas"
        else:
            r = paragraph.add_run(part)
            set_font(r, east, size)


def is_table_sep(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", line)) and "---" in line


def convert(md_path: Path, out_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()

    i = 0
    in_code = False
    code_buf = []

    def flush_code():
        nonlocal code_buf
        if code_buf:
            p = doc.add_paragraph()
            r = p.add_run("\n".join(code_buf))
            r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), EAST_BODY)
            r.font.size = Pt(10)
            code_buf = []

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()
        if not stripped:
            flush_code()
            i += 1
            continue

        # 表格
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for tl in table_lines:
                if is_table_sep(tl):
                    continue
                rows.append([c.strip() for c in tl.strip("|").split("|")])
            if rows:
                ncols = max(len(r) for r in rows)
                table = doc.add_table(rows=len(rows), cols=ncols)
                table.style = "Table Grid"
                for ri, row in enumerate(rows):
                    for ci in range(ncols):
                        text = row[ci] if ci < len(row) else ""
                        cell = table.cell(ri, ci)
                        cell.text = ""
                        para = cell.paragraphs[0]
                        add_inline(para, text, east=EAST_BODY, size=10.5)
                        if ri == 0:
                            for run in para.runs:
                                run.bold = True
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_code()
            level = len(m.group(1))
            p = doc.add_heading(level=level)
            p.text = ""
            r = p.add_run(m.group(2))
            sizes = {1: 16, 2: 14, 3: 12, 4: 12}
            set_font(r, east=EAST_HEAD, size=sizes[level], bold=True)
            i += 1
            continue

        # 引用块
        if stripped.startswith(">"):
            flush_code()
            text = stripped.lstrip(">").strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(24)
            add_inline(p, text, east=EAST_BODY, size=10.5)
            for run in p.runs:
                run.italic = True
            i += 1
            continue

        # 无序列表
        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            flush_code()
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, m.group(1))
            i += 1
            continue

        # 有序列表
        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            flush_code()
            p = doc.add_paragraph(style="List Number")
            add_inline(p, m.group(1))
            i += 1
            continue

        # 普通段落
        flush_code()
        p = doc.add_paragraph()
        add_inline(p, stripped)
        i += 1

    flush_code()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print("OK", out_path.name)


def main():
    reports = Path(__file__).resolve().parent.parent / "reports"
    for md in sorted(reports.glob("*.md")):
        convert(md, md.with_suffix(".docx"))


if __name__ == "__main__":
    main()
