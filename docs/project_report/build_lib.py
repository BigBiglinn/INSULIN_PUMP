"""Small document layer over python-docx: styles, numbered figures/tables/equations, markdown record import."""
import re, os
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_COLOR_INDEX
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = 'Times New Roman'
MONO = 'Consolas'
BODY_W = 6.27  # inches, A4 with 1 inch margins


def setfont(st, name=FONT, size=None, bold=None, italic=None):
    st.font.name = name
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), name)
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    if size:
        st.font.size = Pt(size)
    if bold is not None:
        st.font.bold = bold
    if italic is not None:
        st.font.italic = italic
    st.font.color.rgb = RGBColor(0, 0, 0)


class Rep:
    def __init__(self, labels=None):
        self.d = Document()
        self.labels = labels or {}
        self.new = {}
        self.ch = ''
        self.nf = self.nt = self.ne = 0
        self.sec = 0
        self.sub = 0
        self._styles()
        s = self.d.sections[0]
        self._page(s)

    def _page(self, s):
        s.page_width, s.page_height = Inches(8.27), Inches(11.69)
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)

    def _styles(self):
        S = self.d.styles
        n = S['Normal']
        setfont(n, size=12)
        n.paragraph_format.line_spacing = 1.5
        n.paragraph_format.space_after = Pt(6)
        n.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for name, size, before, after in (('Heading 1', 18, 0, 18), ('Heading 2', 14, 14, 6), ('Heading 3', 12, 10, 4)):
            h = S[name]
            setfont(h, size=size, bold=True, italic=False)
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            h.paragraph_format.line_spacing = 1.15

        def mk(name, base='Normal', **k):
            st = S.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = S[base]
            setfont(st, k.get('font', FONT), k.get('size', 12), k.get('bold'), k.get('italic'))
            pf = st.paragraph_format
            pf.line_spacing = k.get('ls', 1.0)
            pf.space_before = Pt(k.get('before', 0))
            pf.space_after = Pt(k.get('after', 0))
            pf.alignment = k.get('align', WD_ALIGN_PARAGRAPH.LEFT)
            pf.keep_with_next = k.get('kwn', False)
            return st
        mk('Figure Caption', size=10.5, before=4, after=12, align=WD_ALIGN_PARAGRAPH.CENTER)
        mk('Table Caption', size=10.5, before=10, after=4, align=WD_ALIGN_PARAGRAPH.CENTER, kwn=True)
        mk('Cell', size=10, ls=1.0)
        mk('SmallCell', size=8.5, ls=1.0)
        mk('Code', font=MONO, size=7.5, ls=1.0)
        mk('RecH1', size=12, bold=True, before=10, after=4, kwn=True)
        mk('RecH2', size=11, bold=True, before=8, after=3, kwn=True)
        mk('RecBody', size=10, ls=1.1, after=4, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        mk('FrontTitle', size=18, bold=True, before=0, after=18, align=WD_ALIGN_PARAGRAPH.CENTER)
        mk('Centered', size=12, ls=1.3, after=6, align=WD_ALIGN_PARAGRAPH.CENTER)
        mk('Refs', size=11, ls=1.15, after=4)
        for nm in ('TOC 1', 'TOC 2', 'Table of Figures'):
            try:
                st = S[nm]
            except KeyError:
                st = S.add_style(nm, WD_STYLE_TYPE.PARAGRAPH)
                st.base_style = S['Normal']
            setfont(st, size=11.5)
            st.paragraph_format.line_spacing = 1.1
            st.paragraph_format.space_after = Pt(3)
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        S['TOC 2'].paragraph_format.left_indent = Inches(.25)
        for nm in ('List Bullet', 'List Number'):
            setfont(S[nm], size=12)
            S[nm].paragraph_format.line_spacing = 1.3
            S[nm].paragraph_format.space_after = Pt(3)
            S[nm].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # ---- inline markup: **bold**, `code`, ~sub~, ^sup^, [[placeholder]]
    TOK = re.compile(r'(\*\*.+?\*\*|`[^`]+`|~[^~\s]{1,12}~|\^[^\^\s]{1,8}\^|\[\[.+?\]\]|\{(?:fig|tab|eq):[a-z0-9_]+\})')

    def rich(self, p, text, size=None):
        for part in self.TOK.split(text):
            if not part:
                continue
            m = part
            if part.startswith('{') and part.endswith('}'):
                r = p.add_run(self.labels.get(part[1:-1], '?'))
            elif m.startswith('**'):
                # bold may carry nested code or subscripts
                for sub in self.TOK.split(m[2:-2]):
                    if sub:
                        r = self._leaf(p, sub, size)
                        r.bold = True
                continue
            else:
                r = self._leaf(p, part, size)
            if size:
                r.font.size = Pt(size)
        return p

    def _leaf(self, p, part, size):
        if part.startswith('`'):
            r = p.add_run(part[1:-1])
            r.font.name = MONO
            r.font.size = Pt((size or 12) - 1.5)
        elif part.startswith('~') and part.endswith('~') and len(part) > 2:
            r = p.add_run(part[1:-1])
            r.font.subscript = True
        elif part.startswith('^') and part.endswith('^') and len(part) > 2:
            r = p.add_run(part[1:-1])
            r.font.superscript = True
        elif part.startswith('[['):
            r = p.add_run('[' + part[2:-2] + ']')
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        elif part.startswith('{') and part.endswith('}'):
            r = p.add_run(self.labels.get(part[1:-1], '?'))
        else:
            r = p.add_run(part)
        if size and not part.startswith('`'):
            r.font.size = Pt(size)
        return r

    def P(self, text, style=None):
        return self.rich(self.d.add_paragraph(style=style), text)

    def B(self, *items):
        for t in items:
            self.rich(self.d.add_paragraph(style='List Bullet'), t)

    def N(self, *items):
        # plain typed numbers keep each list restarting at 1 without numbering definitions
        for i, t in enumerate(items, 1):
            p = self.d.add_paragraph()
            p.paragraph_format.left_indent = Inches(.3)
            p.paragraph_format.first_line_indent = Inches(-.3)
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.space_after = Pt(3)
            self.rich(p, f'{i}.  {t}')

    def pagebreak(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def chapter(self, title, num=None, prefix='Chapter'):
        self.ch = str(num) if num is not None else ''
        self.nf = self.nt = self.ne = self.sec = self.sub = 0
        h = self.d.add_heading(level=1)
        h.paragraph_format.page_break_before = True
        h.add_run(f'{prefix} {num}: {title}' if num is not None else title)

    def front(self, title):
        p = self.d.add_paragraph(title, style='FrontTitle')
        p.paragraph_format.page_break_before = True

    def S(self, title, label=None):
        self.sec += 1
        self.sub = 0
        self.d.add_heading(f'{self.ch}.{self.sec} {title}', level=2)

    def SS(self, title):
        self.sub += 1
        self.d.add_heading(f'{self.ch}.{self.sec}.{self.sub} {title}', level=3)

    def _pref(self):
        return self.ch

    def fig(self, path, caption, label, width=BODY_W):
        self.nf += 1
        num = f'Figure {self._pref()}.{self.nf}'
        self.new['fig:' + label] = num
        p = self.d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_picture(path, width=Inches(width))
        self.d.add_paragraph(f'{num}: {caption}', style='Figure Caption')

    def eq(self, text, label):
        self.ne += 1
        num = f'({self._pref()}.{self.ne})'
        self.new['eq:' + label] = 'Eq. ' + num
        p = self.d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.2
        ts = p.paragraph_format.tab_stops
        ts.add_tab_stop(Inches(BODY_W / 2), WD_TAB_ALIGNMENT.CENTER)
        ts.add_tab_stop(Inches(BODY_W), WD_TAB_ALIGNMENT.RIGHT)
        p.add_run('\t')
        self.rich(p, text)
        p.add_run('\t' + num)

    def _shade(self, cell, color):
        tc = cell._tc.get_or_add_tcPr()
        sh = OxmlElement('w:shd')
        sh.set(qn('w:val'), 'clear')
        sh.set(qn('w:color'), 'auto')
        sh.set(qn('w:fill'), color)
        tc.append(sh)

    def _grid(self, head, rows, widths, style):
        t = self.d.add_table(rows=0, cols=len(head))
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        total = sum(widths)
        W = [Inches(w * BODY_W / total) for w in widths]
        grid = t._tbl.tblGrid
        for gc, w in zip(grid.findall(qn('w:gridCol')), W):
            gc.set(qn('w:w'), str(int(w.inches * 1440)))
        size = 8.5 if style == 'SmallCell' else 10
        for ri, row in enumerate([head] + rows):
            cells = t.add_row().cells
            tr = t.rows[-1]._tr
            trPr = tr.get_or_add_trPr()
            cs = OxmlElement('w:cantSplit')
            trPr.append(cs)
            if ri == 0:
                th = OxmlElement('w:tblHeader')
                trPr.append(th)
            for c, v, w in zip(cells, row, W):
                c.width = w
                p = c.paragraphs[0]
                p.style = self.d.styles[style]
                self.rich(p, str(v), size=size)
                if ri == 0:
                    for r in p.runs:
                        r.bold = True
                    self._shade(c, 'E8ECF1')
        sp = self.d.add_paragraph()
        sp.paragraph_format.space_after = Pt(6)
        sp.paragraph_format.line_spacing = 1.0
        return t

    def tab(self, caption, label, head, rows, widths=None):
        self.nt += 1
        num = f'Table {self._pref()}.{self.nt}'
        self.new['tab:' + label] = num
        self.d.add_paragraph(f'{num}: {caption}', style='Table Caption')
        self._grid(head, rows, widths or [1] * len(head), 'Cell')

    def toc(self, instr):
        p = self.d.add_paragraph()
        for kind, txt in (('begin', None), (None, instr), ('separate', None), ('t', 'Right-click and choose Update Field.'), ('end', None)):
            r = p.add_run()
            if kind in ('begin', 'separate', 'end'):
                fc = OxmlElement('w:fldChar')
                fc.set(qn('w:fldCharType'), kind)
                r._r.append(fc)
            elif kind == 't':
                r.text = txt
            else:
                it = OxmlElement('w:instrText')
                it.set(qn('xml:space'), 'preserve')
                it.text = txt
                r._r.append(it)

    def footer_num(self, sec, fmt, start=None):
        sec.footer.is_linked_to_previous = False
        p = sec.footer.paragraphs[0]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for kind in ('begin', 'instr', 'end'):
            r = p.add_run()
            r.font.size = Pt(11)
            if kind == 'instr':
                it = OxmlElement('w:instrText')
                it.set(qn('xml:space'), 'preserve')
                it.text = ' PAGE '
                r._r.append(it)
            else:
                fc = OxmlElement('w:fldChar')
                fc.set(qn('w:fldCharType'), kind)
                r._r.append(fc)
        pg = sec._sectPr.find(qn('w:pgNumType'))
        if pg is None:
            pg = OxmlElement('w:pgNumType')
            sec._sectPr.append(pg)
        pg.set(qn('w:fmt'), fmt)
        if start is not None:
            pg.set(qn('w:start'), str(start))

    def blank_footer(self, sec):
        sec.footer.is_linked_to_previous = False

    def code(self, text):
        for line in text.replace('\t', '    ').splitlines() or ['']:
            p = self.d.add_paragraph(style='Code')
            r = p.add_run(line if line else ' ')
            r.font.name = MONO

    def rec_h(self, text, lvl=1):
        self.d.add_paragraph(self._clean(text), style='RecH1' if lvl <= 1 else 'RecH2')

    @staticmethod
    def _clean(s):
        s = re.sub(r'<sub>(.*?)</sub>', r'~\1~', s)
        s = re.sub(r'<sup>(.*?)</sup>', r'^\1^', s)
        s = re.sub(r'<br\s*/?>', ' / ', s)
        s = re.sub(r'</li>\s*<li>', '; ', s)
        s = re.sub(r'</?(ul|li|ol)>', '', s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', s)
        # the record files use {..} nowhere as labels, but guard the label token
        return s

    def md(self, path, shift=1):
        """Imports a project markdown record: headings stay out of the contents list, tables stay as tables."""
        lines = open(path, encoding='utf-8').read().splitlines()
        i = 0
        para = []

        def flush():
            if para:
                self.rich(self.d.add_paragraph(style='RecBody'), self._clean(' '.join(para)), size=10)
                para.clear()
        while i < len(lines):
            ln = lines[i]
            st = ln.strip()
            if st.startswith('```'):
                flush()
                i += 1
                buf = []
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    buf.append(lines[i])
                    i += 1
                self.code('\n'.join(buf))
                sp = self.d.add_paragraph(style='Code')
            elif st.startswith('#'):
                flush()
                lvl = len(st) - len(st.lstrip('#'))
                self.rec_h(st.lstrip('#').strip().replace('**', ''), lvl - 1)
            elif st.startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i + 1]):
                flush()
                head = self._cells(st)
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    c = self._cells(lines[i].strip())
                    c += [''] * (len(head) - len(c))
                    rows.append(c[:len(head)])
                    i += 1
                self._mdtable(head, rows)
                continue
            elif re.match(r'^(\s*)[-*] ', ln) or re.match(r'^\s*\d+\. ', ln):
                flush()
                indent = len(ln) - len(ln.lstrip())
                m = re.match(r'^\s*(\d+\.|[-*]) (.*)', ln)
                mark = m.group(1) if m.group(1)[0].isdigit() else '•'
                p = self.d.add_paragraph(style='RecBody')
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.left_indent = Inches(.22 + indent * .05)
                p.paragraph_format.first_line_indent = Inches(-.2)
                p.paragraph_format.space_after = Pt(2)
                self.rich(p, self._clean(f'{mark} {m.group(2)}'), size=10)
            elif st.startswith('>'):
                flush()
                t = st.lstrip('> ').strip()
                if t:
                    p = self.d.add_paragraph(style='RecBody')
                    p.paragraph_format.left_indent = Inches(.2)
                    self.rich(p, self._clean(t), size=10)
            elif st in ('---', ''):
                flush()
            else:
                para.append(st)
            i += 1
        flush()

    @staticmethod
    def _cells(s):
        s = s.strip()
        if s.startswith('|'):
            s = s[1:]
        if s.endswith('|'):
            s = s[:-1]
        return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', s)]

    def _mdtable(self, head, rows):
        head = [self._clean(h) for h in head]
        rows = [[self._clean(c) for c in r] for r in rows]
        n = len(head)
        w = []
        for j in range(n):
            mx = max([len(head[j])] + [len(r[j]) for r in rows])
            w.append(max(mx ** .6, 2.2))
        self._grid(head, rows, w, 'SmallCell')

    def csv_table(self, path, cols=None, widths=None):
        import csv
        R = list(csv.reader(open(path, encoding='utf-8')))
        h, rows = R[0], R[1:]
        if cols:
            idx = [h.index(c) for c in cols]
            h = cols
            rows = [[r[i] for i in idx] for r in rows]
        self._grid(h, [[c.replace('`', "'") for c in r] for r in rows], widths or [1] * len(h), 'SmallCell')
