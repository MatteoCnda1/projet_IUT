"""Petit générateur de fichiers draw.io (mxGraph) et export PNG/SVG par la CLI drawio."""
import html
import shutil
import subprocess
import xml.etree.ElementTree as ET


class Page:
    def __init__(self, nom, ident):
        self.nom, self.ident = nom, ident
        self.cellules = []
        self.n = 0

    def _id(self, prefixe):
        self.n += 1
        return f"{prefixe}-{self.n}"

    def boite(self, texte, x, y, w, h, style="", ident=None, parent="1"):
        ident = ident or self._id("b")
        c = ET.Element("mxCell", id=ident, value=texte, style=style, vertex="1", parent=parent)
        ET.SubElement(c, "mxGeometry", x=f"{x:g}", y=f"{y:g}", width=f"{w:g}", height=f"{h:g}", **{"as": "geometry"})
        self.cellules.append(c)
        return ident

    def texte(self, texte, x, y, w, h, taille=12, couleur="#101217", gras=False, align="center", extra=""):
        st = (f"text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;"
              f"fontSize={taille};fontColor={couleur};{'fontStyle=1;' if gras else ''}{extra}")
        return self.boite(texte, x, y, w, h, st)

    def lien(self, source, cible, style="", texte="", points=(), ident=None, sx=None, sy=None, tx=None, ty=None, parent="1", pos=None):
        ident = ident or self._id("l")
        st = "endArrow=none;html=1;rounded=0;" + style
        for k, v in (("exitX", sx), ("exitY", sy), ("entryX", tx), ("entryY", ty)):
            if v is not None:
                st += f"{k}={v};"
        if sx is not None or sy is not None:
            st += "exitDx=0;exitDy=0;"
        if tx is not None or ty is not None:
            st += "entryDx=0;entryDy=0;"
        attrs = {"id": ident, "value": texte, "style": st, "edge": "1", "parent": parent}
        if source:
            attrs["source"] = source
        if cible:
            attrs["target"] = cible
        c = ET.Element("mxCell", **attrs)
        g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
        if pos is not None:
            g.set("x", f"{pos:g}")
        if points:
            arr = ET.SubElement(g, "Array", **{"as": "points"})
            for px, py in points:
                ET.SubElement(arr, "mxPoint", x=f"{px:g}", y=f"{py:g}")
        self.cellules.append(c)
        return ident

    def xml(self, largeur=2400, hauteur=1700):
        d = ET.Element("diagram", name=self.nom, id=self.ident)
        m = ET.SubElement(d, "mxGraphModel", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1",
                          fold="1", page="1", pageScale="1", pageWidth=str(largeur), pageHeight=str(hauteur), math="0", shadow="0")
        r = ET.SubElement(m, "root")
        ET.SubElement(r, "mxCell", id="0")
        ET.SubElement(r, "mxCell", id="1", parent="0")
        for c in self.cellules:
            r.append(c)
        return d


def ecrire(pages, chemin, **kw):
    f = ET.Element("mxfile", host="app.diagrams.net")
    for p in pages:
        f.append(p.xml(**kw))
    ET.indent(f)
    chemin.write_text(ET.tostring(f, encoding="unicode"), encoding="utf-8")


def exporter(source, sortie, fmt="png", echelle=1.0, page=None):
    exe = shutil.which("drawio")
    if not exe:
        return False
    cmd = [exe, "-x", "-f", fmt, "-o", str(sortie), "--no-sandbox"]
    if fmt == "png":
        cmd += ["-s", str(echelle), "-b", "10"]
    if page is not None:
        cmd += ["-p", str(page)]
    subprocess.run(cmd + [str(source)], check=True, capture_output=True, timeout=240)
    return True


def h(s):
    """Texte HTML d'une étiquette drawio (html=1) : échappe puis remet les retours à la ligne."""
    return html.escape(s).replace("\n", "<br>")
