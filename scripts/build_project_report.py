"""Build the B.Tech-format project report (DOCX + PDF) from docs/project_report/src/*.md.

Source markup (one directive per line):
  @title / @certificate / @declaration      front-matter pages filled from META below and the source
  @unnumbered Heading                       front-matter or back-matter heading (own page)
  @toc  @lof  @lot                          contents, list of figures, list of tables
  @mainmatter                               new section, Arabic page numbers from 1
  # Chapter title {#label}                  numbered chapter (new page)
  ## Section {#label}   ### Subsection      numbered sections
  @appendix Title {#label}                  appendix chapter A, B, ... (new page)
  !fig label | path | caption | width_in    figure (caption below)
  !table label | caption [| w1,w2,...]      table (caption above); following lines are | cells |
  !eq label | text                          numbered display equation
  !code path | caption                      code listing from a repository file
  !codeblock / !endcode                     literal monospace block
  !box Title | text                         shaded note box
  !pagebreak
  - bullet     1. numbered item
Inline: **bold**, *italic*, `code`, _{sub}, ^{sup}, {fig:x} {tab:x} {eq:x} {sec:x} cross-references.

Two passes: the DOCX is rendered to PDF with LibreOffice, page numbers of every heading and caption are
read back from the PDF text, and the contents/lists are written with those page numbers.
Run from the repository root:  python scripts/build_project_report.py
"""
import os, re, glob, subprocess, shutil, sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RDIR = os.path.join(ROOT, "docs", "project_report")
SRC = os.path.join(RDIR, "src")
OUT_DOCX = os.path.join(RDIR, "PROJECT_REPORT.docx")
OUT_PDF = os.path.join(RDIR, "PROJECT_REPORT.pdf")
FONT = "Times New Roman"
MONO = "Courier New"
TEXT_W = 6.27  # A4 width 8.27 in - 2 x 1 in margins

# ------------------------------------------------------------------ low-level helpers
def set_cell_shading(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader"); el.set(qn("w:val"), "true"); trPr.append(el)


def no_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit"); el.set(qn("w:val"), "true"); trPr.append(el)


def add_field(run, instr):
    for kind, text in (("begin", None), ("instr", instr), ("separate", None), ("text", "1"), ("end", None)):
        if kind == "instr":
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text; run._r.append(el)
        elif kind == "text":
            t = OxmlElement("w:t"); t.text = text; run._r.append(t)
        else:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind); run._r.append(el)


def page_number_format(section, fmt, start=1):
    sectPr = section._sectPr
    pg = sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType"); sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt); pg.set(qn("w:start"), str(start))


def footer_page_number(section, title_page_blank=False):
    section.footer.is_linked_to_previous = False
    f = section.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in list(f.runs):
        r._r.getparent().remove(r._r)
    r = f.add_run(); r.font.name = FONT; r.font.size = Pt(11)
    add_field(r, "PAGE")
    if title_page_blank:
        section.different_first_page_header_footer = True


def set_margins(section):
    section.page_height, section.page_width = Cm(29.7), Cm(21.0)
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, m, Inches(1))
    section.footer_distance = Inches(0.5)


def style_doc(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st.paragraph_format
    pf.line_spacing = 1.5; pf.space_after = Pt(6); pf.space_before = Pt(0)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for lvl, size in ((1, 16), (2, 14), (3, 12)):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = FONT; h.font.size = Pt(size); h.font.bold = True; h.font.italic = False
        h.font.color.rgb = RGBColor(0, 0, 0)
        col = h.element.rPr.find(qn("w:color"))
        for a in ("w:themeColor", "w:themeShade"):
            if col is not None and col.get(qn(a)) is not None:
                del col.attrib[qn(a)]
        rpr = h.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.append(rf)
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), FONT)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
        h.paragraph_format.space_before = Pt(18 if lvl == 1 else 12)
        h.paragraph_format.space_after = Pt(8)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.line_spacing = 1.15
        h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT


# ------------------------------------------------------------------ inline markup
INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`|_\{[^}]*\}|\^\{[^}]*\})")


def add_inline(par, text, size=None, bold=False, italic=False, font=None):
    for part in INLINE.split(text):
        if not part:
            continue
        b, i, mono, sub, sup = bold, italic, False, False, False
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            part, b = part[2:-2], True
        elif part.startswith("`") and part.endswith("`"):
            part, mono = part[1:-1], True
        elif part.startswith("_{") and part.endswith("}"):
            part, sub = part[2:-1], True
        elif part.startswith("^{") and part.endswith("}"):
            part, sup = part[2:-1], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, i = part[1:-1], True
        r = par.add_run(part)
        r.bold, r.italic = b, i
        r.font.name = MONO if mono else (font or FONT)
        if mono:
            r.font.size = Pt((size or 12) - 1.5)
        elif size:
            r.font.size = Pt(size)
        if sub:
            r.font.subscript = True
        if sup:
            r.font.superscript = True
    return par


# ------------------------------------------------------------------ the builder
class Builder:
    def __init__(self, pages=None):
        self.pages = pages or {}
        self.doc = Document()
        style_doc(self.doc)
        set_margins(self.doc.sections[0])
        footer_page_number(self.doc.sections[0], title_page_blank=True)
        page_number_format(self.doc.sections[0], "lowerRoman", 1)
        self.chap = 0; self.sec = [0, 0]; self.appendix = None
        self.fig = 0; self.tab = 0; self.eq = 0
        self.toc, self.lof, self.lot = [], [], []
        self.first_block = True

    # numbering prefix for the current chapter
    def cpre(self):
        return self.appendix if self.appendix else str(self.chap)

    def par(self, text="", align=None, size=None, space_after=None, style=None, bold=False, italic=False,
            line=None, keep=False, indent=None):
        p = self.doc.add_paragraph(style=style)
        if align is not None:
            p.alignment = align
        if space_after is not None:
            p.paragraph_format.space_after = Pt(space_after)
        if line is not None:
            p.paragraph_format.line_spacing = line
        if keep:
            p.paragraph_format.keep_with_next = True
        if indent is not None:
            p.paragraph_format.left_indent = Inches(indent)
        add_inline(p, text, size=size, bold=bold, italic=italic)
        return p

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def heading(self, text, level, numbered=True, new_page=False, toc=True, label=None):
        if new_page and not self.first_block:
            self.page_break()
        self.first_block = False
        if level == 1:
            if numbered:
                if self.appendix:
                    head, num = f"APPENDIX {self.appendix}", self.appendix
                else:
                    self.chap += 1; head, num = f"CHAPTER {self.chap}", str(self.chap)
                self.sec = [0, 0]; self.fig = self.tab = self.eq = 0
                p = self.par(head, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, space_after=4, keep=True)
                p.paragraph_format.space_before = Pt(36)
                h = self.doc.add_heading(text.upper(), level=1)
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                h.runs[0].font.size = Pt(18)
                key = head
                self.toc.append((1, f"{num if not self.appendix else 'Appendix ' + num}  {text}", key))
                if label:
                    self.labels[label] = (f"Chapter {num}" if not self.appendix else f"Appendix {num}")
            else:
                h = self.doc.add_heading(text.upper(), level=1)
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                h.runs[0].font.size = Pt(16)
                if toc:
                    self.toc.append((0, text, text.upper()))
            return
        idx = level - 2
        self.sec[idx] += 1
        if idx == 0:
            self.sec[1] = 0
        num = f"{self.cpre()}." + ".".join(str(s) for s in self.sec[: idx + 1])
        h = self.doc.add_heading(f"{num}  {text}", level=level)
        if label:
            self.labels[label] = f"Section {num}"
        if level <= 3:
            self.toc.append((level, f"{num}  {text}", f"{num} {text}"))

    def resolve(self, text):
        def rep(m):
            k = m.group(1)
            return self.labels.get(k, "??" + k)
        return re.sub(r"\{((?:fig|tab|eq|sec|ch|app):[\w-]+)\}", rep, text)

    # ---------------------------------------------------------- blocks
    def figure(self, label, path, caption, width):
        full = os.path.join(ROOT, path)
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(full, width=Inches(width))
        num = self.labels[label]
        c = self.par("", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, line=1.15)
        r = c.add_run(f"{num}: "); r.bold = True; r.font.size = Pt(10.5); r.font.name = FONT
        add_inline(c, self.resolve(caption), size=10.5)
        self.lof.append((num, caption, f"{num}:"))

    def table(self, label, caption, rows, widths=None):
        num = self.labels[label]
        if num:
            c = self.par("", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, line=1.15, keep=True)
            r = c.add_run(f"{num}: "); r.bold = True; r.font.size = Pt(10.5); r.font.name = FONT
            add_inline(c, self.resolve(caption), size=10.5)
            self.lot.append((num, caption, f"{num}:"))
        ncol = max(len(r) for r in rows)
        t = self.doc.add_table(rows=len(rows), cols=ncol)
        t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        if widths:
            tot = sum(widths); ws = [TEXT_W * w / tot for w in widths]
        else:
            ws = [TEXT_W / ncol] * ncol
        size = 9.5 if ncol <= 4 else (9 if ncol <= 6 else 8)
        t.autofit = False
        grid = t._tbl.tblGrid
        for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
            gc.set(qn("w:w"), str(int(ws[j] * 1440)))
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        for i, row in enumerate(rows):
            tr = t.rows[i]; no_split(tr)
            if i == 0:
                repeat_header(tr)
            for j in range(ncol):
                cell = tr.cells[j]; cell.width = Inches(ws[j])
                txt = row[j] if j < len(row) else ""
                cp = cell.paragraphs[0]
                cp.paragraph_format.line_spacing = 1.0; cp.paragraph_format.space_after = Pt(1)
                cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_inline(cp, self.resolve(txt), size=size, bold=(i == 0))
                if i == 0:
                    set_cell_shading(cell, "D9D9D9")
        sp = self.doc.add_paragraph(); sp.paragraph_format.space_after = Pt(4); sp.paragraph_format.line_spacing = 1.0

    def equation(self, label, text):
        num = self.labels[label]
        p = self.doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W / 2), WD_TAB_ALIGNMENT.CENTER)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run("\t")
        add_inline(p, self.resolve(text), italic=False)
        p.add_run("\t" + num.replace("Equation ", ""))

    def code(self, lines, caption=None):
        if caption:
            c = self.par("", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, line=1.15, keep=True)
            add_inline(c, caption, size=10.5, bold=True)
        for ln in lines:
            p = self.doc.add_paragraph()
            pf = p.paragraph_format; pf.line_spacing = 1.0; pf.space_after = Pt(0); pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.left_indent = Inches(0.1)
            r = p.add_run(ln.rstrip("\n").replace("\t", "    ") or " ")
            r.font.name = MONO; r.font.size = Pt(7.5)
            r._r.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), MONO)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def box(self, title, text):
        t = self.doc.add_table(rows=1, cols=1); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = t.rows[0].cells[0]; cell.width = Inches(TEXT_W); set_cell_shading(cell, "F2F2F2")
        cp = cell.paragraphs[0]; cp.paragraph_format.line_spacing = 1.15; cp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_inline(cp, title + "  ", size=11, bold=True)
        add_inline(cp, self.resolve(text), size=11)
        sp = self.doc.add_paragraph(); sp.paragraph_format.space_after = Pt(2); sp.paragraph_format.line_spacing = 1.0

    def contents(self, kind):
        entries = {"toc": self.final_toc, "lof": self.final_lof, "lot": self.final_lot}[kind]
        for e in entries:
            level, text, key = e
            pg = self.pages.get((kind, key), "")
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.tab_stops.add_tab_stop(Inches(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            pf.line_spacing = 1.15; pf.space_after = Pt(3 if level <= 1 else 1); pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if kind == "toc":
                pf.left_indent = Inches({0: 0, 1: 0, 2: 0.3, 3: 0.65}[level])
                if level <= 1:
                    pf.space_before = Pt(6)
            else:
                pf.left_indent = Inches(1.0); pf.first_line_indent = Inches(-1.0)
            add_inline(p, text, size=11, bold=(kind == "toc" and level <= 1))
            r = p.add_run("\t" + str(pg)); r.font.size = Pt(11); r.font.name = FONT

    # ---------------------------------------------------------- source parsing
    def load(self):
        self.lines = []
        for f in sorted(glob.glob(os.path.join(SRC, "*.md"))):
            self.lines += open(f, encoding="utf-8").read().splitlines() + [""]

    def prescan(self):
        """Number every label and collect final TOC/LOF/LOT entries in order."""
        self.labels = {}
        chap, appx, sec, fig, tab, eq = 0, None, [0, 0], 0, 0, 0
        toc, lof, lot = [], [], []
        for ln in self.lines:
            m = re.match(r"^(#{1,3}) (.+?)(?:\s*\{#([\w:-]+)\})?\s*$", ln)
            if ln.startswith("@appendix "):
                t = ln[len("@appendix "):]
                lm = re.search(r"\{#([\w:-]+)\}", t); t = re.sub(r"\s*\{#[\w:-]+\}", "", t).strip()
                appx = chr(ord("A") + (0 if appx is None else ord(appx) - ord("A") + 1))
                sec = [0, 0]; fig = tab = eq = 0
                toc.append((1, f"Appendix {appx}  {t}", f"APPENDIX {appx}"))
                if lm:
                    self.labels[lm.group(1)] = f"Appendix {appx}"
                continue
            if ln.startswith("@unnumbered "):
                t = ln[len("@unnumbered "):].strip()
                toc.append((0, t, t.upper()))
                continue
            if m:
                lvl, t, lab = len(m.group(1)), m.group(2), m.group(3)
                pre = appx if appx else None
                if lvl == 1:
                    chap += 1; sec = [0, 0]; fig = tab = eq = 0
                    toc.append((1, f"{chap}  {t}", f"CHAPTER {chap}"))
                    if lab:
                        self.labels[lab] = f"Chapter {chap}"
                else:
                    i = lvl - 2; sec[i] += 1
                    if i == 0:
                        sec[1] = 0
                    num = f"{pre or chap}." + ".".join(str(s) for s in sec[: i + 1])
                    toc.append((lvl, f"{num}  {t}", f"{num} {t}"))
                    if lab:
                        self.labels[lab] = f"Section {num}"
                continue
            if ln.startswith("!fig "):
                parts = [x.strip() for x in ln[5:].split("|")]
                fig += 1; num = f"Figure {appx or chap}.{fig}"
                self.labels[parts[0]] = num; lof.append((2, f"{num}  {parts[2]}", f"{num}:"))
            elif ln.startswith("!table "):
                parts = [x.strip() for x in ln[7:].split("|")]
                if parts[0].startswith("nonum"):
                    self.labels[parts[0]] = ""; continue
                tab += 1; num = f"Table {appx or chap}.{tab}"
                self.labels[parts[0]] = num; lot.append((2, f"{num}  {parts[1]}", f"{num}:"))
            elif ln.startswith("!eq "):
                parts = [x.strip() for x in ln[4:].split("|", 1)]
                eq += 1; self.labels[parts[0]] = f"Equation ({appx or chap}.{eq})"
        # strip markup from list text
        clean = lambda s: re.sub(r"[*`]|_\{|\^\{|\}", "", s)
        self.final_toc = [(l, clean(t), k) for l, t, k in toc]
        self.final_lof = [(l, clean(re.sub(r"\{[\w:-]+\}", "", t)), k) for l, t, k in lof]
        self.final_lot = [(l, clean(re.sub(r"\{[\w:-]+\}", "", t)), k) for l, t, k in lot]

    def run(self, meta):
        self.load(); self.prescan()
        L = self.lines; i = 0; para = []
        def flush():
            if para:
                self.par(self.resolve(" ".join(s.strip() for s in para)))
                para.clear()
        while i < len(L):
            ln = L[i]
            s = ln.strip()
            if not s:
                flush(); i += 1; continue
            if s.startswith("<!--"):
                while "-->" not in L[i]:
                    i += 1
                i += 1; continue
            if s == "@title":
                flush(); self.title_page(meta); i += 1; continue
            if s.startswith("@unnumbered "):
                flush(); self.heading(s[12:].strip(), 1, numbered=False, new_page=True); i += 1; continue
            if s in ("@toc", "@lof", "@lot"):
                flush()
                name = {"@toc": "Table of Contents", "@lof": "List of Figures", "@lot": "List of Tables"}[s]
                self.heading(name, 1, numbered=False, new_page=True, toc=False)
                self.contents(s[1:]); i += 1; continue
            if s == "@mainmatter":
                flush()
                sec = self.doc.add_section(WD_SECTION.NEW_PAGE); set_margins(sec)
                footer_page_number(sec); sec.different_first_page_header_footer = False
                page_number_format(sec, "decimal", 1)
                self.first_block = True; i += 1; continue
            if s.startswith("@appendix "):
                flush()
                t = re.sub(r"\s*\{#[\w:-]+\}", "", s[10:]).strip()
                self.appendix = chr(ord("A") + (0 if self.appendix is None else ord(self.appendix) - ord("A") + 1))
                self.heading(t, 1, numbered=True, new_page=True); i += 1; continue
            m = re.match(r"^(#{1,3}) (.+?)(?:\s*\{#([\w:-]+)\})?\s*$", s)
            if m:
                flush(); lvl = len(m.group(1))
                self.heading(m.group(2), lvl, numbered=True, new_page=(lvl == 1), label=None); i += 1; continue
            if s == "!pagebreak":
                flush(); self.page_break(); i += 1; continue
            if s.startswith("!fig "):
                flush(); p = [x.strip() for x in s[5:].split("|")]
                self.figure(p[0], p[1], p[2], float(p[3]) if len(p) > 3 else 6.0); i += 1; continue
            if s.startswith("!table "):
                flush(); p = [x.strip() for x in s[7:].split("|")]
                widths = [float(w) for w in p[2].split(",")] if len(p) > 2 and p[2] else None
                rows = []; i += 1
                while i < len(L) and L[i].strip().startswith("|"):
                    r = L[i].strip().strip("|")
                    cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", r)]
                    if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                        rows.append(cells)
                    i += 1
                self.table(p[0], p[1], rows, widths); continue
            if s.startswith("!eq "):
                flush(); p = [x.strip() for x in s[4:].split("|", 1)]
                self.equation(p[0], p[1]); i += 1; continue
            if s.startswith("!code "):
                flush(); p = [x.strip() for x in s[6:].split("|", 1)]
                src = open(os.path.join(ROOT, p[0]), encoding="utf-8").read().splitlines()
                self.code(src, p[1] if len(p) > 1 else p[0]); i += 1; continue
            if s == "!codeblock":
                flush(); i += 1; blk = []
                while L[i].strip() != "!endcode":
                    blk.append(L[i]); i += 1
                self.code(blk); i += 1; continue
            if s.startswith("!box "):
                flush(); p = [x.strip() for x in s[5:].split("|", 1)]
                self.box(p[0], p[1]); i += 1; continue
            mb = re.match(r"^(-|\d+\.)\s+(.*)$", s)
            if mb and not para:
                p = self.doc.add_paragraph(style="List Bullet" if mb.group(1) == "-" else "List Number")
                p.paragraph_format.line_spacing = 1.3; p.paragraph_format.space_after = Pt(2)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_inline(p, self.resolve(mb.group(2)))
                i += 1; continue
            para.append(s); i += 1
        flush()
        self.doc.core_properties.title = meta["title"]
        self.doc.core_properties.author = meta["author_line"]
        return self.doc

    def title_page(self, m):
        C = WD_ALIGN_PARAGRAPH.CENTER
        self.first_block = False
        p0 = self.par("A PROJECT REPORT ON", align=C, size=13, bold=True, space_after=14)
        p0.paragraph_format.space_before = Pt(40)
        self.par(m["title"].upper(), align=C, size=18, bold=True, space_after=6, line=1.2)
        self.par(m["subtitle"], align=C, size=13, italic=True, space_after=60, line=1.2)
        self.par("Submitted in partial fulfilment of the requirements for the degree of", align=C, size=12, space_after=0)
        self.par("BACHELOR OF TECHNOLOGY", align=C, size=13, bold=True, space_after=48)
        self.par("Submitted by", align=C, size=12, italic=True, space_after=0)
        for a in m["authors"]:
            self.par(a, align=C, size=13, bold=True, space_after=0)
        self.par("", space_after=10)
        self.par("Under the guidance of", align=C, size=12, italic=True, space_after=0)
        self.par(m["guide"], align=C, size=13, bold=True, space_after=90)
        logo = m.get("logo")
        if logo and os.path.exists(logo):
            p = self.doc.add_paragraph(); p.alignment = C; p.add_run().add_picture(logo, width=Inches(1.3))
        self.par(m["department"].upper(), align=C, size=13, bold=True, space_after=0)
        self.par(m["institute"].upper(), align=C, size=13, bold=True, space_after=0)
        self.par(m["place"], align=C, size=12, space_after=0)
        self.par(m["date"], align=C, size=12, space_after=0)


META = {
    "title": "Piezo Insulin Pump v2",
    "subtitle": "Design of a Battery-Powered, Piezoelectric Syringe-Drive Insulin Pump Prototype with "
                "Dual-MCU Safety Architecture and Bluetooth Low Energy (Rev B Digital Design)",
    "authors": ["[Student name]  ([Roll number])"],
    "author_line": "[Student name]",
    "guide": "[Supervisor name, designation]",
    "department": "Department of [Department name]",
    "institute": "Indian Institute of Technology Guwahati",
    "place": "Guwahati, Assam 781039, India",
    "date": "November 2026",
}


def render_pdf(docx_path, outdir):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    return os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")


def page_texts(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    out = []
    for k in range(1, n + 1):
        out.append(subprocess.run(["pdftotext", "-layout", "-f", str(k), "-l", str(k), pdf, "-"],
                                  capture_output=True, text=True).stdout)
    return out


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    s = ""
    for v, r in vals:
        while n >= v:
            s += r; n -= v
    return s


def locate(b, texts):
    """Map each TOC/LOF/LOT key to its printed page number."""
    norm = lambda s: re.sub(r"\s+", " ", s).strip().upper()
    lines = [[norm(l) for l in t.splitlines() if l.strip()] for t in texts]
    # main matter starts at the page that carries "CHAPTER 1" as a line, after the contents pages
    main = next(k for k, ls in enumerate(lines) if "CHAPTER 1" in ls and not any("TABLE OF CONTENTS" == x for x in ls)
                and k > 3 and not any("....." in x for x in ls))
    pages = {}
    for kind, entries in (("toc", b.final_toc), ("lof", b.final_lof), ("lot", b.final_lot)):
        for level, text, key in entries:
            K = norm(key)
            start = main if kind != "toc" or level != 0 else 1
            found = None
            for k in range(start, len(lines)):
                if any("....." in x for x in lines[k]):
                    continue
                if any(x == K or x.startswith(K + " ") or (kind != "toc" and x.startswith(K)) or
                       (kind == "toc" and level >= 2 and x.startswith(K[:60])) for x in lines[k]):
                    found = k; break
            if found is None and level == 0:
                for k in range(1, main):
                    if any(x == K for x in lines[k]) and not any("....." in x for x in lines[k]):
                        found = k; break
            if found is None:
                pages[(kind, key)] = "?"
            elif found >= main:
                pages[(kind, key)] = str(found - main + 1)
            else:
                pages[(kind, key)] = roman(found + 1)
    return pages


def main():
    tmp = os.path.join(RDIR, ".build"); os.makedirs(tmp, exist_ok=True)
    pages = {}
    for attempt in range(3):
        b = Builder(pages)
        doc = b.run(META)
        path = os.path.join(tmp, "PROJECT_REPORT.docx"); doc.save(path)
        pdf = render_pdf(path, tmp)
        new = locate(b, page_texts(pdf))
        missing = [k for k, v in new.items() if v == "?"]
        print(f"pass {attempt + 1}: {len(new)} entries, {len(missing)} not found", missing[:8])
        if new == pages:
            break
        pages = new
    shutil.copy(path, OUT_DOCX); shutil.copy(pdf, OUT_PDF)
    print("wrote", OUT_DOCX, "and", OUT_PDF)


if __name__ == "__main__":
    main()
