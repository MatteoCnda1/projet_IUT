"""Documents imprimables de RudyLink Infrastructure (HTML -> PDF A4).

charte_graphique, plaquette, organisation_projet, modeles/modele_rapport, modeles/signature_mail.
Tous partagent modeles/rudylink-document.css, réutilisable pour les autres livrables.
"""
import json, pathlib
import marque
from marque import C, AXES, NOM, SIGNATURE, CONTACT, DOMAINE

RACINE = pathlib.Path(__file__).parent.parent
SORTIE = RACINE / "livrables" / "communication"
DATE = "12/11/2026"
VERSION = "1.0"

CSS = marque.css_polices("../fonts") + """
/* Charte « Console » de RudyLink : angles droits, traits de 1 px, une seule couleur d'accent. */
:root { --encre:#101217; --papier:#f3f4f6; --surface:#fbfbfc; --remplissage:#eceef1; --trait:#cfd2d8; --trait-doux:#e3e5e9;
  --corps:#2b2f36; --secondaire:#4d525b; --discret:#6d727b; --emeraude:#05893e; --emeraude-fonce:#006925; --emeraude-clair:#b9eec2;
  --sans:'Space Grotesk','Arial',sans-serif; --mono:'IBM Plex Mono','Consolas','Courier New',monospace; }
@page { size: A4; margin: 14mm 15mm 16mm; @bottom-left { content: "RudyLink Infrastructure"; font: 500 7pt var(--mono); color: #6d727b; letter-spacing: .06em; text-transform: uppercase; }
  @bottom-right { content: counter(page) " / " counter(pages); font: 500 7pt var(--mono); color: #6d727b; } }
@page couverture { margin: 0; @bottom-left { content: none } @bottom-right { content: none } }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font: 400 9.3pt/1.5 var(--sans); color: var(--corps); background: #fff; font-variant-numeric: tabular-nums; }
h1, h2, h3 { color: var(--encre); font-weight: 600; text-wrap: balance; margin: 0; }
h1 { font-size: 24pt; line-height: 1.1; letter-spacing: -.02em; }
h2 { font-size: 14.5pt; line-height: 1.25; letter-spacing: -.01em; padding-bottom: 2mm; border-bottom: 1px solid var(--trait); margin: 6mm 0 2.5mm; }
h3 { font-size: 10.5pt; margin: 4.5mm 0 1.5mm; }
p { margin: 1.4mm 0; max-width: 165mm; } ul, ol { margin: 1mm 0 2mm; padding-left: 5mm; } li { margin: .7mm 0; }
b, strong { color: var(--encre); font-weight: 600; }
code, .mono { font-family: var(--mono); font-size: .92em; }
code { background: var(--remplissage); padding: 0 1.2mm; }
.label { font: 500 6.8pt/1.2 var(--mono); letter-spacing: .07em; text-transform: uppercase; color: var(--discret); }
.label.accent { color: var(--emeraude-fonce); }
.chapo { font-size: 11pt; line-height: 1.45; color: var(--secondaire); max-width: 160mm; margin: 2mm 0 4mm; }
.saut { break-before: page; }
.garde { break-inside: avoid; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; font-size: 8.4pt; }
th { text-align: left; font: 500 6.8pt var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--secondaire);
  background: var(--remplissage); border-top: 1px solid var(--trait); border-bottom: 1px solid var(--trait); padding: 1.6mm 2mm; }
td { padding: 1.5mm 2mm; border-bottom: 1px solid var(--trait-doux); vertical-align: top; }
tr { break-inside: avoid; } td.n, th.n { text-align: right; white-space: nowrap; } td.c, th.c { text-align: center; }
.grille { display: grid; gap: 3mm; } .g2 { grid-template-columns: 1fr 1fr; } .g3 { grid-template-columns: repeat(3, 1fr); } .g4 { grid-template-columns: repeat(4, 1fr); }
.bloc { border: 1px solid var(--trait); background: var(--surface); padding: 3mm 3.5mm; break-inside: avoid; }
.bloc > .label { display: block; margin-bottom: 1.5mm; }
.bloc h3 { margin-top: 0; }
.chiffre { font: 600 17pt/1.1 var(--sans); color: var(--encre); letter-spacing: -.02em; display: block; margin: 1mm 0 .5mm; }
.note { border: 1px solid var(--trait); border-left: 3px solid var(--emeraude); background: var(--surface); padding: 2.5mm 3.5mm; margin: 3mm 0; break-inside: avoid; }
.note.alerte { border-left-color: #ab7400; }
.pastille { display: inline-block; font: 500 6.6pt var(--mono); letter-spacing: .05em; text-transform: uppercase; padding: .4mm 1.6mm; border: 1px solid currentColor; }
.oui { color: var(--emeraude-fonce); } .non { color: #c13c3b; }
.entete { display: flex; justify-content: space-between; align-items: center; padding-bottom: 3mm; border-bottom: 1px solid var(--trait); margin-bottom: 6mm; }
.entete img { height: 11mm; }
.entete .label { text-align: right; }
.cartouche { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--trait); margin: 4mm 0; }
.cartouche div { padding: 2mm 3mm; border-right: 1px solid var(--trait-doux); } .cartouche div:last-child { border-right: 0; }
.cartouche b { display: block; font-weight: 500; font-size: 9pt; margin-top: .6mm; }
/* Couverture : pleine page, encre */
.couverture { page: couverture; height: 297mm; background: var(--encre); color: var(--papier); padding: 22mm 20mm; display: flex; flex-direction: column; position: relative; overflow: hidden; }
.couverture h1 { color: var(--papier); font-size: 40pt; font-weight: 500; letter-spacing: -.03em; line-height: 1; margin-top: auto; }
.couverture .chapo { color: #a4a9b1; font-size: 12.5pt; }
.couverture .label { color: #868b94; }
.couverture .bas { display: flex; justify-content: space-between; border-top: 1px solid #353941; padding-top: 4mm; margin-top: 14mm; }
.couverture .logo { height: 17mm; align-self: flex-start; }
.couverture .trame { position: absolute; right: -10mm; top: 52mm; width: 130mm; opacity: .9; }
"""


def contraste(a, b):
    def lum(h):
        r, g, bb = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
        return .2126 * f(r) + .7152 * f(g) + .0722 * f(bb)
    l1, l2 = sorted((lum(a), lum(b)), reverse=True)
    return (l1 + .05) / (l2 + .05)


def page(titre, corps, css_rel="modeles/rudylink-document.css"):
    return (f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{titre}</title>"
            f"<link rel='stylesheet' href='{css_rel}'></head><body>{corps}</body></html>")


def entete(ref, titre, logo="logo/rudylink-infrastructure-couleur.svg"):
    return (f"<div class='entete'><img src='{logo}' alt='{NOM}'>"
            f"<div class='label'>{titre}<br>{ref} · v{VERSION} · {DATE}</div></div>")


def trame(largeur=520, hauteur=420):
    """Motif de couverture : la topologie du symbole, agrandie et répétée sur trois couches."""
    k = 4.2
    out = [f"<svg class='trame' viewBox='0 0 {largeur} {hauteur}' xmlns='http://www.w3.org/2000/svg'>"]
    for a, b in marque.LIENS:
        (x1, y1), (x2, y2) = marque.NOEUDS[a], marque.NOEUDS[b]
        out.append(f"<line x1='{x1 * k}' y1='{y1 * k}' x2='{x2 * k}' y2='{y2 * k}' stroke='#353941' stroke-width='2'/>")
    for n, (x, y) in marque.NOEUDS.items():
        col = C["emeraude"] if n == "c" else "#1f2228"
        out.append(f"<rect x='{x * k - 22}' y='{y * k - 22}' width='44' height='44' fill='{col}' stroke='#4a4f59' stroke-width='1'/>")
    labels = {"c": "CŒUR", "d1": "DISTRIBUTION", "a1": "ACCÈS"}
    for n, t in labels.items():
        x, y = marque.NOEUDS[n]
        out.append(f"<text x='{x * k + 30}' y='{y * k - 26}' fill='#868b94' font-family='IBM Plex Mono' font-size='11' letter-spacing='1'>{t}</text>")
    out.append("</svg>")
    return "".join(out)


def couverture(titre, sous_titre, ref):
    return f"""<section class='couverture'>
<img class='logo' src='logo/rudylink-infrastructure-inverse.svg' alt='{NOM}' style='margin:-24px'>
{trame()}
<div class='label' style='margin-top:auto;margin-bottom:5mm'>{ref} · version {VERSION} · {DATE}</div>
<h1 style='margin-top:0'>{titre}</h1>
<p class='chapo'>{sous_titre}</p>
<div class='bas'><span class='label'>Projet SAÉ 5.02 · IUT Aix-Marseille, R&amp;T Luminy</span><span class='label'>{DOMAINE}</span></div>
</section>"""


# ---------------------------------------------------------------- charte graphique
def nuancier():
    lignes = [
        ("Encre", C["encre"], "Texte principal, fond du symbole, couvertures"),
        ("Papier", C["papier"], "Fond des pages web, nœuds du symbole"),
        ("Surface", C["surface"], "Encadrés, cartes, tableaux"),
        ("Trait", C["trait"], "Filets de 1 px, bordures"),
        ("Corps", C["corps"], "Texte courant"),
        ("Discret", C["discret"], "Légendes, étiquettes, pieds de page"),
        ("Émeraude", C["emeraude"], "Accent unique : cœur du symbole, liens, chiffre clé"),
        ("Émeraude foncé", C["emeraude_fonce"], "Accent sous forme de texte sur fond clair"),
        ("Émeraude nuit", C["emeraude_nuit"], "Accent sur fond sombre"),
        ("Vert Constellation", C["constellation"], "Rappel du portail rudylink.eu (variante de logo)"),
    ]
    rows = []
    for nom, h, usage in lignes:
        r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
        sur_blanc = contraste(h, "#ffffff")
        rows.append(f"<tr><td><span style='display:inline-block;width:8mm;height:4mm;background:{h};border:1px solid {C['trait']};vertical-align:middle'></span></td>"
                    f"<td style='white-space:nowrap'><b>{nom}</b></td><td class='mono'>{h.upper()}</td><td class='mono' style='white-space:nowrap'>{r}&nbsp;{g}&nbsp;{b}</td>"
                    f"<td class='n'>{sur_blanc:.1f}:1</td><td>{usage}</td></tr>")
    return ("<table><tr><th></th><th>Nom</th><th>HEX</th><th>RVB</th><th class='n'>Contraste / blanc</th><th>Usage</th></tr>"
            + "".join(rows) + "</table>")


def charte():
    ax = "".join(f"<div style='display:flex;gap:2mm;align-items:center;border:1px solid {C['trait_doux']};padding:1.5mm 2mm'>"
                 f"<span style='width:5mm;height:5mm;background:{c};flex:none'></span><span class='mono' style='color:{c};font-weight:600'>{k}</span>"
                 f"<span style='flex:1'>{n}</span><span class='mono' style='color:#6d727b'>{c.upper()}</span></div>"
                 for k, (n, c) in AXES.items())
    e_txt = contraste(C["emeraude_fonce"], "#ffffff")
    corps = couverture("Charte graphique", f"Identité visuelle et règles de communication de {NOM}, société de conseil réseau du projet.", "RLI-COM-001") + f"""
{entete("RLI-COM-001", "Charte graphique")}
<span class='label accent'>1 · La société</span>
<h1 style='margin:2mm 0'>{NOM}</h1>
<p class='chapo'>Société de conseil et d'ingénierie des réseaux. Pour le projet, elle joue la maîtrise d'œuvre du réseau du bâtiment R&amp;T de Luminy et de son site jumeau.</p>
<h2>D'où vient le nom</h2>
<p><b>RudyLink existe vraiment.</b> C'est la micro-entreprise de Mattéo Canada, immatriculée le 20 octobre 2026 (activité 62.01Z, programmation informatique). Elle publie déjà deux services sous <span class='mono'>rudylink.eu</span> : <i>RudyLink Nutrition</i> (01) et <i>RudyLink Knowledge</i> (02), une base de fiches de cours réseaux et cybersécurité.</p>
<p>Pour le projet, nous imaginons sa troisième branche : <b>RudyLink Infrastructure</b> (03), le pôle de conseil réseau. Le nom se prête au métier, puisque <i>link</i> désigne un lien réseau. L'identité s'appuie sur une charte qui existe déjà et que tout le groupe peut consulter en ligne, et le nom de domaine nous appartient.</p>
<div class='grille g2'>
<div class='bloc'><span class='label accent'>Réel</span><ul style='margin:0'><li>Le nom RudyLink et le domaine <span class='mono'>rudylink.eu</span></li><li>La charte « Console » (typographies, couleurs, règles de mise en page)</li><li>Les services Nutrition et Knowledge</li></ul></div>
<div class='bloc'><span class='label'>Fictif (jeu de rôle SAÉ 5.02)</span><ul style='margin:0'><li>La branche Infrastructure, son équipe et son offre</li><li>Ses références commerciales et ses tarifs</li><li>Aucune existence juridique : pas de SIREN, pas de contrat avec l'université</li></ul></div>
</div>
<h2>Mission et positionnement</h2>
<p class='chapo' style='color:var(--encre)'>« Nous concevons des réseaux d'établissement qui tiennent quinze ans : documentés, sécurisés selon les guides de l'ANSSI et chiffrés au plus juste. »</p>
<div class='grille g4'>
<div class='bloc'><span class='label'>Valeur 1</span><h3>Mesurer avant d'affirmer</h3><p>Chaque choix est chiffré et vérifiable : distances de câble, puissances, autonomie, coût sur 5 ans.</p></div>
<div class='bloc'><span class='label'>Valeur 2</span><h3>Documenter pour le client</h3><p>Le client doit pouvoir rédiger ses futurs cahiers des charges et CCTP à partir de nos livrables.</p></div>
<div class='bloc'><span class='label'>Valeur 3</span><h3>Sécurité dès la conception</h3><p>Double barrière de pare-feu, 802.1X, administration par bastion, en suivant les guides de l'ANSSI.</p></div>
<div class='bloc'><span class='label'>Valeur 4</span><h3>Sobriété</h3><p>Dimensionner sans excès, mesurer la consommation (PUE) et proposer les économies chiffrées.</p></div>
</div>
<h3>Ce qui nous distingue des autres groupes</h3>
<ul><li><b>Des plans calculés, pas dessinés à la main.</b> Le plan de câblage, l'étude Wi-Fi et le bilan énergétique sont produits par des scripts à partir des plans du bâtiment : une modification se répercute partout.</li>
<li><b>Un chiffrage complet et un suivi ouvert</b> : investissement, coûts annuels et coût sur 5 ans ; roadmap, dépôt Git et journal consultables par l'équipe pédagogique.</li></ul>

<section class='saut'>
<span class='label accent'>2 · Logo</span>
<h2 style='margin-top:2mm'>Le symbole : un réseau en trois couches</h2>
<div class='grille' style='grid-template-columns:52mm 1fr;align-items:start'>
<img src='logo/symbole.svg' style='width:52mm' alt='Symbole'>
<div><p>Le symbole dessine la hiérarchie que nous défendons dans le projet : <b>un cœur</b> (en émeraude), <b>deux équipements de distribution</b> reliés entre eux, <b>trois commutateurs d'accès</b>. L'accès central est raccordé aux deux distributions : c'est la redondance.</p>
<p>Il se construit sur une grille de 96 unités : nœuds carrés de 12, liens de 3, marges de 12. Angles droits partout, aucun arrondi, aucune ombre.</p>
<p>Le mot-symbole reprend la marque mère en <b>Space Grotesk 600</b> ; la branche est écrite en <b>IBM Plex Mono</b> capitales, comme les étiquettes de la charte.</p></div></div>
<h3>Déclinaisons</h3>
<div class='grille g2'>
<div class='bloc'><img src='logo/rudylink-infrastructure-couleur.svg' style='height:15mm'><p class='label' style='margin-top:2mm'>Couleur · fond clair · usage par défaut</p></div>
<div class='bloc' style='background:{C['encre']};border-color:{C['encre']}'><img src='logo/rudylink-infrastructure-inverse.svg' style='height:20mm;margin:-3.4mm'><p class='label' style='margin-top:2mm;color:#868b94'>Inverse · fond encre · couvertures, slides</p></div>
<div class='bloc' style='background:{C['constellation']};border-color:{C['constellation']}'><img src='logo/rudylink-infrastructure-constellation.svg' style='height:20mm;margin:-3.4mm'><p class='label' style='margin-top:2mm;color:#9fc7ad'>Constellation · rappel du portail rudylink.eu</p></div>
<div class='bloc'><img src='logo/rudylink-infrastructure-mono.svg' style='height:15mm'><p class='label' style='margin-top:2mm'>Monochrome · impression noir et blanc, tampon</p></div>
</div>
<p>Une version verticale (<span class='mono'>logo/rudylink-infrastructure-vertical-*.svg</span>) sert aux formats carrés : avatar, page de garde centrée, affiche. Le symbole seul sert d'icône (favicon, réseaux sociaux, puce de diapositive).</p>
<div class='grille g2'>
<div><h3>Zone de protection et tailles minimales</h3>
<ul><li>Espace libre autour du logo : <b>un quart de la hauteur du symbole</b> sur chaque côté.</li>
<li>Logo horizontal : <b>35 mm</b> de large au minimum en impression, <b>140 px</b> à l'écran.</li>
<li>Symbole seul : <b>8 mm</b> ou <b>16 px</b> au minimum.</li>
<li>Fichiers vectoriels (SVG) partout où c'est possible ; PNG à 2000 px fournis pour Word et PowerPoint.</li></ul></div>
<div><h3>À ne pas faire</h3>
<ul><li>Déformer, incliner ou arrondir les angles du symbole.</li>
<li>Changer la couleur du cœur ou colorer les autres nœuds.</li>
<li>Ajouter une ombre, un dégradé ou un contour.</li>
<li>Réécrire « RudyLink » dans une autre police : utiliser les fichiers fournis.</li>
<li>Poser le logo couleur sur une photo chargée ou un fond moyen : passer en inverse.</li></ul></div>
</div>
</section>

<section class='saut'>
<span class='label accent'>3 · Couleurs</span>
<h2 style='margin-top:2mm'>Une palette de neutres et un seul accent</h2>
<p>Les couleurs viennent de la charte « Console » de RudyLink, définies en OKLCH puis converties pour l'impression et la bureautique. Règle de dosage : <b>neutres sur l'essentiel de la page, encre pour le texte et les titres, émeraude en touche</b> (un lien, un chiffre clé, le cœur du symbole). L'émeraude n'est jamais une couleur de fond étendue.</p>
{nuancier()}
<p class='label'>Contraste calculé selon WCAG 2.1. Le texte en émeraude utilise la variante foncée ({e_txt:.1f}:1 sur blanc, niveau AAA) ; l'émeraude standard est réservé aux aplats, aux traits et au texte de grande taille.</p>
<h3>Couleurs des axes du cahier des charges</h3>
<p>Dans la roadmap, le rapport et les schémas, chaque axe garde sa teinte. Ces couleurs servent aux pastilles, aux légendes et aux traits de schéma, jamais au texte courant.</p>
<div class='grille g3' style='gap:2mm;font-size:8.3pt'>{ax}</div><p class='label'>Toutes ces teintes dépassent 4,5:1 sur blanc.</p>
<h3>Couleurs d'état</h3>
<p><span class='pastille oui'>Validé</span> <span class='mono'>#05893E</span> &nbsp; <span class='pastille' style='color:#ab7400'>À valider</span> <span class='mono'>#AB7400</span> &nbsp; <span class='pastille non'>Bloquant</span> <span class='mono'>#C13C3B</span> &nbsp; <span class='pastille' style='color:#0079b5'>Information</span> <span class='mono'>#0079B5</span></p>
</section>

<section class='saut'>
<span class='label accent'>4 · Typographie</span>
<h2 style='margin-top:2mm'>Deux familles, deux rôles</h2>
<div class='grille g2'>
<div class='bloc'><span class='label'>Titres et texte</span><div style='font:500 30pt/1 var(--sans);color:var(--encre);letter-spacing:-.02em;margin:2mm 0'>Space Grotesk</div><p>Grotesque géométrique, lisible en petit corps. Graisses 400 (texte), 500 (intertitres), 600 (titres).</p><p style='font-size:12pt;color:var(--encre)'>Aa Bb Cc 0123456789 éèàçœ €</p></div>
<div class='bloc'><span class='label'>Données et étiquettes</span><div style='font:500 25pt/1.1 var(--mono);color:var(--encre);margin:2mm 0'>IBM Plex Mono</div><p>Chasse fixe pour tout ce qui se lit comme une donnée : noms d'équipements, adresses IP, VLAN, références, étiquettes.</p><p class='mono' style='font-size:10pt;color:var(--encre)'>EL-FGT1 · 10.13.20.0/24 · VLAN 120</p></div>
</div>
<table><tr><th>Niveau</th><th>Police</th><th class='n'>Document</th><th class='n'>Diapositive</th><th class='n'>Web</th><th>Règle</th></tr>
<tr><td>Titre de document</td><td>Space Grotesk 600</td><td class='n'>24 pt</td><td class='n'>40 pt</td><td class='n'>40–56 px</td><td>Interlettrage −2 %</td></tr>
<tr><td>Titre de partie</td><td>Space Grotesk 600</td><td class='n'>14,5 pt</td><td class='n'>28 pt</td><td class='n'>24 px</td><td>Filet de 1 px dessous</td></tr>
<tr><td>Intertitre</td><td>Space Grotesk 600</td><td class='n'>10,5 pt</td><td class='n'>20 pt</td><td class='n'>17 px</td><td>—</td></tr>
<tr><td>Texte courant</td><td>Space Grotesk 400</td><td class='n'>9,5 pt</td><td class='n'>16–18 pt</td><td class='n'>16 px</td><td>Interligne 1,5 ; 70 signes par ligne au plus</td></tr>
<tr><td>Étiquette</td><td>IBM Plex Mono 500</td><td class='n'>7 pt</td><td class='n'>11 pt</td><td class='n'>11 px</td><td>Capitales, interlettrage +6 %</td></tr>
<tr><td>Donnée technique</td><td>IBM Plex Mono 400</td><td class='n'>0,92 em</td><td class='n'>0,92 em</td><td class='n'>0,92 em</td><td>Dans le texte : <code>DL-SW1</code></td></tr></table>
<ul><li><b>Capitales réservées à la mono</b> : jamais de titre tout en majuscules en Space Grotesk.</li>
<li><b>Chiffres tabulaires</b> dans les tableaux, montants alignés à droite.</li>
<li>Remplacement si les polices ne sont pas installées : <b>Arial</b> et <b>Consolas</b>. Les deux familles sont sous licence libre (SIL Open Font License) et fournies dans <span class='mono'>polices/</span>.</li></ul>

</section>
<section class='saut'>
<span class='label accent'>5 · Éléments graphiques</span>
<h2 style='margin-top:2mm'>Les règles « Console »</h2>
<div class='grille g3'>
<div class='bloc'><span class='label'>Règle 1</span><h3>Angles droits</h3><p>Aucun arrondi sur les encadrés, boutons, tableaux et images.</p></div>
<div class='bloc'><span class='label'>Règle 2</span><h3>Filets de 1 px</h3><p>Les blocs se séparent par un trait fin, pas par une ombre.</p></div>
<div class='bloc'><span class='label'>Règle 3</span><h3>Aplats opaques</h3><p>Pas de dégradé, pas de flou, pas d'effet de verre.</p></div>
<div class='bloc'><span class='label'>Règle 4</span><h3>Étiquettes en mono</h3><p>Petites capitales espacées au-dessus des titres : <span class='label'>POINT 04 · CÂBLAGE</span></p></div>
<div class='bloc'><span class='label'>Règle 5</span><h3>Code toujours sombre</h3><p>Les extraits de configuration restent sur fond encre, quel que soit le thème.</p></div>
<div class='bloc'><span class='label'>Règle 6</span><h3>Schémas sobres</h3><p>Nœuds rectangulaires, liens droits, couleur d'axe sur la légende, émeraude pour le cœur.</p></div>
</div>
<div style='background:{C['encre']};color:#e3e5e9;font:400 8.2pt/1.6 var(--mono);padding:3mm 4mm;margin-top:3mm'>
<span style='color:#868b94'>! DL-SW1 · passerelle du VLAN 120</span><br>interface Vlan120<br>&nbsp;description ETUDIANTS-N1<br>&nbsp;ip address 10.13.120.2 255.255.255.0<br>&nbsp;<span style='color:{C['emeraude_nuit']}'>standby 120 ip 10.13.120.1</span></div>
<p class='label' style='margin-top:1.5mm'>Exemple de bloc de configuration (adresses données à titre d'illustration, le plan d'adressage est traité au point 05).</p>
</section>

<section class='saut'>
<span class='label accent'>6 · Rédaction</span>
<h2 style='margin-top:2mm'>Le ton de RudyLink Infrastructure</h2>
<p>Nous écrivons comme un consultant qui doit être compris par un directeur de composante autant que par un administrateur réseau : clair, précis, sans jargon gratuit.</p>
<table><tr><th style='width:30%'>Règle</th><th>Écrire</th><th>Éviter</th></tr>
<tr><td>Vouvoyer le client, parler au « nous » de l'équipe</td><td>Nous vous proposons deux onduleurs en voies A et B.</td><td>Il est proposé de mettre en place une solution d'onduleurs.</td></tr>
<tr><td>Chiffrer chaque affirmation</td><td>24 min d'autonomie si un onduleur tombe en panne.</td><td>Une autonomie confortable.</td></tr>
<tr><td>Expliquer un sigle à sa première apparition</td><td>PUE (rapport entre l'énergie de la salle et celle des équipements)</td><td>Un PUE de 1,34.</td></tr>
<tr><td>Dire ce qui reste à valider</td><td>À valider avec le client : passages en vide sanitaire.</td><td>Passer sous silence une hypothèse.</td></tr>
<tr><td>Phrases courtes, voix active</td><td>La fibre monte par deux colonnes.</td><td>Il a été procédé à la mise en place de deux cheminements verticaux.</td></tr></table>
<h3>Conventions d'écriture</h3>
<div class='grille g2'>
<ul><li>Nombres : <span class='mono'>582 951 €</span> (espace insécable), virgule décimale <span class='mono'>4,2 kW</span>.</li>
<li>Montants : toujours préciser <b>HT</b> ou <b>TTC</b>.</li>
<li>Dates : <span class='mono'>12/11/2026</span> ou « 12 novembre 2026 ».</li>
<li>Équipements : nom du schéma en mono (<code>CL-SW1</code>), puis le modèle.</li></ul>
<ul><li>Références : <span class='mono'>RLI-&lt;TYPE&gt;-&lt;n°&gt;</span> : COM communication, RAP rapport, CR compte rendu, ETU étude, CCTP.</li>
<li>Fichiers : <span class='mono'>RLI-RAP-001_rapport-technique_v1.2.pdf</span>.</li>
<li>Versions : <span class='mono'>0.x</span> brouillon, <span class='mono'>1.0</span> première version livrée au client.</li>
<li>Signature : prénom, nom, rôle, puis le bloc RudyLink Infrastructure.</li></ul>
</div>

<span class='label accent' style='display:block;margin-top:7mm'>7 · Applications</span>
<h2 style='margin-top:2mm'>Les supports et leurs modèles</h2>
<table><tr><th>Support</th><th>Fichier modèle</th><th>Points clés</th></tr>
<tr><td>Rapport technique (30 p.)</td><td class='mono'>modeles/modele_rapport.docx · .html</td><td>Couverture encre, cartouche de suivi, styles de titres, pied de page numéroté</td></tr>
<tr><td>Présentation orale</td><td class='mono'>modeles/modele_presentation.pptx</td><td>Titre, intercalaire, contenu, chiffres clés, deux colonnes, conclusion</td></tr>
<tr><td>Compte rendu de réunion</td><td class='mono'>modeles/modele_compte_rendu.docx</td><td>Participants, décisions, actions avec responsable et échéance</td></tr>
<tr><td>Site vitrine</td><td class='mono'>livrables/site_web/</td><td>Pages HTML simples aux couleurs et polices de la charte, journal de bord intégré</td></tr>
<tr><td>Courriel</td><td class='mono'>modeles/signature_mail.html</td><td>Signature à coller dans le client de messagerie</td></tr>
<tr><td>Feuille de style</td><td class='mono'>modeles/rudylink-document.css</td><td>Pour tout document HTML imprimé en PDF (comme les livrables des points 04 et 14)</td></tr></table>
</section>"""
    return page("Charte graphique · RudyLink Infrastructure", corps)


# ---------------------------------------------------------------- plaquette commerciale
def plaquette(cab, nrj, est):
    eur = lambda v: f"{v:,.0f}".replace(",", " ") + " €"
    corps = f"""{entete("RLI-COM-002", "Présentation de la société")}
<span class='label accent'>Conseil et ingénierie des réseaux d'établissement</span>
<h1 style='font-size:30pt;margin:2mm 0 3mm;max-width:150mm'>Des réseaux conçus pour durer quinze ans.</h1>
<p class='chapo'>{NOM} accompagne les établissements d'enseignement et les collectivités, du relevé des plans jusqu'au cahier des clauses techniques. Nous livrons des choix argumentés, chiffrés et documentés.</p>
<h2>Notre offre</h2>
<div class='grille g2'>
<div class='bloc'><span class='label' style='color:{AXES['B'][1]}'>Architecture</span><h3>Audit et conception</h3><p>Réseau hiérarchique accès, distribution et cœur ; plan d'adressage IPv4 et IPv6 ; interconnexion des sites et accès Internet redondé.</p></div>
<div class='bloc'><span class='label' style='color:{AXES['A'][1]}'>Infrastructure physique</span><h3>Câblage, Wi-Fi et locaux techniques</h3><p>Plan de câblage Cat6A et fibre, étude de couverture Wi-Fi, alimentation secourue, climatisation et bilan énergétique.</p></div>
<div class='bloc'><span class='label' style='color:{AXES['E'][1]}'>Sécurité</span><h3>Sécurité et conformité</h3><p>Double barrière de pare-feu, authentification 802.1X, bastion d'administration, RGPD et chartes, en suivant les guides de l'ANSSI.</p></div>
<div class='bloc'><span class='label' style='color:{AXES['C'][1]}'>Exploitation</span><h3>Services, supervision et sauvegarde</h3><p>Annuaire, téléphonie IP, supervision, sauvegarde et plan de reprise d'activité ; dossier d'exploitation remis au client.</p></div>
</div>
<h2>Notre méthode</h2>
<table><tr><th style='width:16%'>Étape</th><th>Ce que nous faisons</th><th style='width:30%'>Ce que vous recevez</th></tr>
<tr><td><b>1. Écouter</b></td><td>Réunions de cadrage, recueil des usages et des contraintes du site.</td><td>Note de cadrage validée</td></tr>
<tr><td><b>2. Relever</b></td><td>Lecture des plans, inventaire des salles, des locaux techniques et des passages de câbles.</td><td>Inventaire des salles et des prises</td></tr>
<tr><td><b>3. Concevoir</b></td><td>Architecture, câblage, sécurité, services, calculés par nos outils à partir des plans.</td><td>Plans, schémas, dossier technique</td></tr>
<tr><td><b>4. Chiffrer</b></td><td>Investissement, coûts annuels, coût total sur 5 ans et options d'économie.</td><td>Estimation détaillée et pistes d'optimisation</td></tr>
<tr><td><b>5. Transmettre</b></td><td>Rédaction du cahier des charges et du CCTP pour vos consultations.</td><td>CdC, CCTP, maquette de démonstration</td></tr></table>

<section class='saut'>
{entete("RLI-COM-002", "Présentation de la société")}
<span class='label accent'>Référence en cours</span>
<h2 style='margin-top:2mm'>Le bâtiment Génie des Télécommunications, IUT de Luminy</h2>
<p>Réseau complet d'un bâtiment de trois niveaux, relié à un site jumeau à Digne ou Gap. Premiers résultats remis au client :</p>
<div class='grille g4' style='margin:4mm 0'>
<div class='bloc'><span class='label'>Câblage</span><span class='chiffre'>{cab['prises']}</span>prises Cat6A 10 Gb/s</div>
<div class='bloc'><span class='label'>Wi-Fi</span><span class='chiffre'>{cab['par_type']['wifi']}</span>bornes placées par étude de couverture</div>
<div class='bloc'><span class='label'>Locaux</span><span class='chiffre'>{len(cab['baies'])} + 1</span>locaux techniques et salle serveur</div>
<div class='bloc'><span class='label'>Fibre</span><span class='chiffre'>{cab['fibre_m']} m</span>de rocades OM4 doublées</div>
<div class='bloc'><span class='label'>Énergie</span><span class='chiffre'>{str(nrj['energie']['pue']).replace('.', ',')}</span>PUE visé de la salle serveur</div>
<div class='bloc'><span class='label'>Secours</span><span class='chiffre'>{nrj['onduleurs']['autonomie_degrade']} min</span>d'autonomie avec un onduleur en panne</div>
<div class='bloc'><span class='label'>Investissement</span><span class='chiffre'>{eur(est['capex'])}</span>HT, aléas de 10 % compris</div>
<div class='bloc'><span class='label'>Sur 5 ans</span><span class='chiffre'>{eur(est['tco5'])}</span>HT, exploitation comprise</div>
</div>
<h3>Les choix structurants</h3>
<ul><li>Architecture en trois couches avec cœur et distribution redondés (StackWise Virtual).</li>
<li>Double barrière de sécurité : FortiGate en bordure, Stormshield en interne, DMZ pour les services publiés.</li>
<li>Double accès Internet par deux opérateurs arrivant par deux façades opposées.</li>
<li>Salle serveur alimentée par deux onduleurs indépendants, climatisation doublée, allée froide.</li></ul>
<h2>L'équipe</h2>
<p>RudyLink Infrastructure est la maîtrise d'œuvre du projet. Chaque pôle a un responsable ; la direction de projet est l'interlocuteur unique du client. L'organisation complète et la répartition des 21 points sont décrites dans le document <span class='mono'>RLI-COM-003</span>.</p>
<p><b>Équipe</b> : {', '.join(f'{n} ({t.lower()})' if r else n for n, t, r in EQUIPE)}.</p>
<table><tr><th>Pôle</th><th>Périmètre</th></tr>
<tr><td><b>Direction de projet</b></td><td>Planning, relation client, chiffrage, qualité des livrables</td></tr>
<tr><td><b>Architecture réseau</b></td><td>LAN, adressage, WAN, Internet, Wi-Fi, maquette</td></tr>
<tr><td><b>Infrastructure physique</b></td><td>Câblage, locaux techniques, énergie, bâtiment intelligent</td></tr>
<tr><td><b>Systèmes et services</b></td><td>Serveurs, ToIP, applications, sauvegarde, supervision</td></tr>
<tr><td><b>Sécurité et conformité</b></td><td>Politique de sécurité, juridique, chartes, CCTP</td></tr></table>
<div class='note' style='margin-top:6mm'><span class='label accent'>Contact</span><br><b>{NOM}</b> · {SIGNATURE}<br><span class='mono'>{DOMAINE}</span> · <span class='mono'>{CONTACT}</span></div>
<p class='label' style='margin-top:4mm'>Société fictive créée pour la SAÉ 5.02 (BUT R&amp;T, IUT Aix-Marseille). Le nom est emprunté à la micro-entreprise RudyLink ; la branche Infrastructure n'a pas d'existence juridique.</p>
</section>"""
    return page("Présentation · RudyLink Infrastructure", corps)


# ---------------------------------------------------------------- organisation MOA / MOE
# Membres et titres repris des comptes de GesTT (gestionnaire-de-projets, backend/prisma/seed.mjs)
EQUIPE = [
    ("Mattéo Canada", "Chef de projet", "CP"),
    ("Rafael Maunier", "Membre de l'équipe", ""),
    ("Solal Kruczynski", "Membre de l'équipe", ""),
    ("Raphael Hovsepian", "Membre de l'équipe", ""),
]
ROLES = [
    ("CP", "Direction de projet", "Mattéo Canada (fondateur de RudyLink)", "Planning, relation avec la MOA, arbitrages, chiffrage, qualité et dépôt des livrables"),
    ("ARC", "Architecture réseau", "À attribuer", "LAN trois couches, adressage, WAN, Internet, Wi-Fi, maquette GNS3"),
    ("PHY", "Infrastructure physique", "À attribuer", "Câblage, locaux techniques, énergie, climatisation, bâtiment intelligent"),
    ("SYS", "Systèmes et services", "À attribuer", "AD, RADIUS, Proxmox, ToIP, applications, sauvegarde, supervision"),
    ("SEC", "Sécurité et conformité", "À attribuer", "Politique de sécurité, matrice de flux, RGPD, chartes, CCTP"),
    ("COM", "Communication et qualité", "À attribuer (cumulable)", "Charte, site web, journal de bord, relecture, vidéo en anglais"),
]
# point -> responsable(s) R ; le CP est A (approbateur) partout ; C = consulté
RACI = {
    1: ("CP COM", "ARC PHY SYS SEC"), 2: ("COM CP", "ARC PHY SYS SEC"), 3: ("ARC", "PHY SEC"), 4: ("PHY", "ARC"),
    5: ("ARC", "SYS SEC"), 6: ("ARC", "SYS SEC"), 7: ("ARC", "SEC"), 8: ("ARC", "SEC"), 9: ("SEC", "ARC SYS PHY"),
    10: ("ARC", "PHY SEC"), 11: ("SYS", "PHY SEC"), 12: ("SYS", "ARC PHY"), 13: ("SYS", "COM SEC"), 14: ("PHY", "SYS"),
    15: ("SYS", "SEC"), 16: ("SYS", "ARC SEC"), 17: ("PHY", "ARC SYS"), 18: ("CP", "ARC PHY SYS SEC"),
    19: ("SEC", "CP"), 20: ("COM", "CP ARC PHY SYS SEC"), 21: ("CP", "ARC PHY SYS SEC COM"),
}
MOA_DECIDE = {2, 3, 4, 7, 8, 9, 11, 13, 14, 18, 19, 21}  # points avec un choix à faire valider par le client


def organigramme():
    w, h = 720, 300
    def boite(x, y, bw, bh, titre, sous, fond, encre, trait):
        return (f"<rect x='{x}' y='{y}' width='{bw}' height='{bh}' fill='{fond}' stroke='{trait}' stroke-width='1'/>"
                f"<text x='{x + 10}' y='{y + 20}' font-family='IBM Plex Mono' font-weight='500' font-size='9' letter-spacing='.6' fill='{sous[1]}'>{sous[0]}</text>"
                f"<text x='{x + 10}' y='{y + 39}' font-family='Space Grotesk' font-weight='600' font-size='13' fill='{encre}'>{titre}</text>")
    s = [f"<svg viewBox='-1 -1 {w + 2} {h + 2}' xmlns='http://www.w3.org/2000/svg' style='width:100%'>"]
    # MOA et MOE
    s.append(boite(0, 0, 300, 58, "IUT Aix-Marseille · R&amp;T Luminy", ("MAÎTRISE D'OUVRAGE", "#6d727b"), C["surface"], C["encre"], C["trait"]))
    s.append(boite(420, 0, 300, 58, NOM, ("MAÎTRISE D'ŒUVRE", "#868b94"), C["encre"], C["papier"], C["encre"]))
    s.append(f"<line x1='300' y1='29' x2='420' y2='29' stroke='{C['encre']}' stroke-width='1'/>"
             f"<text x='360' y='22' text-anchor='middle' font-family='IBM Plex Mono' font-size='8.5' fill='#4d525b'>BESOINS · VALIDATION</text>"
             f"<text x='360' y='44' text-anchor='middle' font-family='IBM Plex Mono' font-size='8.5' fill='#4d525b'>LIVRABLES · CONSEIL</text>")
    s.append(boite(0, 92, 300, 58, "Équipe pédagogique (rôle client)", ("S. SANCHEZ · D. MANOUKIAN · R. DEPEYRE", "#6d727b"), "#ffffff", C["encre"], C["trait"]))
    s.append(f"<line x1='150' y1='58' x2='150' y2='92' stroke='{C['trait']}'/>")
    # CP
    s.append(boite(420, 92, 300, 58, "Direction de projet", ("CP · INTERLOCUTEUR DU CLIENT", C["emeraude_fonce"]), "#ffffff", C["encre"], C["emeraude"]))
    s.append(f"<line x1='570' y1='58' x2='570' y2='92' stroke='{C['encre']}'/>")
    # pôles
    poles = ROLES[1:]
    pw, gap, y0 = 132, 15, 220
    x0 = (w - (len(poles) * pw + (len(poles) - 1) * gap)) / 2
    s.append(f"<line x1='570' y1='150' x2='570' y2='186' stroke='{C['encre']}'/>"
             f"<line x1='{x0 + pw / 2}' y1='186' x2='{x0 + (len(poles) - 1) * (pw + gap) + pw / 2}' y2='186' stroke='{C['encre']}'/>")
    for i, (code, nom, *_r) in enumerate(poles):
        x = x0 + i * (pw + gap)
        s.append(f"<line x1='{x + pw / 2}' y1='186' x2='{x + pw / 2}' y2='{y0}' stroke='{C['encre']}'/>")
        mots = nom.split(" ", 1)
        s.append(f"<rect x='{x}' y='{y0}' width='{pw}' height='66' fill='#ffffff' stroke='{C['trait']}'/>"
                 f"<text x='{x + 9}' y='{y0 + 18}' font-family='IBM Plex Mono' font-weight='500' font-size='9' letter-spacing='.6' fill='#6d727b'>{code}</text>"
                 f"<text x='{x + 9}' y='{y0 + 37}' font-family='Space Grotesk' font-weight='600' font-size='12' fill='{C['encre']}'>{mots[0]}</text>"
                 f"<text x='{x + 9}' y='{y0 + 53}' font-family='Space Grotesk' font-weight='600' font-size='12' fill='{C['encre']}'>{mots[1] if len(mots) > 1 else ''}</text>")
    s.append("</svg>")
    return "".join(s)


def organisation(points):
    codes = [r[0] for r in ROLES]
    entetes = "".join(f"<th class='c'>{c}</th>" for c in codes) + "<th class='c'>MOA</th>"
    lignes = []
    for k in sorted(points, key=lambda k: points[k]["num"]):
        p = points[k]
        n = p["num"]
        resp, cons = (x.split() for x in RACI[n])
        cel = []
        for c in codes:
            v = ("R" if c in resp else "") + ("A" if c == "CP" else "")
            v = v or ("C" if c in cons else "I")
            style = "font-weight:600;color:#101217" if "R" in v else ("color:#6d727b" if v == "I" else "")
            cel.append(f"<td class='c mono' style='{style}'>{v}</td>")
        moa = "V" if n in MOA_DECIDE else "I"
        cel.append(f"<td class='c mono' style='{'font-weight:600;color:#006925' if moa == 'V' else 'color:#6d727b'}'>{moa}</td>")
        col = AXES.get(p["axis"], ("", "#4d525b"))[1]
        lignes.append(f"<tr><td class='mono' style='color:{col}'>{n:02d} · {p['axis']}</td><td>{p['title']}</td>{''.join(cel)}</tr>")
    equipe = "".join(f"<tr><td><b>{n}</b></td><td>{t}</td><td class='mono'>{r or 'à répartir'}</td></tr>" for n, t, r in EQUIPE)
    roles = "".join(f"<tr><td class='mono'><b>{c}</b></td><td><b>{n}</b></td><td>{qui}</td><td>{per}</td></tr>" for c, n, qui, per in ROLES)
    corps = f"""{entete("RLI-COM-003", "Organisation du projet")}
<span class='label accent'>Point 02 · Rôles MOA et MOE</span>
<h1 style='margin:2mm 0'>Organisation du projet</h1>
<p class='chapo'>Qui décide, qui conçoit, qui valide. Ce document fixe les rôles de la maîtrise d'ouvrage et de la maîtrise d'œuvre, la répartition des 21 points du cahier des charges et le circuit de validation des livrables.</p>
<h2>Maîtrise d'ouvrage et maîtrise d'œuvre</h2>
<div class='grille g2'>
<div class='bloc'><span class='label'>MOA · le client</span><h3>IUT Aix-Marseille, département R&amp;T (site de Luminy)</h3>
<p>Exprime le besoin, fixe le budget et les priorités, arbitre les choix et réceptionne les livrables. Pendant le projet, l'équipe pédagogique (S. Sanchez, D. Manoukian, R. Depeyre) joue ce rôle lors des réunions client.</p>
<p>Derrière la MOA : les <b>utilisateurs</b> (étudiants, enseignants, personnels) et le <b>futur exploitant</b>, le service informatique de l'université, qui recevra le dossier d'exploitation.</p></div>
<div class='bloc' style='border-color:{C['encre']}'><span class='label accent'>MOE · nous</span><h3>{NOM}</h3>
<p>Conçoit la solution technique, la chiffre, la documente et la défend devant le client. Nous sommes <b>force de proposition</b> : nous présentons des options argumentées et laissons la décision à la MOA.</p>
<p>Nous rédigeons aussi le <b>cahier des charges et le CCTP</b> qui permettront à l'université, acheteur public, de consulter les entreprises de câblage, d'électricité et les intégrateurs.</p></div>
</div>
<div style='margin:5mm 0 2mm'>{organigramme()}</div>
<section class='saut'>
{entete("RLI-COM-003", "Organisation du projet")}
<h2 style='margin-top:0'>Rôles dans l'équipe</h2>
<p>L'équipe compte quatre membres (comptes GesTT). Les six rôles sont donc cumulés : chacun prend un ou deux pôles, et le rôle COM peut être tenu par un responsable de pôle. <b>La répartition des pôles techniques reste à décider</b> à la prochaine réunion de suivi.</p>
<table><tr><th>Membre</th><th>Titre</th><th>Rôle(s)</th></tr>{equipe}</table>
<table><tr><th>Code</th><th>Rôle</th><th>Titulaire</th><th>Périmètre</th></tr>{roles}</table>
<h2>Instances de suivi</h2>
<table><tr><th>Instance</th><th>Fréquence</th><th>Participants</th><th>Trace écrite</th></tr>
<tr><td><b>Réunion de suivi</b></td><td>¼ h par semaine IUT</td><td>Équipe, encadrant</td><td>Entrée du journal de bord (site web)</td></tr>
<tr><td><b>Réunion client</b></td><td>Selon le calendrier (commune ou par groupe)</td><td>CP, responsables des points abordés, MOA</td><td>Compte rendu <span class='mono'>RLI-CR-nnn</span> sous 48 h</td></tr>
<tr><td><b>Revue interne</b></td><td>Avant chaque livraison</td><td>Rédacteur, relecteur d'un autre pôle, CP</td><td>Statut du livrable dans la roadmap</td></tr>
<tr><td><b>Bilan de rotation</b></td><td>À chaque rotation académique</td><td>Chaque membre</td><td>Bilan au format attente / objectif (noté)</td></tr></table>
</section>

<section class='saut'>
{entete("RLI-COM-003", "Organisation du projet")}
<h2 style='margin-top:0'>Répartition des 21 points (matrice RACI)</h2>
<p><b class='mono'>R</b> réalise · <b class='mono'>A</b> approuve avant envoi au client · <b class='mono'>C</b> consulté · <b class='mono'>I</b> informé · <b class='mono' style='color:#006925'>V</b> la MOA valide un choix ou une option.</p>
<table style='font-size:7.9pt'><tr><th>Point · axe</th><th>Intitulé</th>{entetes}</tr>{''.join(lignes)}</table>
</section>

<section class='saut'>
{entete("RLI-COM-003", "Organisation du projet")}
<h2 style='margin-top:0'>Circuit de validation d'un livrable</h2>
<table><tr><th>Statut</th><th>Qui</th><th>Condition pour passer au suivant</th></tr>
<tr><td><span class='pastille' style='color:#6d727b'>Brouillon</span></td><td>Responsable (R)</td><td>Contenu complet, hypothèses écrites, sources citées</td></tr>
<tr><td><span class='pastille' style='color:#0079b5'>En relecture</span></td><td>Relecteur d'un autre pôle</td><td>Cohérence avec les autres points (quantités, noms d'équipements, chiffrage)</td></tr>
<tr><td><span class='pastille' style='color:#ab7400'>Validé en interne</span></td><td>Direction de projet (A)</td><td>Charte respectée, référence et version à jour</td></tr>
<tr><td><span class='pastille' style='color:#101217'>Livré</span></td><td>Direction de projet</td><td>Envoyé ou présenté à la MOA, réserves notées</td></tr>
<tr><td><span class='pastille oui'>Validé client</span></td><td>MOA</td><td>Réserves levées ; le document passe en version 1.x</td></tr></table>
<h2>Gestion documentaire</h2>
<ul><li><b>Dépôt Git</b> : source de vérité pour les scripts, les schémas et les livrables. Une modification = un commit qui dit ce qui change.</li>
<li><b>Roadmap partagée</b> : avancement des 21 points, responsables, échéances et journal.</li>
<li><b>Références</b> : <span class='mono'>RLI-COM</span> communication, <span class='mono'>RLI-RAP</span> rapport, <span class='mono'>RLI-CR</span> compte rendu, <span class='mono'>RLI-ETU</span> étude, <span class='mono'>RLI-CCTP</span>.</li>
<li><b>Rendu final</b> : tous les supports sur AMETICE 8 à 10 jours avant la soutenance.</li></ul>
<div class='note alerte'><span class='label' style='color:#ab7400'>À décider en réunion de suivi</span><br>Attribuer les rôles ARC, PHY, SYS, SEC et COM, puis reporter les noms dans la roadmap (champ « Responsable(s) » de chaque point).</div>
</section>"""
    return page("Organisation du projet · RudyLink Infrastructure", corps)


# ---------------------------------------------------------------- modèle de rapport (HTML)
def modele_rapport():
    corps = f"""<section class='couverture'>
<img class='logo' src='../logo/rudylink-infrastructure-inverse.svg' alt='{NOM}' style='margin:-24px'>
<div class='label' style='margin-top:auto;margin-bottom:5mm'>RLI-RAP-001 · version 0.1 · JJ/MM/AAAA</div>
<h1 style='margin-top:0'>Titre du document</h1>
<p class='chapo'>Sous-titre : une phrase qui dit ce que le lecteur trouvera dans le document.</p>
<div class='bas'><span class='label'>Client : IUT Aix-Marseille, R&amp;T Luminy</span><span class='label'>Diffusion : client et équipe pédagogique</span></div>
</section>
{entete("RLI-RAP-001", "Titre du document", "../logo/rudylink-infrastructure-couleur.svg")}
<div class='cartouche'>
<div><span class='label'>Référence</span><b class='mono'>RLI-RAP-001</b></div>
<div><span class='label'>Version</span><b class='mono'>0.1</b></div>
<div><span class='label'>Statut</span><b>Brouillon</b></div>
<div><span class='label'>Rédigé par</span><b>Prénom Nom (rôle)</b></div></div>
<h3>Historique des versions</h3>
<table><tr><th>Version</th><th>Date</th><th>Auteur</th><th>Modifications</th></tr>
<tr><td class='mono'>0.1</td><td>JJ/MM/AAAA</td><td>Prénom Nom</td><td>Création du document</td></tr></table>
<span class='label accent' style='display:block;margin-top:8mm'>Point 04 · Architecture physique</span>
<h2 style='margin-top:2mm'>1. Titre de partie</h2>
<p>Texte courant en Space Grotesk 9,5 pt. Une affirmation, un chiffre : la salle serveur consomme <b>4,2 kW</b> en fonctionnement normal. Les équipements sont nommés comme sur le schéma, en mono : <code>CL-SW1</code>, <code>EL-FGT1</code>.</p>
<h3>1.1 Intertitre</h3>
<table><tr><th>Équipement</th><th>Modèle</th><th class='n'>Qté</th><th class='n'>Total HT</th></tr>
<tr><td class='mono'>CL-SW1, CL-SW2</td><td>Cisco C9500-16X</td><td class='n'>2</td><td class='n'>00 000 €</td></tr></table>
<p class='label'>Tableau 1 · Légende du tableau, source des chiffres.</p>
<div class='note'><span class='label accent'>Recommandation</span><br>Une recommandation au client, en une ou deux phrases.</div>
<div class='note alerte'><span class='label' style='color:#ab7400'>À valider avec le client</span><br>Hypothèse retenue faute d'information, à confirmer en réunion.</div>"""
    return page("Modèle de rapport · RudyLink Infrastructure", corps, "rudylink-document.css")


def signature():
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Signature de courriel · {NOM}</title></head>
<body style='margin:24px;font-family:Arial,sans-serif'>
<!-- Copier le tableau ci-dessous dans les réglages de signature (Gmail, Outlook, Thunderbird). Styles en ligne, sans police web, pour tous les clients de messagerie. -->
<table cellpadding='0' cellspacing='0' border='0' style='border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;color:#2b2f36'>
<tr><td style='padding:0 14px 0 0;border-right:1px solid #cfd2d8;vertical-align:top'>
<img src='https://{DOMAINE}/assets/logo/symbole.png' width='48' height='48' alt='RudyLink Infrastructure' style='display:block'></td>
<td style='padding:0 0 0 14px;vertical-align:top'>
<div style='font-size:14px;font-weight:bold;color:#101217'>Prénom Nom</div>
<div style='font-size:12px;color:#4d525b;margin-top:2px'>Rôle · {NOM}</div>
<div style='font-family:Consolas,monospace;font-size:11px;color:#006925;margin-top:8px;letter-spacing:.5px'>{DOMAINE.upper()}</div>
<div style='font-size:11px;color:#6d727b;margin-top:2px'>{SIGNATURE} · projet SAÉ 5.02, IUT Aix-Marseille</div>
</td></tr></table>
</body></html>"""


def produire(rendu):
    import shutil
    (SORTIE / "modeles").mkdir(parents=True, exist_ok=True)
    rendu.copier_polices(SORTIE / "fonts")
    (SORTIE / "modeles" / "rudylink-document.css").write_text(CSS, encoding="utf-8")
    cab = json.loads((RACINE / "livrables/plan_cablage/resume.json").read_text(encoding="utf-8"))
    nrj = json.loads((RACINE / "livrables/energie_refroidissement/resume.json").read_text(encoding="utf-8"))
    est = json.loads((RACINE / "chiffrage/estimation.json").read_text(encoding="utf-8"))
    pts = json.loads((RACINE / "roadmap/seed_points.json").read_text(encoding="utf-8"))
    points = {k: v for k, v in pts.items() if k.startswith("points/")}
    societe = {
        "nom": NOM, "signature": SIGNATURE, "site": DOMAINE, "contact": CONTACT,
        "origine": "Branche fictive de RudyLink, micro-entreprise réelle de Mattéo Canada (rudylink.eu), qui reprend sa charte graphique.",
        "equipe": [{"nom": n, "titre": t, "role": r} for n, t, r in EQUIPE],
        "roles": [{"code": c, "nom": n, "titulaire": q, "perimetre": per} for c, n, q, per in ROLES],
        "documents": [
            {"ref": "RLI-COM-001", "titre": "Charte graphique", "chemin": "livrables/communication/charte_graphique.pdf"},
            {"ref": "RLI-COM-002", "titre": "Présentation de la société", "chemin": "livrables/communication/plaquette_rudylink_infrastructure.pdf"},
            {"ref": "RLI-COM-003", "titre": "Organisation du projet", "chemin": "livrables/communication/organisation_projet.pdf"},
            {"ref": "", "titre": "Modèle de rapport (Word)", "chemin": "livrables/communication/modeles/modele_rapport.docx"},
            {"ref": "", "titre": "Modèle de compte rendu (Word)", "chemin": "livrables/communication/modeles/modele_compte_rendu.docx"},
            {"ref": "", "titre": "Modèle de présentation (PowerPoint)", "chemin": "livrables/communication/modeles/modele_presentation.pptx"},
            {"ref": "", "titre": "Site vitrine", "chemin": "livrables/site_web/"},
        ],
    }
    (SORTIE / "societe.json").write_text(json.dumps(societe, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    docs = {
        "charte_graphique": charte(),
        "plaquette_rudylink_infrastructure": plaquette(cab, nrj, est),
        "organisation_projet": organisation(points),
    }
    for nom, html in docs.items():
        f = SORTIE / f"{nom}.html"
        f.write_text(html, encoding="utf-8")
        rendu.pdf(f, SORTIE / f"{nom}.pdf")
    f = SORTIE / "modeles" / "modele_rapport.html"
    f.write_text(modele_rapport(), encoding="utf-8")
    rendu.pdf(f, SORTIE / "modeles" / "modele_rapport.pdf")
    (SORTIE / "modeles" / "signature_mail.html").write_text(signature(), encoding="utf-8")
    return list(docs)
