# -*- coding: utf-8 -*-
"""
Final paper text extractor (stdlib only).

Pipeline
  1. brute-force `N G obj ... endobj` scan; expand /Type /ObjStm containers
  2. per font object build a code -> character decoder:
       - Type0/Identity-H  : code=GID -> embedded-font cmap -> /ToUnicode -> MS glyph order
       - simple fonts      : /Encoding /Differences -> code-as-ASCII
  3. walk the page tree, interpret Tf / Tj / TJ / ' / " and vertical moves
  4. repair runs of text set in a shifted symbolic font (line-level shift search)
Output: 03_literature/paper_clean.txt
"""
# -*- coding: utf-8 -*-
# --- workspace-root anchor (added during reorganisation) -------------------
from pathlib import Path as _Path
import os as _os
_ROOT = _Path(__file__).resolve().parent
while not (_ROOT / "01_data").exists() and _ROOT.parent != _ROOT:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
# --------------------------------------------------------------------------
import re, sys, zlib, struct
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
PDF = next(iter(ROOT.glob("**/Beyond More Is Better*.pdf")), None)
if PDF is None:
    raise SystemExit("source PDF not found under workspace root")
OUT = ROOT / "03_literature" / "paper_clean.txt"

data = PDF.read_bytes()

# ------------------------------------------------------------------ objects
objs = {}
for m in re.finditer(rb"(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj", data, re.S):
    n = int(m.group(1)); body = m.group(3)
    sm = re.search(rb"stream\r?\n", body)
    if sm:
        s = sm.end(); e = body.find(b"endstream", s); e = e if e != -1 else len(body)
        objs[n] = [body[:sm.start()], body[s:e]]
    else:
        objs[n] = [body, None]

def inflate(raw):
    for f in (lambda b: zlib.decompress(b),
              lambda b: zlib.decompressobj().decompress(b),
              lambda b: zlib.decompress(b, -15)):
        try:
            o = f(raw)
            if o:
                return o
        except Exception:
            pass
    return None

def sbytes(n):
    dic, raw = objs.get(n, [b"", None])
    if raw is None:
        return None
    if not dic:
        return inflate(raw) or raw
    if b"FlateDecode" in dic:
        return inflate(raw)
    return raw if b"Filter" not in dic else None

for n in list(objs):
    dic, raw = objs[n]
    if b"/ObjStm" not in dic:
        continue
    dec = sbytes(n)
    if not dec:
        continue
    N = int(re.search(rb"/N\s+(\d+)", dic).group(1))
    First = int(re.search(rb"/First\s+(\d+)", dic).group(1))
    hdr = dec[:First].split()
    for i in range(N):
        try:
            onum = int(hdr[2 * i]); off = int(hdr[2 * i + 1])
        except Exception:
            break
        end = (int(hdr[2 * i + 3]) + First) if 2 * i + 3 < len(hdr) else len(dec)
        if onum not in objs:
            objs[onum] = [dec[First + off:end], None]

print(f"objects: {len(objs):,}")

# ------------------------------------------------------------- TrueType bits
def ttf_tables(buf):
    if len(buf) < 12:
        return {}
    try:
        num = struct.unpack(">H", buf[4:6])[0]
    except Exception:
        return {}
    tabs, off = {}, 12
    for _ in range(num):
        if off + 16 > len(buf):
            break
        tabs[buf[off:off + 4]] = struct.unpack(">II", buf[off + 8:off + 16])
        off += 16
    return tabs

def ttf_cmap(buf, tabs):
    if b"cmap" not in tabs:
        return {}
    base = tabs[b"cmap"][0]
    if base + 4 > len(buf):
        return {}
    n = struct.unpack(">H", buf[base + 2:base + 4])[0]
    best = None
    for i in range(n):
        rec = base + 4 + 8 * i
        if rec + 8 > len(buf):
            break
        pid, eid, off = struct.unpack(">HHI", buf[rec:rec + 8])
        sc = {(3, 1): 3, (3, 10): 3, (3, 0): 2, (0, 3): 2, (0, 4): 2, (1, 0): 1}.get((pid, eid), 0)
        if best is None or sc > best[0]:
            best = (sc, base + off)
    if not best:
        return {}
    sub = best[1]
    if sub + 2 > len(buf):
        return {}
    fmt = struct.unpack(">H", buf[sub:sub + 2])[0]
    g2u = {}
    if fmt == 4:
        segX2 = struct.unpack(">H", buf[sub + 6:sub + 8])[0]
        seg = segX2 // 2
        ends = struct.unpack(">%dH" % seg, buf[sub + 14:sub + 14 + segX2])
        starts = struct.unpack(">%dH" % seg, buf[sub + 16 + segX2:sub + 16 + 2 * segX2])
        deltas = struct.unpack(">%dh" % seg, buf[sub + 16 + 2 * segX2:sub + 16 + 3 * segX2])
        rop = sub + 16 + 3 * segX2
        roffs = struct.unpack(">%dH" % seg, buf[rop:rop + segX2])
        for i in range(seg):
            for c in range(starts[i], min(ends[i], 0xFFFF) + 1):
                if roffs[i] == 0:
                    g = (c + deltas[i]) & 0xFFFF
                else:
                    gp = rop + 2 * i + roffs[i] + 2 * (c - starts[i])
                    if gp + 2 > len(buf):
                        continue
                    g = struct.unpack(">H", buf[gp:gp + 2])[0]
                    if g:
                        g = (g + deltas[i]) & 0xFFFF
                if g and g not in g2u:
                    g2u[g] = chr(c)
    elif fmt == 12:
        ng = struct.unpack(">I", buf[sub + 12:sub + 16])[0]
        p = sub + 16
        for _ in range(ng):
            if p + 12 > len(buf):
                break
            sc_, ec, sg = struct.unpack(">III", buf[p:p + 12]); p += 12
            for c in range(sc_, min(ec, sc_ + 20000) + 1):
                g = sg + (c - sc_)
                if g and g not in g2u:
                    g2u[g] = chr(c)
    elif fmt == 6:
        first = struct.unpack(">H", buf[sub + 6:sub + 8])[0]
        cnt = struct.unpack(">H", buf[sub + 8:sub + 10])[0]
        for i in range(cnt):
            g = struct.unpack(">H", buf[sub + 10 + 2 * i:sub + 12 + 2 * i])[0]
            if g and g not in g2u:
                g2u[g] = chr(first + i)
    return g2u

def ttf_post(buf, tabs):
    if b"post" not in tabs:
        return {}
    base = tabs[b"post"][0]
    if base + 34 > len(buf):
        return {}
    if struct.unpack(">I", buf[base:base + 4])[0] != 0x00020000:
        return {}
    ng = struct.unpack(">H", buf[base + 32:base + 34])[0]
    idx, p = [], base + 34
    for _ in range(ng):
        if p + 2 > len(buf):
            break
        idx.append(struct.unpack(">H", buf[p:p + 2])[0]); p += 2
    names = []
    while p < len(buf) and len(names) < 500:
        ln = buf[p]; p += 1
        names.append(buf[p:p + ln].decode("latin-1")); p += ln
    return {g: names[ix - 258] for g, ix in enumerate(idx) if 258 <= ix < 258 + len(names)}

MAC_ORDER = (" .notdef .null nonmarkingreturn space exclam quotedbl numbersign dollar percent "
             "ampersand quotesingle parenleft parenright asterisk plus comma hyphen period slash "
             "zero one two three four five six seven eight nine colon semicolon less equal greater "
             "question at A B C D E F G H I J K L M N O P Q R S T U V W X Y Z bracketleft backslash "
             "bracketright asciicircum underscore grave a b c d e f g h i j k l m n o p q r s t u v w "
             "x y z braceleft bar braceright asciitilde").split()
NAME2CHAR = {"space": " ", "exclam": "!", "quotedbl": '"', "numbersign": "#", "dollar": "$",
             "percent": "%", "ampersand": "&", "quotesingle": "'", "parenleft": "(",
             "parenright": ")", "asterisk": "*", "plus": "+", "comma": ",", "hyphen": "-",
             "period": ".", "slash": "/", "colon": ":", "semicolon": ";", "less": "<",
             "equal": "=", "greater": ">", "question": "?", "at": "@", "bracketleft": "[",
             "backslash": "\\", "bracketright": "]", "asciicircum": "^", "underscore": "_",
             "grave": "`", "braceleft": "{", "bar": "|", "braceright": "}", "asciitilde": "~",
             "spacehackarabic": " "}

def parse_pdf_cmap(dec):
    m = {}; txt = dec.decode("latin-1")
    for blk in re.findall(r"beginbfchar(.*?)endbfchar", txt, re.S):
        for s, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            try:
                m[int(s, 16)] = bytes.fromhex(d).decode("utf-16-be", "ignore")
            except Exception:
                pass
    for blk in re.findall(r"beginbfrange(.*?)endbfrange", txt, re.S):
        for lo, hi, d in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            try:
                a, b = int(lo, 16), int(hi, 16); base = bytes.fromhex(d)
                for k in range(a, b + 1):
                    tail = (int.from_bytes(base[-2:], "big") + (k - a)).to_bytes(2, "big")
                    m[k] = (base[:-2] + tail).decode("utf-16-be", "ignore")
            except Exception:
                pass
        for lo, hi, arr in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", blk, re.S):
            try:
                a, b = int(lo, 16), int(hi, 16)
                items = re.findall(r"<([0-9A-Fa-f]*)>", arr)
                for k, it in zip(range(a, b + 1), items):
                    m[k] = bytes.fromhex(it).decode("utf-16-be", "ignore") if it else ""
            except Exception:
                pass
    return m

def build_fonts():
    fonts = {}
    for n, (dic, _) in objs.items():
        if not re.search(rb"/Type\s*/Font", dic):
            continue
        tu = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", dic)
        pdf_map = {}
        if tu:
            b = sbytes(int(tu.group(1)))
            if b:
                pdf_map = parse_pdf_cmap(b)
        is_cid = bool(re.search(rb"/Type0|Identity-H", dic))
        g2u, names = {}, {}
        if is_cid:
            desc = re.search(rb"/DescendantFonts\s*\[\s*(\d+)\s+\d+\s+R", dic)
            fd = objs.get(int(desc.group(1)), [b"", None])[0] if desc else b""
            fdr = re.search(rb"/FontDescriptor\s+(\d+)\s+\d+\s+R", fd)
            fdesc = objs.get(int(fdr.group(1)), [b"", None])[0] if fdr else b""
            for key in (b"/FontFile2", b"/FontFile3", b"/FontFile"):
                ff = re.search(key + rb"\s+(\d+)\s+\d+\s+R", fdesc)
                if ff:
                    buf = sbytes(int(ff.group(1)))
                    if buf:
                        tabs = ttf_tables(buf)
                        g2u = ttf_cmap(buf, tabs)
                        names = ttf_post(buf, tabs)
                    break
        else:
            enc = re.search(rb"/Encoding\s+(\d+)\s+\d+\s+R", dic)
            encdic = objs.get(int(enc.group(1)), [b"", None])[0] if enc else dic
            dm = re.search(rb"/Differences\s*\[(.*?)\]", encdic, re.S)
            if dm:
                cur = None
                for tk in dm.group(1).split():
                    if tk.startswith(b"/"):
                        cur = tk[1:].decode("latin-1")
                    else:
                        try:
                            c = int(tk)
                        except Exception:
                            continue
                        if cur:
                            names[c] = cur
                            cur = None
        fonts[n] = dict(pdf=pdf_map, g2u=g2u, names=names, cid=is_cid)
    return fonts

FONTS = build_fonts()

def glyph_char(nm):
    if nm in NAME2CHAR:
        return NAME2CHAR[nm]
    if len(nm) == 1:
        return nm
    if nm.startswith("uni") and len(nm) >= 7:
        try:
            return chr(int(nm[3:7], 16))
        except Exception:
            return ""
    return ""

def char_for(fobj, code):
    f = FONTS.get(fobj)
    if not f:
        return ""
    if not f["cid"]:
        nm = f["names"].get(code)
        if nm:
            return glyph_char(nm)
        return chr(code) if 32 <= code < 127 else ""
    if code in f["g2u"]:
        return f["g2u"][code]
    if code in f["pdf"]:
        return f["pdf"][code]
    nm = f["names"].get(code, "")
    if nm:
        c = glyph_char(nm)
        if c:
            return c
    if code < len(MAC_ORDER):
        nm = MAC_ORDER[code]
        return NAME2CHAR.get(nm, nm if len(nm) == 1 else "")
    return ""

def dec_bytes(bs, fobj):
    f = FONTS.get(fobj)
    if f and f["cid"]:
        if len(bs) % 2:
            bs += b"\x00"
        return "".join(char_for(fobj, int.from_bytes(bs[i:i + 2], "big")) for i in range(0, len(bs), 2))
    return "".join(char_for(fobj, b) for b in bs)

# ------------------------------------------------------------------- bigrams
BIGRAMS = {}
for w, c in {
    "th": 3.56, "he": 3.07, "in": 2.43, "er": 2.05, "an": 1.99, "re": 1.85, "on": 1.76,
    "at": 1.49, "en": 1.45, "nd": 1.35, "ti": 1.34, "es": 1.31, "or": 1.28, "te": 1.27,
    "of": 1.17, "ed": 1.17, "is": 1.13, "it": 1.12, "al": 1.09, "ar": 1.07, "st": 1.05,
    "to": 1.04, "nt": 1.04, "ng": 0.95, "se": 0.93, "ha": 0.93, "as": 0.87, "ou": 0.87,
    "io": 0.83, "le": 0.83, "ve": 0.83, "co": 0.79, "me": 0.79, "de": 0.76, "hi": 0.76,
    "ri": 0.73, "ro": 0.73, "ic": 0.70, "ne": 0.69, "ea": 0.69, "ra": 0.69, "ce": 0.65,
    "li": 0.62, "ch": 0.60, "ll": 0.58, "be": 0.58, "ma": 0.57, "si": 0.55, "om": 0.55,
    "ur": 0.54, "ca": 0.53, "el": 0.53, "ta": 0.53, "la": 0.53, "ns": 0.51, "di": 0.50,
    "fo": 0.49, "ho": 0.46, "pe": 0.46, "ec": 0.45, "pr": 0.45, "no": 0.44, "ct": 0.44,
    "us": 0.43, "ac": 0.43, "ot": 0.42, "il": 0.42, "tr": 0.42, "ly": 0.42, "nc": 0.41,
    "et": 0.41, "ut": 0.40, "ss": 0.40, "so": 0.40, "am": 0.39, "em": 0.39, "rs": 0.39,
    "pa": 0.38, "mi": 0.37, "po": 0.37, "ie": 0.35, "ge": 0.35, "ir": 0.35, "ee": 0.35,
    "ag": 0.34, "bl": 0.33, "pl": 0.33, "vi": 0.32, "id": 0.32, "ig": 0.30, "gh": 0.30,
    "wi": 0.29, "lo": 0.29, "ry": 0.28, "ol": 0.28, "ey": 0.26, "ay": 0.26, "ai": 0.26,
    "sp": 0.25, "rt": 0.25, "sc": 0.25, "nc": 0.41, "ta": 0.53,
}.items():
    BIGRAMS[w] = c

def bigram_score(s):
    low = "".join(ch for ch in s.lower() if ch.isalpha() or ch == " ")
    total = 0.0
    for i in range(len(low) - 1):
        a, b = low[i], low[i + 1]
        if a.isalpha() and b.isalpha():
            total += BIGRAMS.get(a + b, -2.2)
    return total

def shift_alpha(s, k):
    o = []
    for ch in s:
        if "a" <= ch <= "z":
            o.append(chr((ord(ch) - 97 + k) % 26 + 97))
        elif "A" <= ch <= "Z":
            o.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            o.append(ch)
    return "".join(o)

# ---- pass 1: decode, keeping per-font samples so a shifted font can be detected
seen = {}

def get_ref(dic, key):
    m = re.search(key + rb"\s+(\d+)\s+\d+\s+R", dic)
    return int(m.group(1)) if m else None

pages = []
for num, (dic, _) in objs.items():
    if re.search(rb"/Type\s*/Catalog", dic):
        def walk(n, d=0):
            if d > 12 or n is None:
                return
            dd = objs.get(n, [b"", None])[0]
            if re.search(rb"/Type\s*/Page\b", dd) and not re.search(rb"/Type\s*/Pages", dd):
                pages.append(n); return
            kids = re.search(rb"/Kids\s*\[(.*?)\]", dd, re.S)
            if kids:
                for k in re.findall(rb"(\d+)\s+\d+\s+R", kids.group(1)):
                    walk(int(k), d + 1)
        walk(get_ref(dic, rb"/Pages"))
        break

def lit(raw):
    out, i = [], 0
    while i < len(raw):
        c = raw[i]
        if c == 0x5C and i + 1 < len(raw):
            n = raw[i + 1]
            mp = {ord('n'): 10, ord('r'): 13, ord('t'): 9, ord('b'): 8, ord('f'): 12,
                  ord('('): 40, ord(')'): 41, ord('\\'): 92}
            if n in mp:
                out.append(mp[n]); i += 2; continue
            if 0x30 <= n <= 0x37:
                j = i + 1; od = b""
                while j < len(raw) and len(od) < 3 and 0x30 <= raw[j] <= 0x37:
                    od += bytes([raw[j]]); j += 1
                out.append(int(od, 8)); i = j; continue
            i += 2; continue
        out.append(c); i += 1
    return bytes(out)

TOK = re.compile(rb"/([A-Za-z0-9_.+-]+)\s+[-\d.]+\s+Tf"
                 rb"|\[(.*?)\]\s*TJ"
                 rb"|(\((?:\\.|[^\\()])*\))\s*Tj"
                 rb"|<([0-9A-Fa-f\s]+)>\s*Tj"
                 rb"|(T\*|Td|TD|Tm|ET)", re.S)

def subdict(dic, key):
    """Return the value of /key: an indirect object's dict, or an inline <<...>>."""
    m = re.search(key + rb"\s+(\d+)\s+\d+\s+R", dic)
    if m:
        return objs.get(int(m.group(1)), [b"", None])[0]
    i = dic.find(key + b"<<")
    if i == -1:
        i = dic.find(key)
        if i == -1:
            return b""
        i = dic.find(b"<<", i)
        if i == -1:
            return b""
    j = i + len(key)
    while j < len(dic) and dic[j:j + 2] != b"<<":
        j += 1
    depth, k = 0, j
    while k < len(dic) - 1:
        if dic[k:k + 2] == b"<<":
            depth += 1; k += 2; continue
        if dic[k:k + 2] == b">>":
            depth -= 1; k += 2
            if depth == 0:
                return dic[j:k]
            continue
        k += 1
    return b""

page_out = []
for pno in pages:
    dic = objs.get(pno, [b"", None])[0]
    # resources may be inline or inherited from ancestor /Pages nodes
    res = b""
    node = pno
    for _ in range(8):
        node_dic = objs.get(node, [b"", None])[0]
        cand = subdict(node_dic, rb"/Resources")
        if b"/Font" in cand:
            res = cand
            break
        parent = get_ref(node_dic, rb"/Parent")
        if parent is None:
            break
        node = parent
    fonts = {}
    fdic = subdict(res, rb"/Font")
    if fdic:
        for fname, onum in re.findall(rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+\d+\s+R", fdic):
            fonts[fname.decode("latin-1")] = int(onum)
    cnums = []
    cr = get_ref(dic, rb"/Contents")
    if cr:
        cnums = [cr]
    else:
        cm = re.search(rb"/Contents\s*\[(.*?)\]", dic, re.S)
        if cm:
            cnums = [int(x) for x in re.findall(rb"(\d+)\s+\d+\s+R", cm.group(1))]
    cur, out = None, []
    ntok = 0
    for cn in cnums:
        cb = sbytes(cn)
        if not cb:
            continue
        for m in TOK.finditer(cb):
            ntok += 1
            if m.group(1):
                cur = fonts.get(m.group(1).decode("latin-1"))
            elif m.group(2) is not None:
                parts = []
                for piece in re.finditer(rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>|-?\d+(?:\.\d+)?", m.group(2)):
                    t = piece.group(0)
                    if t.startswith(b"("):
                        parts.append(dec_bytes(lit(t[1:-1]), cur))
                    elif t.startswith(b"<"):
                        hx = re.sub(rb"\s", b"", t[1:-1])
                        if len(hx) % 2:
                            hx += b"0"
                        try:
                            parts.append(dec_bytes(bytes.fromhex(hx.decode()), cur))
                        except Exception:
                            pass
                    else:
                        try:
                            if float(t) < -180:
                                parts.append(" ")
                        except Exception:
                            pass
                out.append("".join(parts))
            elif m.group(3) is not None:
                out.append(dec_bytes(lit(m.group(3)[1:-1]), cur))
            elif m.group(4) is not None:
                hx = re.sub(rb"\s", b"", m.group(4))
                if len(hx) % 2:
                    hx += b"0"
                try:
                    out.append(dec_bytes(bytes.fromhex(hx.decode()), cur))
                except Exception:
                    pass
            else:
                out.append("\n")
    page_out.append("".join(out))
    if len(page_out) <= 10:
        print(f"  page {len(page_out)}: tokens={ntok} chars={len(page_out[-1])} "
              f"fonts={list(fonts.items())[:4]}")

full = "\n".join(f"===== PAGE {i+1} =====\n{t}" for i, t in enumerate(page_out))
full = "".join(ch if (ch.isprintable() or ch in "\n\t") else " " for ch in full)
full = re.sub(r"[ \t]+", " ", full)
full = re.sub(r"\n{3,}", "\n\n", full)

# ---- repair shifted symbol-font lines (word-level bigram scoring)
WORDS = set("""a an the and or but if then than that this these those these there their them they
we our you your it its is are was were be been being have has had do does did not no nor so
as at by for from in into of on onto out over to up with within without about above after again
against all also am among any because before below between both can could did down during each few
first for further get given go had has have he her here hers him his how however i if in into it its
just know like made make many may me might more most much must my no nor not now of off often on once
one only or other our out over own same see she should since some such take than that the their them
then there these they this those through thus to too under until up upon us use used using very was
we well were what when where which while who whom why will with within without would year years
table tables figure figures note notes variable variables coefficient coefficients estimate estimates
standard error errors mean median value values index indexes threshold thresholds peak cluster clusters
model models regression regressions robustness results result data dataset sample samples price prices
hybridization quadratic linear dependent independent effect effects significant significance level
study research analysis variable score scores number numbers total total games game steam tag tags
meta subgenre subgenres dna blue ocean review reviews performance commercial category categories
distribution normal log reviews revenue sales market markets indie developer developers""".split())

def _word_score(w: str) -> float:
    lw = w.lower()
    if lw in WORDS:
        return 8.0
    for suf in ("s", "es", "ed", "d", "ing", "ly"):
        if lw.endswith(suf) and lw[:-len(suf)] in WORDS:
            return 7.0
    return bigram_score(lw)

def fix_line(line: str) -> str:
    def repl(m):
        tok = m.group(0)
        if len(tok) < 4 or tok.isdigit():
            return tok
        base = _word_score(tok)
        best, best_sc = tok, base
        for k in range(1, 26):
            c = shift_alpha(tok, k)
            sc = _word_score(c)
            if sc > best_sc + 1e-9:
                best, best_sc = c, sc
        # only accept a shift if it is clearly better than the original
        return best if best_sc >= base + 4.0 else tok
    return re.sub(r"[A-Za-z]{4,}", repl, line)

def fix_line2(line: str) -> str:
    """Whole-line shift, accepted only when the gain is large (clearly shifted prose)."""
    if sum(c.isalpha() for c in line) < 12:
        return line
    base = bigram_score(line)
    best, best_sc = 0, base
    for k in range(1, 26):
        sc = bigram_score(shift_alpha(line, k))
        if sc > best_sc + 1e-9:
            best, best_sc = k, sc
    if best and (best_sc - base) > max(12.0, 0.35 * abs(base)):
        return shift_alpha(line, best)
    return line

_nfix = 0
fixed_lines = []
for ln in full.split("\n"):
    fl = fix_line2(fix_line(ln))
    if fl != ln:
        _nfix += 1
    fixed_lines.append(fl)
full = "\n".join(fixed_lines)
print(f"shifted lines repaired: {_nfix:,}")

OUT.write_text(full, encoding="utf-8")
print(f"pages: {len(pages)}  chars: {len(full):,}")
print("[written]", OUT)
