"""Modèles bureautiques : rapport et compte rendu (Word), soutenance (PowerPoint).

Nécessite python-docx et python-pptx (pip install python-docx python-pptx).
Polices à installer sur le poste : livrables/communication/polices/ (Space Grotesk, IBM Plex Mono).
Les chiffres des diapositives sont lus dans les JSON du câblage, de l'énergie et du chiffrage.
"""
import json, pathlib
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Mm, RGBColor
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

import marque
from marque import C, AXES, NOM, DOMAINE
from documents import CH  # charte commune (version du dossier, format des nombres)

N = CH.nombre

RACINE = pathlib.Path(__file__).parent.parent
SORTIE = RACINE / "livrables" / "communication"
LOGO = SORTIE / "logo"
SANS, MONO = "Space Grotesk", "IBM Plex Mono"
rgb = lambda h: RGBColor.from_string(h[1:].upper())
prgb = lambda h: PRGB.from_string(h[1:].upper())


# ============================================================== Word
def _police(run_or_style, nom, taille=None, couleur=None, gras=None):
    f = run_or_style.font
    f.name = nom
    rpr = run_or_style.element.get_or_add_rPr() if hasattr(run_or_style.element, "get_or_add_rPr") else run_or_style._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), nom)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rf.attrib.pop(qn(a), None)
    if taille: f.size = Pt(taille)
    if couleur: f.color.rgb = rgb(couleur)
    if gras is not None: f.bold = gras


def _bordure(par, cote="bottom", couleur=C["trait"], taille=4, espace=4):
    ppr = par._p.get_or_add_pPr() if hasattr(par, "_p") else par.element.get_or_add_pPr()
    b = ppr.find(qn("w:pBdr"))
    if b is None:
        b = OxmlElement("w:pBdr"); ppr.append(b)
    e = OxmlElement(f"w:{cote}")
    e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(taille)); e.set(qn("w:space"), str(espace)); e.set(qn("w:color"), couleur[1:])
    b.append(e)


def _cellule(cell, fond=None, bords=None):
    tcpr = cell._tc.get_or_add_tcPr()
    if fond:
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fond[1:]); tcpr.append(sh)
    if bords:
        tb = OxmlElement("w:tcBorders")
        for cote, (coul, sz) in bords.items():
            e = OxmlElement(f"w:{cote}"); e.set(qn("w:val"), "single" if sz else "nil"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), coul[1:])
            tb.append(e)
        tcpr.append(tb)


def _champ(par, instr):
    r = par.add_run()
    for typ, txt in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if typ:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), typ); r._r.append(e)
        elif txt == "1":
            t = OxmlElement("w:t"); t.text = "1"; r._r.append(t)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = f" {txt} "; r._r.append(e)
    return r


def _styles(doc):
    st = doc.styles
    _police(st["Normal"], SANS, 10, C["corps"])
    st["Normal"].paragraph_format.space_after = Pt(5)
    st["Normal"].paragraph_format.line_spacing = 1.25
    for nom, taille, avant in (("Title", 30, 0), ("Heading 1", 17, 18), ("Heading 2", 13, 12), ("Heading 3", 11, 8)):
        s = st[nom]
        _police(s, SANS, taille, C["encre"], True)
        s.paragraph_format.space_before = Pt(avant)
        s.paragraph_format.space_after = Pt(6 if nom != "Title" else 4)
        s.paragraph_format.keep_with_next = True
    _bordure(st["Heading 1"], "bottom", C["trait"], 6, 4)
    for nom in ("Étiquette", "Légende", "Code"):
        if nom not in [s.name for s in st]:
            st.add_style(nom, 1)
    _police(st["Étiquette"], MONO, 7.5, C["emeraude_fonce"], False)
    st["Étiquette"].paragraph_format.space_after = Pt(1)
    st["Étiquette"].font.all_caps = True
    _police(st["Légende"], MONO, 7.5, C["discret"], False)
    st["Légende"].font.all_caps = True
    _police(st["Code"], MONO, 8.5, C["encre"], False)
    st["Code"].paragraph_format.space_after = Pt(0)
    for lst in ("List Bullet", "List Number"):
        _police(st[lst], SANS, 10, C["corps"])


def _tableau(doc, entetes, lignes, largeurs=None):
    t = doc.add_table(rows=1, cols=len(entetes))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(entetes):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h.upper())
        _police(r, MONO, 7, C["secondaire"])
        _cellule(c, C["remplissage"], {"top": (C["trait"], 4), "bottom": (C["trait"], 4), "left": ("#ffffff", 0), "right": ("#ffffff", 0)})
    for ligne in lignes:
        cells = t.add_row().cells
        for i, v in enumerate(ligne):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            _police(r, SANS, 9, C["corps"])
            _cellule(cells[i], None, {"bottom": (C["trait_doux"], 4), "top": ("#ffffff", 0), "left": ("#ffffff", 0), "right": ("#ffffff", 0)})
    if largeurs:
        for row in t.rows:
            for i, w in enumerate(largeurs):
                row.cells[i].width = Mm(w)
    doc.add_paragraph()
    return t


def _encadre(doc, etiquette, texte, couleur=C["emeraude"]):
    t = doc.add_table(rows=1, cols=1)
    c = t.rows[0].cells[0]
    _cellule(c, C["surface"], {"left": (couleur, 18), "top": (C["trait"], 4), "bottom": (C["trait"], 4), "right": (C["trait"], 4)})
    p = c.paragraphs[0]
    r = p.add_run(etiquette.upper() + "\n"); _police(r, MONO, 7.5, C["emeraude_fonce"] if couleur == C["emeraude"] else couleur)
    r = p.add_run(texte); _police(r, SANS, 9.5, C["corps"])
    doc.add_paragraph()


def _entete_pied(section, ref, titre):
    section.different_first_page_header_footer = True
    h = section.header.paragraphs[0]
    h.add_run().add_picture(str(LOGO / "rudylink-infrastructure-couleur.png"), height=Mm(8))
    r = h.add_run(f"\t\t{titre} · {ref}"); _police(r, MONO, 7, C["discret"])
    _bordure(h, "bottom", C["trait"], 4, 6)
    f = section.footer.paragraphs[0]
    r = f.add_run(f"{NOM.upper()}\t\t"); _police(r, MONO, 7, C["discret"])
    _police(_champ(f, "PAGE"), MONO, 7, C["discret"])


def _couverture(doc, ref, titre, sous_titre, meta):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(20)
    sec.top_margin, sec.bottom_margin = Mm(26), Mm(20)
    sec.header_distance, sec.footer_distance = Mm(9), Mm(9)
    p = doc.add_paragraph(); p.add_run().add_picture(str(LOGO / "rudylink-infrastructure-couleur.png"), height=Mm(16))
    for _ in range(9):
        doc.add_paragraph()
    doc.add_paragraph(ref, style="Étiquette")
    doc.add_paragraph(titre, style="Title")
    p = doc.add_paragraph(); r = p.add_run(sous_titre); _police(r, SANS, 13, C["secondaire"])
    for _ in range(5):
        doc.add_paragraph()
    t = doc.add_table(rows=2, cols=len(meta))
    for i, (k, v) in enumerate(meta):
        a, b = t.rows[0].cells[i], t.rows[1].cells[i]
        a.text = b.text = ""
        _police(a.paragraphs[0].add_run(k.upper()), MONO, 7, C["discret"])
        _police(b.paragraphs[0].add_run(v), SANS, 9.5, C["encre"])
        for c in (a, b):
            _cellule(c, None, {"top": (C["encre"] if c is a else "#ffffff", 8 if c is a else 0), "bottom": ("#ffffff", 0), "left": ("#ffffff", 0), "right": ("#ffffff", 0)})
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)
    _entete_pied(sec, ref.split(" ·")[0], titre)


PLAN_RAPPORT = [
    ("Synthèse", [], "Une page pour le décideur : le besoin, la solution retenue, le coût, les points à valider."),
    ("1. Le projet et son contexte", ["02"], "Le client et ses besoins, RudyLink Infrastructure, l'organisation MOA / MOE, la méthode."),
    ("2. Architecture physique", ["04", "10", "14"], "Câblage, locaux techniques, Wi-Fi, énergie et refroidissement."),
    ("3. Architecture réseau", ["03", "05", "06"], "Modèle trois couches, VLAN, plan d'adressage IPv4 / IPv6, configuration du LAN."),
    ("4. Interconnexions", ["07", "08"], "Liaison avec le site jumeau, accès Internet redondé, routage."),
    ("5. Systèmes et services", ["11", "12", "13", "15", "16"], "Annuaire, serveurs, ToIP et vidéo, applications, sauvegarde, supervision."),
    ("6. Sécurité et conformité", ["09", "19"], "Politique de sécurité, matrice de flux, PRA, RGPD, chartes."),
    ("7. Innovation et développement durable", ["17"], "Bâtiment intelligent, Green IT, veille technologique."),
    ("8. Coûts", ["18"], "Investissement, exploitation, coût sur 5 ans, options d'économie."),
    ("9. Conduite du projet", ["01", "21"], "Planning, journal de bord, bilan."),
    ("Conclusion et perspectives", [], ""),
    ("Annexes", [], "Plans, tableaux de brassage, configurations, CdC et CCTP (point 19), abstract en anglais (point 20)."),
]


def rapport_docx(sortie, nrj):
    doc = Document()
    _styles(doc)
    _couverture(doc, "RLI-RAP-001 · vX.Y — JJ/MM/AAAA", "Rapport technique",
                "Réseau du bâtiment Génie des Télécommunications de l'IUT, campus de Luminy, et du site jumeau (Digne ou Gap)",
                [("Client", "IUT Aix-Marseille, R&T"), ("Référence", "RLI-RAP-001"), ("Version", "vX.Y · brouillon"), ("Date", "JJ/MM/AAAA")])
    doc.add_paragraph("Suivi des versions", style="Étiquette")
    _tableau(doc, ["Version", "Date", "Auteur", "Modifications"], [["vX.Y", "JJ/MM/AAAA", "Prénom Nom", "Version du dossier dans laquelle le document change"]], [20, 28, 40, 82])
    doc.add_heading("Sommaire", 1)
    p = doc.add_paragraph(); _champ(p, 'TOC \\o "1-3" \\h \\z \\u')
    p = doc.add_paragraph("Clic droit sur le sommaire puis « Mettre à jour les champs » une fois le rapport rédigé.", style="Légende")
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)
    for titre, pts, consigne in PLAN_RAPPORT:
        doc.add_heading(titre, 1)
        if pts:
            doc.add_paragraph("Points " + " · ".join(pts), style="Étiquette")
        if consigne:
            p = doc.add_paragraph(); r = p.add_run(consigne); r.italic = True; _police(r, SANS, 10, C["discret"])
        if titre.startswith("2."):
            doc.add_heading("2.1 Exemple de mise en forme", 2)
            p = doc.add_paragraph("Texte courant. Une affirmation, un chiffre : la salle serveur consomme ")
            r = p.add_run(f"{N(nrj['salle']['it_typ'] / 1000, 2)} kW"); r.bold = True
            p.add_run(" en fonctionnement normal. Les équipements gardent le nom du schéma : ")
            _police(p.add_run("CL-SW1"), MONO, 9, C["encre"])
            p.add_run(".")
            _tableau(doc, ["Équipement", "Modèle", "Qté", "Total HT"], [["CL-SW1, CL-SW2", "Cisco C9500-16X", "2", "00 000 € HT"]], [45, 65, 20, 40])
            doc.add_paragraph("Tableau 1 · Légende du tableau et source des chiffres", style="Légende")
            _encadre(doc, "Recommandation", "Une recommandation au client, en une ou deux phrases.")
            _encadre(doc, "À valider avec le client", "Hypothèse retenue faute d'information, à confirmer en réunion.", C["alerte"])
            for l in ("! DL-SW1 · passerelle du VLAN 120", "interface Vlan120", " ip address 10.13.120.2 255.255.255.0"):
                p = doc.add_paragraph(l, style="Code")
                p.paragraph_format.left_indent = Mm(4)
            doc.add_paragraph()
    doc.save(sortie)


def compte_rendu_docx(sortie):
    doc = Document()
    _styles(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(18)
    sec.top_margin, sec.bottom_margin = Mm(26), Mm(18)
    sec.header_distance, sec.footer_distance = Mm(9), Mm(8)
    h = sec.header.paragraphs[0]
    h.add_run().add_picture(str(LOGO / "rudylink-infrastructure-couleur.png"), height=Mm(9))
    _police(h.add_run("\t\tCOMPTE RENDU · RLI-CR-nnn"), MONO, 7, C["discret"])
    _bordure(h, "bottom", C["trait"], 4, 6)
    f = sec.footer.paragraphs[0]
    _police(f.add_run(f"{NOM.upper()} · DIFFUSION : PARTICIPANTS, ÉQUIPE PÉDAGOGIQUE\t"), MONO, 7, C["discret"])
    _police(_champ(f, "PAGE"), MONO, 7, C["discret"])
    doc.add_paragraph("Réunion client · point(s) nn", style="Étiquette")
    doc.add_heading("Objet de la réunion", 0)
    _tableau(doc, ["Date", "Lieu", "Type", "Rédacteur", "Référence"],
             [["JJ/MM/AAAA, HHhMM", "IUT Luminy, salle …", "Client / suivi / interne", "Prénom Nom", "RLI-CR-nnn"]], [30, 34, 36, 34, 36])
    doc.add_heading("Participants", 2)
    _tableau(doc, ["Nom", "Rôle", "Côté", "Présent"],
             [["S. Sanchez", "Client (équipe pédagogique)", "MOA", "☐"], ["D. Manoukian", "Client (équipe pédagogique)", "MOA", "☐"],
              ["R. Depeyre", "Client (équipe pédagogique)", "MOA", "☐"], ["Prénom Nom", "Direction de projet", "MOE", "☐"], ["Prénom Nom", "Rôle", "MOE", "☐"]],
             [45, 70, 25, 30])
    doc.add_heading("Ordre du jour", 2)
    for i in ("Point 1", "Point 2", "Questions diverses"):
        doc.add_paragraph(i, style="List Number")
    doc.add_heading("Décisions", 2)
    _tableau(doc, ["N°", "Décision", "Décidé par", "Impact"], [["D1", "…", "MOA", "Points concernés, coût, planning"]], [12, 90, 28, 40])
    doc.add_heading("Actions", 2)
    _tableau(doc, ["N°", "Action", "Responsable", "Échéance", "Statut"], [["A1", "…", "Rôle / nom", "JJ/MM", "À faire"]], [12, 78, 32, 24, 24])
    doc.add_heading("Questions restées ouvertes", 2)
    doc.add_paragraph("…", style="List Bullet")
    _encadre(doc, "Prochaine réunion", "Date, lieu, sujets prévus.")
    doc.save(sortie)


# ============================================================== PowerPoint
W, H = Inches(13.333), Inches(7.5)
M = Inches(0.6)


def _txt(slide, x, y, w, h, texte, taille, couleur, police=SANS, gras=False, caps=False, align=PP_ALIGN.LEFT, ancre=MSO_ANCHOR.TOP, espacement=None):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ancre
    lignes = texte if isinstance(texte, list) else [texte]
    for i, l in enumerate(lignes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if espacement:
            p.space_after = PPt(espacement)
        r = p.add_run()
        r.text = l.upper() if caps else l
        f = r.font
        f.name, f.size, f.bold, f.color.rgb = police, PPt(taille), gras, prgb(couleur)
    return tb


def _rect(slide, x, y, w, h, fond, trait=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.shadow.inherit = False
    if fond:
        s.fill.solid(); s.fill.fore_color.rgb = prgb(fond)
    else:
        s.fill.background()
    if trait:
        s.line.color.rgb = prgb(trait); s.line.width = PPt(0.75)
    else:
        s.line.fill.background()
    return s


def _fond(slide, couleur):
    bg = slide.background.fill
    bg.solid(); bg.fore_color.rgb = prgb(couleur)


def _pied(slide, n, sombre=False):
    c = "#868b94" if sombre else C["discret"]
    trait = C["nuit_trait"] if sombre else C["trait"]
    ln = slide.shapes.add_connector(1, M, H - Inches(0.55), W - M, H - Inches(0.55))
    ln.line.color.rgb = prgb(trait); ln.line.width = PPt(0.75)
    slide.shapes.add_picture(str(LOGO / ("symbole-inverse.png" if sombre else "symbole.png")), M, H - Inches(0.43), height=Inches(0.24))
    _txt(slide, M + Inches(0.36), H - Inches(0.41), Inches(6), Inches(0.25), f"{NOM} · Soutenance SAÉ 5.02", 9, c, MONO, caps=True, ancre=MSO_ANCHOR.MIDDLE)
    _txt(slide, W - M - Inches(1.5), H - Inches(0.41), Inches(1.5), Inches(0.25), f"{n:02d}", 9, c, MONO, align=PP_ALIGN.RIGHT, ancre=MSO_ANCHOR.MIDDLE)


def _titre(slide, etiquette, titre, couleur_etiquette=C["emeraude_fonce"]):
    _txt(slide, M, Inches(0.55), Inches(10), Inches(0.3), etiquette, 11, couleur_etiquette, MONO, caps=True)
    _txt(slide, M, Inches(0.85), W - 2 * M, Inches(0.9), titre, 30, C["encre"], SANS, gras=True)


def soutenance_pptx(sortie, cab, nrj, est):
    eur = lambda v: CH.euros(v, ht=False)
    ge = nrj.get("bet", {}).get("groupe_electrogene")
    opt = next((o for o in nrj.get("optimisations", []) if o["piste"].startswith("Cœur replié")), None)
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    vide = prs.slide_layouts[6]
    n = 0

    def nouvelle(fond=C["papier"]):
        nonlocal n
        n += 1
        s = prs.slides.add_slide(vide)
        _fond(s, fond)
        return s

    # 1. Titre
    s = nouvelle(C["encre"])
    s.shapes.add_picture(str(LOGO / "rudylink-infrastructure-inverse.png"), M - Inches(0.2), Inches(0.4), height=Inches(0.95))
    k = 0.052
    for a, b in marque.LIENS:
        (x1, y1), (x2, y2) = marque.NOEUDS[a], marque.NOEUDS[b]
        ln = s.shapes.add_connector(1, Inches(8.3 + x1 * k), Inches(1.2 + y1 * k), Inches(8.3 + x2 * k), Inches(1.2 + y2 * k))
        ln.line.color.rgb = prgb(C["nuit_trait"]); ln.line.width = PPt(2)
    for nd, (x, y) in marque.NOEUDS.items():
        _rect(s, Inches(8.3 + x * k - 0.28), Inches(1.2 + y * k - 0.28), Inches(0.56), Inches(0.56),
              C["emeraude"] if nd == "c" else "#1f2228", "#4a4f59")
    _txt(s, M, Inches(3.75), Inches(7), Inches(0.3), "Soutenance · JJ/MM/AAAA", 12, "#868b94", MONO, caps=True)
    _txt(s, M, Inches(4.15), Inches(7.3), Inches(1.6), "Le réseau du bâtiment Génie des Télécommunications, à Luminy", 40, C["papier"], SANS, gras=True)
    _txt(s, M, Inches(6.0), Inches(7.3), Inches(0.5), "Proposition de RudyLink Infrastructure à l'IUT Aix-Marseille", 18, "#a4a9b1")
    _pied(s, n, True)

    # 2. Sommaire
    s = nouvelle()
    _titre(s, "Sommaire", "Ce que nous allons vous présenter")
    parties = [("A", "Le bâtiment et son câblage"), ("B", "L'architecture du réseau"), ("D", "Les liaisons avec l'extérieur"),
               ("C", "Les systèmes et services"), ("E", "La sécurité"), ("F", "Le coût")]
    for i, (ax, t) in enumerate(parties):
        y = Inches(2.1 + i * 0.68)
        _rect(s, M, y, Inches(0.09), Inches(0.42), AXES[ax][1])
        _txt(s, M + Inches(0.3), y, Inches(1), Inches(0.42), f"{i + 1:02d}", 18, C["discret"], MONO, ancre=MSO_ANCHOR.MIDDLE)
        _txt(s, M + Inches(1.1), y, Inches(8), Inches(0.42), t, 22, C["encre"], ancre=MSO_ANCHOR.MIDDLE)
        _txt(s, Inches(9.5), y, Inches(3.2), Inches(0.42), AXES[ax][0], 11, AXES[ax][1], MONO, caps=True, ancre=MSO_ANCHOR.MIDDLE)
    _pied(s, n)

    # 3. Intercalaire
    s = nouvelle(C["encre"])
    _txt(s, M, Inches(2.2), Inches(4), Inches(1.6), "01", 96, C["emeraude_nuit"], MONO)
    _txt(s, M, Inches(4.0), Inches(11), Inches(1), "Le bâtiment et son câblage", 40, C["papier"], SANS, gras=True)
    _txt(s, M, Inches(5.0), Inches(11), Inches(0.5), "Architecture physique · points 04, 10 et 14", 14, "#868b94", MONO, caps=True)
    _pied(s, n, True)

    # 4. Contenu
    s = nouvelle()
    _titre(s, "Point 04 · Plan de câblage", "Une prise par poste, du 10 Gb/s pour quinze ans")
    _txt(s, M, Inches(2.1), Inches(7.2), Inches(4), [
        f"{cab['prises']} prises Cat6A, dont {cab['par_type']['wifi']} pour les bornes Wi-Fi, {cab['par_type']['camera']} pour les caméras et {cab['par_type']['badge']} pour les badgeuses",
        f"{len(cab['baies'])} locaux techniques au plus près des salles : aucun lien ne dépasse {str(cab['lien_max_m']).replace('.', ',')} m (norme : 90 m)",
        "Rocades fibre OM4 doublées par deux colonnes montantes différentes",
        "Deux arrivées d'opérateurs par deux façades opposées",
    ], 18, C["corps"], espacement=14)
    _rect(s, Inches(8.4), Inches(2.1), Inches(4.3), Inches(3.9), C["surface"], C["trait"])
    _txt(s, Inches(8.7), Inches(2.35), Inches(3.8), Inches(0.3), "À retenir", 11, C["emeraude_fonce"], MONO, caps=True)
    _txt(s, Inches(8.7), Inches(2.75), Inches(3.8), Inches(3), "Une panne de câble ou de local ne coupe jamais tout un étage.", 22, C["encre"], gras=True)
    _pied(s, n)

    # 5. Chiffres clés
    s = nouvelle()
    _titre(s, "Synthèse", "Le projet en huit chiffres")
    tuiles = [("Câblage", str(cab["prises"]), "prises Cat6A"), ("Wi-Fi", str(cab["par_type"]["wifi"]), "bornes"),
              ("Fibre", f"{N(cab['fibre_m'])} m", "de rocades OM4"), ("Locaux", f"{len(cab['baies'])} + 1", "locaux et salle serveur"),
              ("Énergie", N(nrj["energie"]["pue"], 2), "PUE de la salle serveur"),
              ("Secours", f"{nrj['onduleurs']['autonomie_degrade']} min", f"sur un onduleur, puis groupe {ge['autonomie_h']} h" if ge else "avec un onduleur en panne"),
              ("Investissement", eur(est["capex"]), "HT, aléas compris"), ("Sur 5 ans", eur(est["tco5"]), "HT, exploitation comprise")]
    tw, th, g = Inches(2.85), Inches(1.95), Inches(0.2)
    for i, (lab, val, sous) in enumerate(tuiles):
        x, y = M + (i % 4) * (tw + g), Inches(2.0) + (i // 4) * (th + g)
        _rect(s, x, y, tw, th, C["surface"], C["trait"])
        _txt(s, x + Inches(0.22), y + Inches(0.2), tw, Inches(0.3), lab, 10, C["discret"], MONO, caps=True)
        _txt(s, x + Inches(0.22), y + Inches(0.6), tw - Inches(0.3), Inches(0.7), val, 30, C["emeraude_fonce"] if i >= 6 else C["encre"], gras=True)
        _txt(s, x + Inches(0.22), y + Inches(1.35), tw - Inches(0.3), Inches(0.4), sous, 13, C["secondaire"])
    _pied(s, n)

    # 6. Deux options
    s = nouvelle()
    _titre(s, "Point 03 · Choix à valider", "Trois couches ou cœur replié ?")
    opts = [("Option A · schéma actuel", "Trois couches", ["Distribution par zone, cœur dédié", "Évolutif si le site s'agrandit", "Correspond au cahier des charges"], C["emeraude"]),
            ("Option B", "Cœur replié", ["Distribution et cœur fusionnés", "4 commutateurs en moins, environ " + (N(round(opt["euros"], -2)) if opt else "1 500") + " € HT/an d'électricité économisés", "Suffisant pour un seul bâtiment"], C["trait"])]
    for i, (lab, t, pts, coul) in enumerate(opts):
        x = M + i * Inches(6.15)
        _rect(s, x, Inches(2.0), Inches(5.9), Inches(4.2), C["surface"], coul)
        _txt(s, x + Inches(0.3), Inches(2.25), Inches(5), Inches(0.3), lab, 11, C["emeraude_fonce"] if i == 0 else C["discret"], MONO, caps=True)
        _txt(s, x + Inches(0.3), Inches(2.65), Inches(5.3), Inches(0.6), t, 26, C["encre"], gras=True)
        _txt(s, x + Inches(0.3), Inches(3.5), Inches(5.3), Inches(2.6), ["— " + p for p in pts], 16, C["corps"], espacement=10)
    _pied(s, n)

    # 7. Schéma
    s = nouvelle()
    _titre(s, "Point 04 · Synoptique", "Les rocades entre la salle serveur et les six locaux")
    img = RACINE / "livrables/plan_cablage/synoptique.png"
    if img.exists():
        pic = s.shapes.add_picture(str(img), M, Inches(1.95), height=Inches(4.75))
        if pic.width > W - 2 * M:
            ratio = (W - 2 * M) / pic.width
            pic.width, pic.height = int(pic.width * ratio), int(pic.height * ratio)
    _pied(s, n)

    # 8. Conclusion
    s = nouvelle(C["encre"])
    _txt(s, M, Inches(1.4), Inches(6), Inches(0.3), "Merci de votre attention", 12, "#868b94", MONO, caps=True)
    _txt(s, M, Inches(1.8), Inches(11), Inches(1.4), "Vos questions", 54, C["papier"], SANS, gras=True)
    _txt(s, M, Inches(3.4), Inches(9), Inches(1.5), ["Dossier complet : rapport technique RLI-RAP-001", f"Site du projet : {DOMAINE}"], 18, "#a4a9b1", espacement=8)
    s.shapes.add_picture(str(LOGO / "rudylink-infrastructure-vertical-inverse.png"), Inches(9.4), Inches(3.6), height=Inches(2.6))
    _pied(s, n, True)
    prs.save(sortie)


def produire(rendu):
    for nom, larg in (("rudylink-infrastructure-couleur", 2000), ("rudylink-infrastructure-inverse", 2000), ("rudylink-infrastructure-mono", 2000),
                      ("rudylink-infrastructure-constellation", 2000), ("rudylink-infrastructure-vertical-couleur", 1200),
                      ("rudylink-infrastructure-vertical-inverse", 1200), ("symbole", 512), ("symbole-inverse", 512)):
        rendu.png(LOGO / f"{nom}.svg", LOGO / f"{nom}.png", larg)
    cab = json.loads((RACINE / "livrables/plan_cablage/resume.json").read_text(encoding="utf-8"))
    nrj = json.loads((RACINE / "livrables/energie_refroidissement/resume.json").read_text(encoding="utf-8"))
    est = json.loads((RACINE / "chiffrage/estimation.json").read_text(encoding="utf-8"))
    m = SORTIE / "modeles"
    rapport_docx(m / "modele_rapport.docx", nrj)
    compte_rendu_docx(m / "modele_compte_rendu.docx")
    soutenance_pptx(m / "modele_presentation.pptx", cab, nrj, est)
    return ["modele_rapport.docx", "modele_compte_rendu.docx", "modele_presentation.pptx"]
