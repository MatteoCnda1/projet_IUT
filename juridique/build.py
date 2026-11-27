#!/usr/bin/env python3
"""Point 19 · Aspects juridiques et chartes : produit livrables/depots/p19/ (charte commune commun/charte.py).

Usage : python3 juridique/build.py   (après cablage/plan_cablage.py, energie/energie.py, chiffrage/estimation.py et securite/build.py)
Entrées : juridique/donnees.py (registre, AIPD, journaux, crise), pra.py, charte.py, cctp.py ; securite/pssi.py (mesures M-xx) ;
          chiffrage/estimation.json, livrables/plan_cablage/resume.json et prises.csv, livrables/energie_refroidissement/resume.json
Sorties : livrables/depots/p19/*.pdf (dossier et noms du dépôt GesTT de la tâche P19, PR #10), juridique/README.md ;
  pages HTML intermédiaires dans juridique/build/
  charte_informatique   RLI-ETU-009   charte des utilisateurs + annexe administrateurs + annexe IA
  volet_juridique       RLI-ETU-010   cadre légal, registre, AIPD, politique de journalisation, IA, crise, clauses des CCTP
  pra_juridique         RLI-ETU-011   PRA, volet juridique : obligations, exigences de reprise, moyens, contrats, calendrier
  guide_cdc_cctp        RLI-ETU-012   construire un cahier des charges et un CCTP
  cctp_lot1..5          RLI-CCTP-001 à 005   modèles de CCTP pour le client
"""
import html
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ROOT / "securite"))
from commun import charte as CH  # noqa: E402
import charte as CI  # noqa: E402  (charte informatique : juridique/charte.py)
import cctp as CC  # noqa: E402
import donnees as J  # noqa: E402
import pra as PRA  # noqa: E402
import pssi as PP  # noqa: E402

OUT = ROOT / "livrables" / "depots" / "p19"   # dossier du dépôt GesTT de la tâche P19 (PR #10), mêmes noms de fichiers
BUILD = ICI / "build"                          # pages HTML intermédiaires (non suivies par git)
e = html.escape
PSSI = {m[0]: m for m in PP.MESURES}
REFS = {"charte_informatique": "RLI-ETU-009", "volet_juridique": "RLI-ETU-010", "pra_juridique": "RLI-ETU-011",
        "guide_cdc_cctp": "RLI-ETU-012"}
REFS.update({f"cctp_lot{l['num']}": l["ref"] for l in CC.LOTS})
BADGE = CH.badge("v2.1")


def t(s):
    """Texte échappé, repère « [v2.1] » rendu en badge."""
    return e(str(s)).replace(e(J.V21), BADGE)


def css_extra(titre_court):
    """Classes propres aux documents du point 19, aux couleurs de la charte (page paysage avec le même pied de page)."""
    pied = "font: 500 6.8pt 'IBM Plex Mono','Consolas',monospace; color: #6d727b; letter-spacing: .06em;"
    return f"""
@page paysage {{ size: A4 landscape; margin: 11mm 12mm 14mm;
  @bottom-left {{ content: "RUDYLINK INFRASTRUCTURE · {titre_court.upper()}"; {pied} }}
  @bottom-right {{ content: counter(page) " / " counter(pages); {pied} }} }}
.paysage {{ page: paysage; break-before: page; break-after: page; }}
h2, h3 {{ break-after: avoid; }}
.charte p {{ text-align: justify; }}
.art {{ break-inside: avoid; margin-bottom: 2mm; }}
.signature {{ margin-top: 10mm; display: grid; grid-template-columns: 1fr 1fr; gap: 10mm; }}
.signature div {{ border-top: 1px solid var(--trait); padding-top: 2mm; font-size: 8pt; color: var(--discret); }}
.fiche {{ border: 1px solid var(--trait); border-left: 3px solid var(--encre); background: var(--surface); padding: 2.5mm 3.5mm;
  margin: 3mm 0; break-inside: avoid; }}
.fiche h3 {{ margin: 0 0 1.5mm; }}
table.regles {{ font-size: 7.3pt; }} table.regles td {{ padding: 1mm 1.4mm; }}
.ref {{ font: 500 6.6pt var(--mono); color: var(--discret); }}
.nw {{ white-space: nowrap; font-family: var(--mono); font-size: .92em; }}
td.num {{ font-family: var(--mono); white-space: nowrap; color: var(--encre); font-weight: 600; }}
td.case {{ text-align: center; color: var(--discret); }}
table.reprise {{ table-layout: fixed; font-size: 7.4pt; }}
.reprise th:nth-child(1) {{ width: 13%; }} .reprise th:nth-child(2) {{ width: 15%; }} .reprise th:nth-child(3) {{ width: 6%; }}
.reprise th:nth-child(4) {{ width: 17%; }} .reprise th:nth-child(5) {{ width: 8%; }} .reprise th:nth-child(6) {{ width: 17%; }}
.reprise th:nth-child(7) {{ width: 24%; }}
"""


def tableau(entetes, lignes, cls=""):
    H = [f"<table class='{cls}'><tr>" + "".join(f"<th>{x}</th>" for x in entetes) + "</tr>"]
    for l in lignes:
        H.append("<tr>" + "".join(f"<td>{x}</td>" for x in l) + "</tr>")
    return "".join(H) + "</table>"


def liste(items, ordonnee=False):
    b = "ol" if ordonnee else "ul"
    return f"<{b}>" + "".join(f"<li>{t(x)}</li>" for x in items) + f"</{b}>"


AVERTISSEMENT = ("<div class='note'><b>Nature du document.</b> Proposition du concepteur, rédigée pour aider le client. Ce n'est pas "
                 "un avis juridique : chaque choix (base légale, durée, régime de la vidéoprotection) est à valider par le DPO et le service "
                 "juridique de l'AMU avant d'être appliqué.</div>")


def produire(nom, titre, titre_court, chapo, corps, changements):
    ref = REFS[nom]
    page = CH.page(titre=titre, corps="".join(corps) + CH.bloc_suivi(ref, changements=changements), dossier=BUILD, ref=ref,
                   titre_court=titre_court, points="19", chapo=chapo, css_extra=css_extra(titre_court))
    CH.ecrire_et_imprimer(page, BUILD / f"{nom}.html", OUT / f"{nom}.pdf")
    print(f"  livrables/depots/p19/{nom}.pdf ({ref})")


# ---------------------------------------------------------------------------
# Charte informatique (RLI-ETU-009)
# ---------------------------------------------------------------------------
def articles(liste_articles, prefixe=""):
    H = []
    for i, (titre, pars) in enumerate(liste_articles, 1):
        H.append(f"<div class='art'><h3>{prefixe}{i}. {t(titre)}</h3>" + "".join(f"<p>{t(p)}</p>" for p in pars) + "</div>")
    return "".join(H)


def doc_charte():
    corps = ["<div class='charte'>", f"<p><b>{t(CI.PREAMBULE)}</b></p>", articles(CI.ARTICLES),
             "<h2 class='saut'>Annexe A · Administrateurs</h2><p>Les personnes qui disposent de droits d'administration (personnels "
             "et prestataires) s'engagent en plus sur ce qui suit.</p>", articles(CI.ANNEXE_ADMIN, "A."),
             "<div class='signature'><div>Nom, fonction, date</div><div>Signature de l'administrateur</div></div>",
             "<h2 class='saut'>Annexe B · Usage de la plateforme d'IA</h2>", articles(CI.ANNEXE_IA, "B."),
             "</div>",
             "<h2>Mise en œuvre</h2><ul>"
             "<li><b>Opposabilité</b> : la charte est annexée au règlement intérieur, ce qui la rend applicable aux étudiants et aux agents ; "
             "pour les personnels, le CSA est consulté avant, car elle décrit des moyens de contrôle de leur activité.</li>"
             "<li><b>Information</b> : remise à l'inscription et à l'arrivée, acceptée à la première connexion, affichée sur le portail.</li>"
             "<li><b>Révision</b> : à chaque évolution notable des moyens de contrôle (journaux, inspection TLS, vidéoprotection), avec la PSSI.</li>"
             f"<li><b>Cohérence</b> {BADGE} : les durées citées sont celles de la politique de journalisation (volet juridique, section 4) : "
             "données techniques de connexion 1 an, adresses des pages consultées 6 mois, images 30 jours.</li></ul>"]
    produire("charte_informatique", "Charte informatique", "Charte informatique",
             "Règles d'usage des moyens informatiques de l'IUT. À annexer au règlement intérieur de l'AMU, après consultation du "
             "comité social d'administration (CSA).", corps,
             "Ce que l'IUT contrôle dit exactement : données techniques de connexion conservées 1 an, adresses des pages consultées "
             "6 mois pour la sécurité seulement ; vidéoprotection (aucune caméra dans les lieux de pause, 30 jours) ; réseaux Wi-Fi et "
             "bancs de TP corrigés ; charte commune des livrables.")


# ---------------------------------------------------------------------------
# Volet juridique (RLI-ETU-010)
# ---------------------------------------------------------------------------
CLAUSES_LOTS = {  # ce que chaque CCTP reprend du volet juridique
    1: "Confidentialité et accès distant par le bastion ; configurations effacées avant tout retour de matériel ; clauses "
       "environnementales (loi Climat et résilience).",
    2: "Journal légal (adresses et ports, volumes : 1 an) et journal du proxy (URL : 6 mois), conformes à la section 4 ; "
       "inspection TLS avec liste d'exclusion.",
    3: f"Sous-traitance RGPD (art. 28) de la copie externalisée : {J.SECNUMCLOUD} ; disques défectueux conservés par l'IUT ; plateforme "
       "d'IA hors ligne (AI Act, AIPD T08).",
    4: "AIPD T06 : aucune caméra dans un lieu de pause, une salle de cours, un bureau ou des sanitaires ; 30 jours ; masquage ; "
       "panneaux ; autorisation préfectorale ; disques de l'enregistreur conservés par l'IUT.",
    5: "Vérification initiale (Code du travail, R4226-14), bruit de voisinage (Code de la santé publique, R1336-6 et R1336-7), "
       "non-classement ICPE, NF C 15-100 ; ni modem ni télésurveillance en nuage.",
}


def doc_volet():
    H = [AVERTISSEMENT, "<div class='cles'>", f"<div class='cle'><b>{len(J.TRAITEMENTS)}</b>traitements au registre</div>",
         f"<div class='cle'><b>{len(J.AIPD)}</b>analyses d'impact</div>",
         f"<div class='cle'><b>{len(J.JOURNAUX)}</b>types de journaux encadrés</div>",
         f"<div class='cle'><b>{len(CC.LOTS)}</b>CCTP qui reprennent ces règles</div></div>"]
    # 1. Cadre
    H += ["<h2>1. Cadre légal applicable</h2>",
          tableau(["Texte", "Ce qu'il impose au projet"], [
              [t(J.TEXTES["RGPD"]) + "<br>" + t(J.TEXTES["LIL"]), "Registre, information des personnes, sécurité, AIPD pour les traitements "
               "à risque, notification des violations sous 72 h. Le DPO est obligatoire pour une autorité publique : celui de l'AMU."],
              [t(J.TEXTES["CPCE"]) + "<br>" + t(J.TEXTES["LCEN"]), f"Conserver un an les données techniques de connexion (qui, quand, "
               f"adresses IP et ports, volumes), jamais le contenu, et les fournir sur réquisition. {BADGE}"],
              [t(J.TEXTES["CSI"]), "Caméras filmant un lieu ouvert au public : autorisation du préfet, information, durée limitée (un mois au plus). "
               "Ailleurs (locaux non ouverts au public), le RGPD seul s'applique."],
              [t(J.TEXTES["CT"]) + "<br>" + t(J.TEXTES["CGFP"]), "Un contrôle de l'activité des personnels doit être justifié, proportionné, "
               "connu à l'avance ; les instances représentatives sont consultées."],
              [t(J.TEXTES["CP-STAD"]) + "<br>" + t(J.TEXTES["CP-CORR"]) + " " + BADGE, "Fonde les sanctions de la charte ; protège les "
               "messages personnels, y compris contre les administrateurs, agents publics soumis à l'article 432-9."],
              [t(J.TEXTES["AIA"]), "Formation des utilisateurs à l'IA, usages interdits (reconnaissance des émotions dans l'enseignement), "
               "usages à haut risque (évaluation, admission, surveillance des examens)."],
              [t(J.TEXTES["NIS2"]), "Hypothèse retenue : entité concernée. Gouvernance, gestion des risques, notification des incidents "
               "(24 h, 72 h, 1 mois)."],
              [t(J.TEXTES["CCP"]), f"Marchés en {len(CC.LOTS)} lots (CCTP RLI-CCTP-001 à {CC.LOTS[-1]['ref'][-3:]}) : égalité des candidats "
               f"(« ou équivalent »), allotissement, critère et clauses environnementales. {BADGE}"],
              [t(J.TEXTES["CT-ELEC"]) + "<br>" + t(J.TEXTES["CSP-BRUIT"]) + "<br>" + t(J.TEXTES["ICPE"]),
               "Groupe électrogène et installations du lot 5 : vérification initiale par un organisme accrédité avant la mise en service ; "
               "émergence du bruit limitée à 5 dB(A) le jour et 3 dB(A) la nuit ; groupe non classé (sous 1 MW thermique et 50 t de "
               f"produits pétroliers). {BADGE}"],
              [t(J.TEXTES["CPI"]), "Licences des logiciels, droits sur les contenus ; rappelé dans la charte."]])]
    # 2. Registre
    H += ["<div class='paysage'><h2>2. Registre des traitements (RGPD art. 30)</h2>",
          "<p>Responsable de traitement : l'AMU, représentée sur le site par le directeur de l'IUT. Seuls les traitements créés ou "
          "touchés par l'infrastructure figurent ici ; ils sont à reporter dans le registre de l'AMU. Aucun transfert hors de l'Union "
          f"européenne : tout est hébergé sur le site, et la sauvegarde externalisée suit la règle unique du dossier : {t(J.SECNUMCLOUD)}. "
          f"{BADGE}</p>",
          tableau(["", "Traitement", "Finalité", "Base légale", "Personnes", "Données", "Destinataires", "Durée", "Sécurité", "AIPD"],
                  [[f"<b>{c}</b>", f"<b>{t(n)}</b><br><span class='ref'>{e(pt)}</span>", t(fi), e(J.BASES[b]), t(pe), t(do), t(de), t(du),
                    e(me), "<b class='ko'>oui</b>" if a == "oui" else "non"]
                   for c, n, fi, b, pe, do, de, du, me, a, pt in J.TRAITEMENTS], cls="regles"),
          "<p class='sous'>T10 (géolocalisation) figure au registre parce qu'elle est envisagée par le point 13 ; l'AIPD conclut "
          "qu'il ne faut pas la mettre en œuvre (section 3). T13 (messagerie) est ajoutée en v2.1 : elle manquait au registre.</p></div>"]
    # 3. AIPD
    H.append("<h2>3. Analyses d'impact (AIPD, RGPD art. 35)</h2>"
             "<p>Une AIPD est due quand un traitement réunit au moins deux critères des lignes directrices du CEPD. Gravité et vraisemblance "
             "notées de 1 à 4, comme dans la méthode de la CNIL.</p>")
    noms = {x[0]: x[1] for x in J.TRAITEMENTS}
    for code, a in J.AIPD.items():
        H.append(f"<div class='fiche'><h3>{code} · {t(noms[code])}</h3>"
                 f"<p><b>Critères</b> : {e(', '.join(J.CRITERES[c] for c in a['criteres']))}.</p>"
                 f"<p><b>Nécessité</b> : {t(a['necessite'])}</p><p><b>Proportionnalité</b> :</p>" + liste(a["proportion"])
                 + tableau(["Risque pour les personnes", "Gravité", "Vraisemblance", "Mesures"],
                           [[t(r), str(g), str(v), t(m)] for r, g, v, m in a["risques"]])
                 + f"<p><b>Conclusion</b> : {t(a['conclusion'])}</p></div>")
    H.append(f"<h3>Les {J.NB_CAMERAS} caméras du plan de câblage</h3><p>Le régime dépend du lieu filmé. Classement proposé, à valider "
             "par le DPO :</p>")
    H.append(tableau(["Prise", "Niveau", "Lieu", "Régime", "Point d'attention"],
                     [[f"<span class='nw'>{c}</span>", n, e(s), ("<b class='ko'>" + r + "</b>") if r == "à retirer" else e(r), e(x)]
                      for c, n, s, r, x in J.CAMERAS]))
    if J.LIEU_DE_PAUSE_FILME:
        H.append("<div class='note alerte'><b>À corriger dans le plan de câblage (point 04)</b> : "
                 + ", ".join(c[0] for c in J.CAMERAS if c[3] == "à retirer") + " (lieu de pause). Le foyer "
                 "est un lieu de vie : la CNIL considère que filmer les lieux de pause est disproportionné. Proposition : la remplacer par "
                 "une caméra sur la porte du foyer, côté circulation, ou la supprimer.</div>")
    else:
        H.append(f"<div class='note'><b>Caméra du foyer retirée</b> {BADGE} : la v2 prévoyait une caméra au foyer des étudiants "
                 "(prise N0-LT01-P050 du plan v2). Le foyer est un lieu de pause, que la CNIL exclut de la vidéoprotection : le plan de câblage v2.1 l'a "
                 f"retirée ({J.NB_CAMERAS} caméras). Les images sont enregistrées par un enregistreur dédié, VS-NVR1, en zone SRV, "
                 "dimensionné pour 30 jours et pas au-delà.</div>")
    # 4. Journalisation
    H += ["<h2 class='saut'>4. Politique de journalisation</h2>",
          "<p>Ce qui est gardé, combien de temps et qui peut le lire. La chaîne technique (collecte, scellement, archives) est décrite "
          "dans l'architecture L3 (section 10) et la PSSI (M-DET-1).</p>",
          f"<div class='note'><b>Deux classes de journaux</b> {BADGE}<ul><li>{t(J.CONSERVATION_CONNEXION)} ; base : "
          f"{t(J.TEXTES['CPCE'])}.</li><li>{t(J.CONSERVATION_NAVIGATION)}.</li></ul>La PSSI (M-DET-1), la matrice des flux, ce volet et "
          "la charte informatique disent la même chose ; une durée différente dans l'un d'eux est une erreur à corriger.</div>",
          tableau(["Journal", "Sources", "Contenu", "Finalité", "Durée", "Accès", "Registre"], [[t(x) for x in j] for j in J.JOURNAUX]),
          "<h3>Ce qui est interdit</h3>" + liste(J.INTERDITS_JOURNAUX),
          "<h3>Répondre à une réquisition judiciaire</h3><ol>"
          "<li>La réquisition (code de procédure pénale, art. 60-1, 77-1-1 ou 99-3) arrive par écrit à la direction, qui la transmet au RSSI ; "
          "une demande orale ou par simple courriel n'est pas une réquisition.</li>"
          "<li>Le RSSI vérifie qu'elle émane d'un officier de police judiciaire ou d'un magistrat et qu'elle précise les données et la période.</li>"
          "<li>L'une des deux personnes habilitées extrait les seules données demandées des archives scellées, avec l'empreinte du fichier "
          "d'origine (preuve d'intégrité).</li>"
          "<li>La réponse est envoyée par le canal indiqué ; la réquisition, l'extraction et l'envoi sont consignés dans le registre des accès.</li></ol>",
          "<h3>Droits des personnes</h3><p>Accès et rectification auprès du DPO de l'AMU. Les données de connexion (T03) relèvent d'une "
          "obligation légale : pas de droit d'opposition ni d'effacement avant la fin de la durée de conservation.</p>"]
    # 5. IA
    H += ["<h2>5. Intelligence artificielle</h2>",
          f"<p>La plateforme d'IA locale (point 11) fait de l'IUT le <b>déployeur</b> d'un système d'IA reposant sur un modèle d'IA à usage "
          f"général, au sens de l'AI Act (art. 3, point 4) {BADGE}. Il deviendrait <b>fournisseur</b> s'il modifiait substantiellement "
          "le modèle (réentraînement) ou le mettait sur le marché sous son nom, ce qui n'est pas prévu.</p>",
          tableau(["Obligation", "Ce qui est prévu", "Depuis"], [
              ["Maîtrise de l'IA (art. 4) : former les personnes qui utilisent le système", "Formation courte demandée avant le premier "
               "usage (annexe B de la charte)", "2 février 2025"],
              ["Pratiques interdites (art. 5), dont la reconnaissance des émotions dans les établissements d'enseignement", "Interdit par la "
               "charte et absent de la plateforme", "2 février 2025"],
              ["Usages à haut risque (annexe III, point 3) : admission, évaluation des acquis, surveillance des examens", "Exclus de la "
               "plateforme ; tout projet de ce type passerait par une analyse et une conformité dédiées", "2 août 2026"],
              ["Transparence (art. 50) : signaler à l'utilisateur qu'il échange avec une IA, marquer certains contenus générés",
               "Mention permanente dans l'interface ; règle de citation dans la charte", "2 août 2026"],
              ["RGPD", "AIPD T08, durées courtes, pas de réentraînement sur les requêtes", "—"]]),
          "<p class='sous'>Le calendrier des obligations « haut risque » peut être décalé par la proposition « omnibus numérique » de la "
          "Commission (novembre 2025) : à vérifier à la date de mise en service.</p>"]
    # 6. Crise
    H += ["<h2 class='saut'>6. Gestion d'une crise d'origine cyber (volet gouvernance du PRA)</h2>",
          "<p>Le PRA technique (sauvegardes, RPO/RTO, ordre de restauration) est au point 15. Ici : qui décide, qui prévient qui, et dans "
          "quels délais. Inspiré des guides de l'ANSSI sur la gestion de crise et du kit d'exercice dédié à l'enseignement supérieur. "
          "Le document <b>PRA, volet juridique</b> (pra_juridique.pdf, RLI-ETU-011) complète cette section : obligations de continuité, "
          "exigences de reprise par service données au point 15, continuité électrique, contrats, preuves et calendrier légal des "
          "premières heures.</p>",
          "<h3>Cellule de crise</h3>", tableau(["Rôle", "Qui", "Mission"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in J.CELLULE]),
          "<p>Elle se réunit hors du SI touché : liste de contacts imprimée, téléphones portables, une salle prévue à l'avance, une messagerie "
          "de secours qui ne dépend pas de l'annuaire.</p>",
          "<h3>Qui prévenir, et quand</h3>",
          tableau(["Qui", "Quand", "Délai", "Par qui", "Texte"], [[f"<b>{e(a)}</b>", e(b), e(c), e(d), e(x)] for a, b, c, d, x in J.NOTIFICATIONS]),
          "<h3>Fiches réflexes</h3>"]
    for titre, etapes in J.FICHES_REFLEXES:
        H.append(f"<div class='fiche'><h3>{e(titre)}</h3>" + liste(etapes, ordonnee=True) + "</div>")
    H += ["<h3>S'entraîner</h3><p>Un exercice par an avec le kit de l'ANSSI pour l'enseignement supérieur (scénario rançongiciel en période "
          "d'examens), puis un retour d'expérience qui met à jour la PSSI, l'analyse de risque et ces fiches.</p>"]
    # 7. Marchés
    H += [f"<h2>7. Marchés : ce que les {len(CC.LOTS)} CCTP reprennent de ce volet {BADGE}</h2>",
          "<p>Une obligation juridique écrite dans le CCTP s'impose au titulaire ; oubliée, elle coûte un avenant. Chaque lot reprend en "
          "plus les clauses communes (accès distant par le bastion, confidentialité, garanties de rétablissement).</p>",
          tableau(["Lot", "Réf.", "Objet", "Clauses juridiques reprises"],
                  [[str(l["num"]), f"<span class='nw'>{l['ref']}</span>", t(l["titre"]), t(CLAUSES_LOTS[l["num"]])] for l in CC.LOTS])]
    # 8. Points à valider
    H += ["<h2>8. Points à faire valider par le DPO et le service juridique</h2><ul>",
          "<li>Régime de chaque caméra (lieu ouvert au public ou non)" + (" et autorisation préfectorale" if J.LIEU_PUBLIC_FILME else
          " : toutes aux accès des locaux techniques, aucune autorisation préfectorale à demander")
          + (" ; retrait de la caméra du foyer" if J.LIEU_DE_PAUSE_FILME else "") + ".</li>",
          "<li>Durées de conservation, en particulier pour la plateforme d'IA (30 jours de contenus) et pour les journaux de navigation "
          f"(6 mois) {BADGE}.</li>",
          "<li>Abandon de la géolocalisation des étudiants (T10) au profit d'un émargement en salle.</li>",
          "<li>Calendrier de consultation du CSA pour la charte et la vidéoprotection.</li>",
          "<li>Statut NIS 2 de l'établissement une fois la loi promulguée, et désignation des contacts auprès de l'ANSSI.</li></ul>"]
    produire("volet_juridique", "Volet juridique", "Volet juridique",
             "Cadre légal, registre des traitements, analyses d'impact, politique de journalisation, intelligence artificielle, gestion "
             "d'une crise d'origine cyber et clauses reprises par les CCTP.", H,
             "Politique de journalisation en deux classes (connexion 1 an, navigation 6 mois) ; messagerie ajoutée au registre (T13) ; "
             f"caméra du foyer retirée ({J.NB_CAMERAS} caméras), enregistreur VS-NVR1 ; règle SecNumCloud unique ; références précisées "
             "(décrets de 2021, art. 432-9, AI Act, NIS 2) ; cadre légal du groupe électrogène ; section 7 sur les cinq CCTP ; charte "
             "commune des livrables.")


# ---------------------------------------------------------------------------
# PRA, volet juridique (RLI-ETU-011)
# ---------------------------------------------------------------------------
def doc_pra():
    H = [AVERTISSEMENT, "<div class='cles'>", f"<div class='cle'><b>{len(PRA.SERVICES)}</b>services avec DMIA et PDMA</div>",
         "<div class='cle'><b>4 h</b>GTR des équipements critiques, 24 h/24</div>",
         f"<div class='cle'><b>{PRA.GE['autonomie_h']} h</b>d'autonomie du groupe électrogène</div>",
         "<div class='cle'><b>72 h</b>CNIL, ANSSI et plainte</div></div>",
         "<h2>1. Partage avec le point 15</h2>",
         tableau(["", "Ce document (point 19)", "PRA technique (point 15)"], [
             ["<b>Question</b>", "Qu'exigent la loi et les contrats ?", "Comment sauvegarder et restaurer ?"],
             ["<b>Contenu</b>", "obligations, DMIA et PDMA exigées, moyens qui les tiennent, règles de restauration, contrats, preuves, "
              "notifications, gouvernance",
              f"sauvegardes, ordre et procédures de restauration, tests ; réplication vers le site jumeau (Digne ou Gap) (piste du point 15 ; "
              f"flux de sauvegarde à ajouter à la matrice si elle est retenue) {BADGE}"],
             ["<b>Valide</b>", "DPO, service juridique, direction", "RSSI, administrateurs"]]),
         "<p><b>DMIA</b> : durée maximale d'interruption admissible (RTO). <b>PDMA</b> : perte de données maximale admissible (RPO). "
         "<b>GTR</b> : garantie de rétablissement exigée du titulaire de la maintenance.</p>",
         "<h2>2. Obligations de continuité</h2>",
         tableau(["Obligation", "Texte", "Ce qu'il impose", "Conséquence pour le PRA"],
                 [[f"<b>{t(a)}</b>", e(b), e(c), t(d)] for a, b, c, d in PRA.OBLIGATIONS], cls="pra"),
         "<div class='paysage'><h2>3. Exigences de reprise par service</h2>",
         "<p>Pour chaque service, l'enjeu juridique fixe une durée d'interruption et une perte de données admissibles. Ce sont les "
         "exigences d'entrée du PRA technique ; la PDMA dit aussi ce qui la tient (section 4). Les codes Txx renvoient au registre des "
         f"traitements (volet juridique, section 2). {BADGE}</p>",
         tableau(["Service", "Équipements (GTR)", "Registre", "Enjeu juridique", "DMIA", "PDMA", "Mode dégradé"],
                 [[f"<b>{t(a)}</b>", t(b), t(c), t(d), t(f), t(g), t(m)] for a, b, c, d, f, g, m in PRA.SERVICES], cls="reprise"),
         f"<p class='sous'>{t(PRA.NOTE_SERVICES)}</p></div>",
         f"<h2>4. Ce qui tient les PDMA et les DMIA {BADGE}</h2>",
         "<h3>Sauvegardes et réplications de l'architecture v2.1</h3><p>Les fréquences sont celles que le point 15 doit paramétrer ; les "
         "PDMA de la section 3 n'en demandent pas davantage.</p>",
         tableau(["Moyen", "Ce qu'il protège", "Fréquence", "Perte maximale", "Limite"],
                 [[f"<b>{t(a)}</b>", t(b), t(c), t(d), t(x)] for a, b, c, d, x in PRA.MOYENS]),
         "<h3>Continuité électrique</h3><p>Étude du point 14 (énergie et refroidissement, BET des locaux techniques). Le groupe "
         "électrogène et l'inverseur de source sont achetés par le lot 5, avec leur maintenance et la livraison de gazole.</p>",
         tableau(["Situation", "Ce qui se passe", "Limite"], [[f"<b>{t(a)}</b>", t(b), t(c)] for a, b, c in PRA.CONTINUITE]),
         "<h2>5. Restaurer sans enfreindre le droit</h2>"]
    for titre, texte in PRA.REGLES_RESTAURATION:
        H.append(f"<div class='fiche'><h3>{t(titre)}</h3><p>{t(texte)}</p></div>")
    H += ["<h2 class='saut'>6. Contrats : clauses de reprise à prévoir</h2>",
          tableau(["Contrat", "Clause", "Pourquoi", "Où"], [[f"<b>{t(a)}</b>", t(b), t(c), t(d)] for a, b, c, d in PRA.CONTRATS], cls="pra"),
          "<h2>7. Calendrier légal d'une crise</h2>",
          "<p>H0 : le moment où l'incident est connu. Les délais courent dès cette heure-là, y compris la nuit et le week-end.</p>",
          tableau(["Échéance", "Action", "Qui", "Texte"], [[f"<b>{e(a)}</b>", e(b), e(c), e(d)] for a, b, c, d in PRA.CALENDRIER]),
          "<h3>Cellule de crise</h3>",
          tableau(["Rôle", "Qui", "Mission"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in J.CELLULE]),
          "<p>Détail des notifications et fiches réflexes : volet juridique, section 6.</p>",
          "<h2 class='saut'>8. Ce que le point 15 doit livrer</h2>" + liste(PRA.EXIGENCES_P15),
          "<h2>9. Faire vivre le PRA</h2>",
          tableau(["Quoi", "Qui", "Quand"], [[f"<b>{t(a)}</b>", t(b), t(c)] for a, b, c in PRA.GOUVERNANCE]),
          "<h2>10. Points à faire valider</h2>" + liste(PRA.A_VALIDER)]
    produire("pra_juridique", "Plan de reprise d'activité · volet juridique", "PRA juridique",
             "Ce que le droit impose à la reprise du site après un sinistre, une coupure électrique ou une cyberattaque, et ce que le "
             "PRA technique du point 15 doit donc garantir.", H,
             f"Continuité électrique (groupe électrogène, arrêt NUT à T0 + {PRA.T_ARRET} min s'il ne démarre pas) ; DMIA et PDMA alignées "
             "sur les sauvegardes en place (nuit, rotation hebdomadaire des disques, S3 Object Lock) ; garanties de rétablissement 4 h et "
             "J+1 par service ; journaux légaux sur deux collecteurs ; règle SecNumCloud unique ; charte commune des livrables.")


# ---------------------------------------------------------------------------
# CCTP (RLI-CCTP-001 à 005)
# ---------------------------------------------------------------------------
CHANGEMENTS_CCTP = {
    1: "Garanties de rétablissement (4 h pour le cœur, la distribution et les WLC, J+1 pour le reste) ; rocades : second cheminement "
       "là où le plan les fait passer par les mêmes locaux ; Euroclasse et norme alignées sur le plan de câblage ; désignations lues "
       "dans le chiffrage, sans les notes internes ; lot 5 pour l'énergie.",
    2: "Remplacement sous 4 h, 24 h/24 (au lieu du jour ouvré suivant) ; sécurité du routage BGP ; ordre de déploiement des règles ; "
       "journal légal et journal du proxy conformes à la politique de journalisation.",
    3: "Garanties de rétablissement et disques conservés ; sauvegarde quotidienne, rotation des disques hors ligne et S3 Object Lock ; "
       "règle SecNumCloud unique ; ligne de la sauvegarde externalisée ; tranche IA rattachée au lot 5 pour l'énergie.",
    4: f"Enregistreur physique VS-NVR1 dimensionné pour 30 jours ({J.NB_CAMERAS} caméras) ; caméra du foyer retirée ; quantités lues "
       "dans le chiffrage du lot sûreté ; maintenance J+1 et disques conservés.",
    5: "Nouveau lot : groupe électrogène, inverseur de source, génie civil et raccordement, onduleurs, TD-INFO, climatisation, "
       "ventilation des locaux techniques, extinction, protections contre l'eau, baies ; maintenance 4 h et livraison de gazole.",
}


def doc_cctp(lot):
    H = ["<div class='note'><b>Modèle.</b> Les références de produits sont celles du chiffrage du projet, données à titre indicatif : "
         "chaque marque citée est suivie de « ou équivalent ». Les exigences numérotées sont vérifiées à la recette."
         + (f" {BADGE} Lot créé en v2.1." if lot.get("nouveau") else "") + "</div>"]
    if lot.get("attention"):
        H.append(f"<div class='note alerte'><b>Avant la consultation</b> : {t(lot['attention'])}</div>")
    H += ["<h2>1. Objet</h2>", f"<p>{t(lot['objet'])}</p>", f"<p><b>Hors du lot</b> : {t(lot['hors_lot'])}</p>",
          f"<h2>2. Documents de référence</h2><p>Dossier de conception RudyLink Infrastructure, {CH.MENTION} : "
          + ", ".join(e(r) for r in lot["references"]) + ".</p>",
          "<h2>3. Quantités</h2>",
          tableau(["Repère", "Désignation (indicative)", "Quantité", "Remarque"],
                  [[e(a), e(b) + (" <i>ou équivalent</i>" if CC.marque(b) else ""), q, t(n)] for a, b, q, n in lot["quantites"]])]
    if lot.get("recurrent"):
        H += ["<h3>Prestations récurrentes (prix annuels au bordereau, 3 ans)</h3>",
              tableau(["Prestation", "Contenu"], [[f"<b>{e(p)}</b>", t(d)] for p, d in lot["recurrent"]])]
    H.append("<h2>4. Exigences techniques</h2>")
    k = 0
    for titre, exigences in lot["exigences"]:
        H.append(f"<h3>{t(titre)}</h3>")
        rangs = []
        for x in exigences:
            k += 1
            rangs.append([f"L{lot['num']}-{k:02d}", t(x), "☐"])
        H.append(tableau(["N°", "Exigence", "Conforme"], rangs, cls="exig").replace("<tr><td>L", "<tr><td class='num'>L")
                 .replace("<td>☐</td>", "<td class='case'>☐</td>"))
    H.append("<h2 class='saut'>5. Clauses communes à tous les lots</h2>")
    for titre, clauses in CC.COMMUNES.items():
        H.append(f"<h3>{t(titre)}</h3>" + liste(clauses))
    H.append("<h2>6. Réponse attendue du candidat</h2><ul>"
             "<li>Un mémoire technique qui reprend chaque exigence numérotée et indique comment elle est satisfaite (ou l'écart proposé).</li>"
             "<li>Les fiches techniques, la consommation électrique, les dates de fin de support et la politique de correctifs.</li>"
             f"<li>Le délai de rétablissement garanti pour chaque équipement, au plus celui des exigences {BADGE}.</li>"
             "<li>Le plan de recette proposé et le planning d'intervention, compatible avec le calendrier universitaire.</li></ul>")
    nom = f"cctp_lot{lot['num']}"
    produire(nom, f"CCTP · Lot {lot['num']} : {lot['titre']}", f"CCTP lot {lot['num']}",
             "Modèle de cahier des clauses techniques particulières, à compléter par les services achats de l'AMU (CCAP, règlement de "
             "la consultation, bordereau de prix).", H, CHANGEMENTS_CCTP[lot["num"]])


# ---------------------------------------------------------------------------
# Guide CdC / CCTP (RLI-ETU-012)
# ---------------------------------------------------------------------------
def doc_guide():
    n = len(CC.LOTS)
    ccag = {5: "CCAG-Travaux", 1: "CCAG-TIC (CCAG-Travaux pour la pose du câblage)"}
    H = ["<h2>1. Les pièces d'un marché</h2>", tableau(["Pièce", "Rôle"], [[f"<b>{e(a)}</b>", t(b)] for a, b in CC.PIECES]),
         "<h2>2. Démarche</h2>" + liste(CC.DEMARCHE, ordonnee=True),
         "<h2>3. Sommaire type d'un cahier des charges</h2>" + liste(CC.SOMMAIRE_CDC, ordonnee=True),
         f"<h2>4. Les {n} modèles de CCTP {BADGE}</h2>",
         tableau(["Lot", "Réf.", "Objet", "Fichier", "CCAG"],
                 [[str(l["num"]), f"<span class='nw'>{l['ref']}</span>", t(l["titre"]) + (f" {BADGE}" if l.get("nouveau") else ""), f"<code>cctp_lot{l['num']}.pdf</code>",
                   ccag.get(l["num"], "CCAG-TIC")] for l in CC.LOTS]),
         f"<p>Le lot 5 (énergie et locaux techniques : groupe électrogène et inverseur de source, onduleurs, TD-INFO, climatisation, "
         f"extinction, baies) reprend l'étude du point 14 et relève du CCAG-Travaux ; il peut être scindé en deux lots par métier "
         f"(électricité ; génie climatique et extinction). Les prestations d'intégration et de recette du chiffrage sont réparties dans "
         f"les lots. Toutes les quantités des CCTP sont lues dans le chiffrage du point 18 et dans les études des points 04 et 14. {BADGE}</p>",
         "<h2>5. Où sont les exigences de sécurité et de maintenance</h2><p>Les clauses communes reprennent la PSSI : "
         + ", ".join(f"{c} ({e(PSSI[c][2])})" for c in ("M-ADM-2", "M-ADM-3", "M-POS-2", "M-FOU-1") if c in PSSI) + ". Les tests de "
         "recette du filtrage sont ceux de la matrice des flux. Les garanties de rétablissement (4 h, 24 h/24 et 7 j/7 pour les "
         f"équipements critiques, jour ouvré suivant pour les autres) sont celles du PRA, volet juridique {BADGE}. Une exigence de "
         "sécurité écrite dans le CCTP coûte peu ; la même, ajoutée après la livraison, coûte un avenant.</p>"]
    produire("guide_cdc_cctp", "Construire un cahier des charges et un CCTP", "Guide CdC et CCTP",
             "Guide pour le client : quelles pièces écrire, dans quel ordre, et comment utiliser les cinq modèles de CCTP de ce dossier.", H,
             "Cinq lots : lot 5 « Énergie et locaux techniques » (CCAG-Travaux) ; références RLI-CCTP-001 à 005 ; garanties de "
             "rétablissement ; charte commune des livrables.")


# ---------------------------------------------------------------------------
# README (modèle A8 de la charte) et contrôles
# ---------------------------------------------------------------------------
def readme():
    lignes = [
        ("charte_informatique", True, "Charte des utilisateurs, annexe A administrateurs, annexe B usage de l'IA"),
        ("volet_juridique", True, "Cadre légal, registre des traitements, AIPD (vidéoprotection, IA, géolocalisation), politique de "
         "journalisation, AI Act, gestion de crise (volet gouvernance du PRA), clauses reprises par les CCTP"),
        ("pra_juridique", True, "PRA, volet juridique : obligations de continuité, DMIA et PDMA par service (entrée du point 15), "
         "sauvegardes et continuité électrique qui les tiennent, garanties de rétablissement, contrats, calendrier légal des 72 premières heures"),
        ("guide_cdc_cctp", True, f"Construire un cahier des charges et un CCTP ; les {len(CC.LOTS)} lots"),
    ] + [(f"cctp_lot{l['num']}", False, f"CCTP lot {l['num']} : {l['titre']}") for l in CC.LOTS]
    tab = "".join(f"| {'**' if gras else ''}[{n}.pdf](../livrables/depots/p19/{n}.pdf){'**' if gras else ''} | {REFS[n]} | {c} |\n" for n, gras, c in lignes)
    texte = ("# Aspects juridiques et chartes (point 19) : sources\n\n"
             "Charte informatique, volet juridique (RGPD, journaux, IA, crise), PRA juridique et modèles de CCTP pour les marchés du client. "
             "Les PDF sont écrits dans `livrables/depots/p19/`, le dossier et les noms du dépôt GesTT de la tâche P19 (PR #10).\n\n"
             "| Document | Réf. | Contenu |\n|---|---|---|\n" + tab +
             f"\n**Version {CH.VERSION[1:]} — {CH.DATE_VERSION}** : lot 5 « Énergie et locaux techniques » (groupe électrogène, "
             "inverseur de source, onduleurs, climatisation, extinction), garanties de rétablissement 4 h et J+1, conservation des "
             "journaux en deux classes (connexion 1 an, navigation 6 mois), enregistreur vidéo VS-NVR1 et caméra du foyer retirée, "
             "règle SecNumCloud unique, quantités des CCTP lues dans le chiffrage sans ses notes internes, charte commune ; changements "
             "repérés « v2.1 » dans les documents. Version précédente : le dépôt GesTT du 19/11/2026 (PR #10).\n\n"
             "Régénérer : `python3 juridique/build.py` (sources : `juridique/donnees.py`, `pra.py`, `charte.py`, `cctp.py` ; "
             "entrées : `chiffrage/estimation.json`, `livrables/plan_cablage/resume.json`, `livrables/energie_refroidissement/resume.json`). "
             "Propositions du concepteur, à valider par le DPO et le service juridique de l'AMU.\n")
    (ICI / "README.md").write_text(texte, encoding="utf-8")
    print("  juridique/README.md")


def controles():
    """Avertissements (non bloquants) : données d'entrée incohérentes ou périmées."""
    try:
        PP.verifier()
    except AssertionError as x:
        print(f"  ⚠ securite/pssi.py : verifier() échoue ({x})")
    for cat, schema, sol in CC.couverture():
        print(f"  ⚠ ligne du chiffrage dans aucun CCTP : {cat} · {schema} · {sol}")
    if J.NB_CAMERAS != CC.NB_CAMERAS:
        print(f"  ⚠ prises.csv ({J.NB_CAMERAS} caméras) et resume.json ({CC.NB_CAMERAS}) diffèrent : relancer cablage/plan_cablage.py")
    if CC.SURETE_CHIFFREE:
        cam = [q for _, b, q, _ in CC.quantites_lot4() if "améra" in b]
        if cam and cam[0] != str(CC.NB_CAMERAS):
            print(f"  ⚠ lot 4 : {cam[0]} caméras chiffrées, {CC.NB_CAMERAS} au plan de câblage")
    else:
        print("  ⚠ chiffrage sans catégorie « Sûreté » : quantités du lot 4 prises au plan de câblage")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    controles()
    doc_charte()
    doc_volet()
    doc_pra()
    doc_guide()
    for lot in CC.LOTS:
        doc_cctp(lot)
    readme()


if __name__ == "__main__":
    main()
