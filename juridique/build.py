#!/usr/bin/env python3
"""Point 19 · Aspects juridiques et chartes : produit livrables/juridique/.

Usage : python3 juridique/build.py   (après securite/build.py et cablage/plan_cablage.py)
Entrées : juridique/donnees.py (registre, AIPD, journaux, crise), pra.py, charte.py, cctp.py ; securite/pssi.py (mesures M-xx)
Sorties : livrables/juridique/
  charte_informatique.pdf   charte des utilisateurs + annexe administrateurs + annexe IA
  volet_juridique.pdf       cadre légal, registre des traitements, AIPD, politique de journalisation, IA, gestion de crise
  pra_juridique.pdf         PRA, volet juridique : obligations, exigences de reprise pour le point 15, contrats, preuves, calendrier
  cctp_lot1..4.pdf          modèles de CCTP pour le client
  guide_cdc_cctp.pdf        construire un cahier des charges et un CCTP
"""
import datetime
import html
import importlib.util
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ROOT / "securite"))
import charte as CH  # noqa: E402
import cctp as CC  # noqa: E402
import donnees as J  # noqa: E402
import pra as PRA  # noqa: E402
import pssi as PP  # noqa: E402

_spec = importlib.util.spec_from_file_location("securite_build", ROOT / "securite" / "build.py")
SB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SB)
tableau, pdf = SB.tableau, SB.pdf

OUT = ROOT / "livrables" / "juridique"
e = html.escape
DATE = datetime.date.today().strftime("%d/%m/%Y")
CSS = SB.CSS + SB.CSS_RISQUE + """
.charte h2 { font-size: 12pt; } .charte p { text-align: justify; }
.art { page-break-inside: avoid; margin-bottom: 2mm; }
.alerte { border-left: 3px solid #B3261E; background: #FBE9E7; padding: 2mm 3mm; margin: 3mm 0; }
.note-dpo { border-left: 3px solid #1F4E8C; background: #EEF3FA; padding: 2mm 3mm; margin: 3mm 0; }
.signature { margin-top: 10mm; display: grid; grid-template-columns: 1fr 1fr; gap: 10mm; }
.reprise { table-layout: fixed; width: 100%; } .reprise td:first-child b, .pra td:first-child b { white-space: normal; }
.reprise th:nth-child(1) { width: 15%; } .reprise th:nth-child(2) { width: 12%; } .reprise th:nth-child(3) { width: 8%; }
.reprise th:nth-child(4) { width: 20%; } .reprise th:nth-child(5), .reprise th:nth-child(6) { width: 9%; } .reprise th:nth-child(7) { width: 27%; }
.signature div { border-top: 1px solid #6C6861; padding-top: 2mm; font-size: 8pt; color: #6C6861; }
"""
PSSI = {m[0]: m for m in PP.MESURES}


def entete(titre, sous, point="19"):
    return [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{e(titre)}</title><style>{CSS}</style></head><body>",
            f"<h1>{e(titre)}</h1>",
            f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · point {point} du cahier des charges · "
            f"version {J.VERSION} · {DATE}<br>{sous}</p>"]


AVERTISSEMENT = ("<div class='note-dpo'><b>Nature du document.</b> Proposition du concepteur, rédigée pour aider le client. Ce n'est pas "
                 "un avis juridique : chaque choix (base légale, durée, régime de la vidéoprotection) est à valider par le DPO et le service "
                 "juridique de l'AMU avant d'être appliqué.</div>")


# ---------------------------------------------------------------------------
# Charte
# ---------------------------------------------------------------------------
def articles(liste, prefixe=""):
    H = []
    for i, (titre, pars) in enumerate(liste, 1):
        H.append(f"<div class='art'><h3>{prefixe}{i}. {e(titre)}</h3>" + "".join(f"<p>{e(p)}</p>" for p in pars) + "</div>")
    return "".join(H)


def doc_charte():
    H = entete("Charte informatique", "Règles d'usage des moyens informatiques de l'IUT. À annexer au règlement intérieur de l'AMU, "
               "après consultation du comité social d'administration (CSA).")
    H += ["<div class='charte'>", f"<p><b>{e(CH.PREAMBULE)}</b></p>", articles(CH.ARTICLES),
          "<h2 class='saut'>Annexe A · Administrateurs</h2><p>Les personnes qui disposent de droits d'administration (personnels "
          "et prestataires) s'engagent en plus sur ce qui suit.</p>", articles(CH.ANNEXE_ADMIN, "A."),
          "<div class='signature'><div>Nom, fonction, date</div><div>Signature de l'administrateur</div></div>",
          "<h2 class='saut'>Annexe B · Usage de la plateforme d'IA</h2>", articles(CH.ANNEXE_IA, "B."),
          "</div>",
          "<h2>Mise en œuvre</h2><ul>"
          "<li><b>Opposabilité</b> : la charte est annexée au règlement intérieur, ce qui la rend applicable aux étudiants et aux agents ; "
          "pour les personnels, le CSA est consulté avant, car elle décrit des moyens de contrôle de leur activité.</li>"
          "<li><b>Information</b> : remise à l'inscription et à l'arrivée, acceptée à la première connexion, affichée sur le portail.</li>"
          "<li><b>Révision</b> : à chaque évolution notable des moyens de contrôle (journaux, inspection TLS, vidéoprotection), avec la PSSI.</li>"
          "<li><b>Cohérence</b> : les durées citées sont celles de la politique de journalisation (volet juridique, section 4).</li></ul>",
          "</body></html>"]
    return "\n".join(H)


# ---------------------------------------------------------------------------
# Volet juridique
# ---------------------------------------------------------------------------
def doc_volet():
    H = entete("Volet juridique", "Cadre légal, registre des traitements, analyses d'impact, politique de journalisation, intelligence "
               "artificielle, gestion d'une crise d'origine cyber.")
    H.append(AVERTISSEMENT)
    H += ["<div class='cles'>", f"<div class='cle'><b>{len(J.TRAITEMENTS)}</b>traitements au registre</div>",
          f"<div class='cle'><b>{len(J.AIPD)}</b>analyses d'impact</div>",
          f"<div class='cle'><b>{len(J.JOURNAUX)}</b>types de journaux encadrés</div>",
          f"<div class='cle'><b>{len(J.NOTIFICATIONS)}</b>notifications en cas de crise</div></div>"]
    # 1. Cadre
    H += ["<h2>1. Cadre légal applicable</h2>",
          tableau(["Texte", "Ce qu'il impose au projet"], [
              [e(J.TEXTES["RGPD"]) + "<br>" + e(J.TEXTES["LIL"]), "Registre, information des personnes, sécurité, AIPD pour les traitements "
               "à risque, notification des violations sous 72 h. Le DPO est obligatoire pour une autorité publique : celui de l'AMU."],
              [e(J.TEXTES["CPCE"]) + "<br>" + e(J.TEXTES["LCEN"]), "Conserver un an les données qui identifient l'auteur d'une connexion "
               "(pas le contenu) et les fournir sur réquisition."],
              [e(J.TEXTES["CSI"]), "Caméras filmant un lieu ouvert au public : autorisation du préfet, information, durée limitée (un mois au plus). "
               "Ailleurs (locaux non ouverts au public), le RGPD seul s'applique."],
              [e(J.TEXTES["CT"]) + "<br>" + e(J.TEXTES["CGFP"]), "Un contrôle de l'activité des personnels doit être justifié, proportionné, "
               "connu à l'avance ; les instances représentatives sont consultées."],
              [e(J.TEXTES["CP-STAD"]) + "<br>" + e(J.TEXTES["CP-CORR"]), "Fonde les sanctions de la charte ; protège les messages "
               "personnels, y compris contre les administrateurs."],
              [e(J.TEXTES["AIA"]), "Formation des utilisateurs à l'IA, usages interdits (reconnaissance des émotions dans l'enseignement), "
               "usages à haut risque (évaluation, admission, surveillance des examens)."],
              [e(J.TEXTES["NIS2"]), "Hypothèse retenue : entité concernée. Gouvernance, gestion des risques, notification des incidents "
               "(24 h, 72 h, 1 mois)."],
              [e(J.TEXTES["CCP"]), "Marchés : égalité des candidats (« ou équivalent »), allotissement, critère et clauses environnementales."],
              [e(J.TEXTES["CPI"]), "Licences des logiciels, droits sur les contenus ; rappelé dans la charte."]])]
    # 2. Registre
    H += ["<div class='paysage'><h2>2. Registre des traitements (RGPD art. 30)</h2>",
          "<p>Responsable de traitement : l'AMU, représentée sur le site par le directeur de l'IUT. Seuls les traitements créés ou "
          "touchés par l'infrastructure figurent ici ; ils sont à reporter dans le registre de l'AMU. Aucun transfert hors de l'Union "
          "européenne : tout est hébergé sur le site, et la sauvegarde externalisée reste en France (SecNumCloud).</p>",
          tableau(["", "Traitement", "Finalité", "Base légale", "Personnes", "Données", "Destinataires", "Durée", "Sécurité", "AIPD"],
                  [[f"<b>{c}</b>", f"<b>{e(n)}</b><br><span class='ref'>{e(pt)}</span>", e(fi), e(J.BASES[b]), e(pe), e(do), e(de), e(du),
                    e(me), "<b class='ko'>oui</b>" if a == "oui" else "non"]
                   for c, n, fi, b, pe, do, de, du, me, a, pt in J.TRAITEMENTS], cls="regles"),
          "<p class='sous'>T10 (géolocalisation) figure au registre parce qu'elle est envisagée par le point 13 ; l'AIPD conclut "
          "qu'il ne faut pas la mettre en œuvre (section 3).</p></div>"]
    # 3. AIPD
    H.append("<h2>3. Analyses d'impact (AIPD, RGPD art. 35)</h2>"
             "<p>Une AIPD est due quand un traitement réunit au moins deux critères des lignes directrices du CEPD. Gravité et vraisemblance "
             "notées de 1 à 4, comme dans la méthode de la CNIL.</p>")
    noms = {t[0]: t[1] for t in J.TRAITEMENTS}
    for code, a in J.AIPD.items():
        H.append(f"<div class='fiche'><h3>{code} · {e(noms[code])}</h3>"
                 f"<p><b>Critères</b> : {e(', '.join(J.CRITERES[c] for c in a['criteres']))}.</p>"
                 f"<p><b>Nécessité</b> : {e(a['necessite'])}</p><p><b>Proportionnalité</b> :</p><ul>"
                 + "".join(f"<li>{e(x)}</li>" for x in a["proportion"]) + "</ul>"
                 + tableau(["Risque pour les personnes", "Gravité", "Vraisemblance", "Mesures"],
                           [[e(r), str(g), str(v), e(m)] for r, g, v, m in a["risques"]])
                 + f"<p><b>Conclusion</b> : {e(a['conclusion'])}</p></div>")
    H.append("<h3>Les 15 caméras du plan de câblage</h3><p>Le régime dépend du lieu filmé. Classement proposé, à valider par le DPO :</p>")
    H.append(tableau(["Prise", "Niveau", "Lieu", "Régime", "Point d'attention"],
                     [[c, n, e(s), ("<b class='ko'>" + r + "</b>") if r == "à retirer" else e(r), e(t)] for c, n, s, r, t in J.cameras()]))
    H.append("<div class='alerte'><b>À corriger dans le plan de câblage (point 04)</b> : la caméra du foyer des étudiants (N0-LT01-P050). "
             "Le foyer est un lieu de vie : la CNIL considère que filmer les lieux de pause est disproportionné. Proposition : la remplacer "
             "par une caméra sur la porte du foyer, côté circulation, ou la supprimer.</div>")
    # 4. Journalisation
    H += ["<h2 class='saut'>4. Politique de journalisation</h2>",
          "<p>Ce que l'on garde, combien de temps et qui peut le lire. La chaîne technique (collecte, scellement, archives) est décrite "
          "dans l'architecture L3 (section 10) et la PSSI (M-DET-1).</p>",
          tableau(["Journal", "Sources", "Contenu", "Finalité", "Durée", "Accès", "Registre"], [[e(x) for x in j] for j in J.JOURNAUX]),
          "<h3>Ce qui est interdit</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in J.INTERDITS_JOURNAUX) + "</ul>",
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
          "<p>La plateforme d'IA locale (point 11) fait de l'IUT un <b>déployeur</b> d'un modèle d'IA à usage général, au sens de l'AI Act. "
          "Il en devient <b>fournisseur</b> s'il modifie substantiellement le modèle (réentraînement) ou le met sur le marché sous son nom, "
          "ce qui n'est pas prévu.</p>",
          tableau(["Obligation", "Ce que l'on prévoit", "Depuis"], [
              ["Maîtrise de l'IA (art. 4) : former les personnes qui utilisent le système", "Formation courte demandée avant le premier "
               "usage (annexe B de la charte)", "2 février 2025"],
              ["Pratiques interdites (art. 5), dont la reconnaissance des émotions dans les établissements d'enseignement", "Interdit par la "
               "charte et absent de la plateforme", "2 février 2025"],
              ["Usages à haut risque (annexe III, point 3) : admission, évaluation des acquis, surveillance des examens", "Exclus de la "
               "plateforme ; tout projet de ce type passerait par une analyse et une conformité dédiées", "2 août 2026"],
              ["Transparence (art. 50) : signaler qu'on échange avec une IA, marquer certains contenus générés", "Mention permanente dans "
               "l'interface ; règle de citation dans la charte", "2 août 2026"],
              ["RGPD", "AIPD T08, durées courtes, pas de réentraînement sur les requêtes", "—"]]),
          "<p class='sous'>Le calendrier des obligations « haut risque » peut être décalé par la proposition « omnibus numérique » de la "
          "Commission (novembre 2025) : à vérifier à la date de mise en service.</p>"]
    # 6. Crise
    H += ["<h2 class='saut'>6. Gestion d'une crise d'origine cyber (volet gouvernance du PRA)</h2>",
          "<p>Le PRA technique (sauvegardes, RPO/RTO, ordre de restauration) est au point 15. Ici : qui décide, qui prévient qui, et dans "
          "quels délais. Inspiré des guides de l'ANSSI sur la gestion de crise et du kit d'exercice dédié à l'enseignement supérieur. "
          "Le document <b>PRA, volet juridique</b> (pra_juridique.pdf) complète cette section : obligations de continuité, exigences de "
          "reprise par service données au point 15, contrats, preuves et calendrier légal des premières heures.</p>",
          "<h3>Cellule de crise</h3>", tableau(["Rôle", "Qui", "Mission"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in J.CELLULE]),
          "<p>Elle se réunit hors du SI touché : liste de contacts imprimée, téléphones portables, une salle prévue à l'avance, une messagerie "
          "de secours qui ne dépend pas de l'annuaire.</p>",
          "<h3>Qui prévenir, et quand</h3>",
          tableau(["Qui", "Quand", "Délai", "Par qui", "Texte"], [[f"<b>{e(a)}</b>", e(b), e(c), e(d), e(t)] for a, b, c, d, t in J.NOTIFICATIONS]),
          "<h3>Fiches réflexes</h3>"]
    for titre, etapes in J.FICHES_REFLEXES:
        H.append(f"<div class='fiche'><h3>{e(titre)}</h3><ol>" + "".join(f"<li>{e(x)}</li>" for x in etapes) + "</ol></div>")
    H += ["<h3>S'entraîner</h3><p>Un exercice par an avec le kit de l'ANSSI pour l'enseignement supérieur (scénario rançongiciel en période "
          "d'examens), puis un retour d'expérience qui met à jour la PSSI, l'analyse de risque et ces fiches.</p>",
          "<h2>7. Points à faire valider par le DPO et le service juridique</h2><ul>"
          "<li>Régime de chaque caméra (lieu ouvert au public ou non) et retrait de la caméra du foyer.</li>"
          "<li>Durées de conservation, en particulier pour la plateforme d'IA (30 jours de contenus).</li>"
          "<li>Abandon de la géolocalisation des étudiants (T10) au profit d'un émargement en salle.</li>"
          "<li>Calendrier de consultation du CSA pour la charte et la vidéoprotection.</li>"
          "<li>Statut NIS 2 de l'établissement une fois la loi promulguée, et désignation des contacts auprès de l'ANSSI.</li></ul>",
          "</body></html>"]
    return "\n".join(H)


# ---------------------------------------------------------------------------
# PRA, volet juridique
# ---------------------------------------------------------------------------
def doc_pra():
    H = entete("Plan de reprise d'activité · volet juridique", "Ce que le droit impose à la reprise du site après un sinistre ou une "
               "cyberattaque, et ce que le PRA technique du point 15 doit donc garantir.")
    H.append(AVERTISSEMENT)
    H += ["<div class='cles'>", f"<div class='cle'><b>{len(PRA.OBLIGATIONS)}</b>obligations de continuité</div>",
          f"<div class='cle'><b>{len(PRA.SERVICES)}</b>services avec DMIA et PDMA</div>",
          f"<div class='cle'><b>{len(PRA.CONTRATS)}</b>contrats à clauses de reprise</div>",
          "<div class='cle'><b>72 h</b>CNIL, ANSSI et plainte</div></div>",
          "<h2>1. Partage avec le point 15</h2>",
          tableau(["", "Ce document (point 19)", "PRA technique (point 15)"], [
              ["<b>Question</b>", "Qu'est-ce que la loi et les contrats exigent ?", "Comment on sauvegarde et on restaure ?"],
              ["<b>Contenu</b>", "obligations, DMIA et PDMA exigées, règles de restauration, contrats, preuves, notifications, gouvernance",
               "sauvegardes, réplication vers le site jumeau, ordre et procédures de restauration, tests"],
              ["<b>Valide</b>", "DPO, service juridique, direction", "RSSI, administrateurs"]]),
          "<p><b>DMIA</b> : durée maximale d'interruption admissible (RTO). <b>PDMA</b> : perte de données maximale admissible (RPO).</p>",
          "<h2>2. Obligations de continuité</h2>",
          tableau(["Obligation", "Texte", "Ce qu'il impose", "Conséquence pour le PRA"],
                  [[f"<b>{e(a)}</b>", e(b), e(c), e(d)] for a, b, c, d in PRA.OBLIGATIONS], cls="pra"),
          "<h2 class='saut'>3. Exigences de reprise par service</h2>",
          "<p>Pour chaque service, l'enjeu juridique fixe une durée d'interruption et une perte de données admissibles. Ce sont les "
          "exigences d'entrée du PRA technique. Les codes Txx renvoient au registre des traitements (volet juridique, section 2).</p>",
          tableau(["Service", "Serveurs", "Registre", "Enjeu juridique", "DMIA", "PDMA", "Mode dégradé"],
                  [[f"<b>{e(a)}</b>", e(b), e(c), e(d), e(f), e(g), e(m)] for a, b, c, d, f, g, m in PRA.SERVICES], cls="reprise"),
          f"<p class='sous'>{e(PRA.NOTE_SERVICES)}</p>",
          "<h2>4. Restaurer sans enfreindre le droit</h2>"]
    for titre, texte in PRA.REGLES_RESTAURATION:
        H.append(f"<div class='fiche'><h3>{e(titre)}</h3><p>{e(texte)}</p></div>")
    H += ["<h2 class='saut'>5. Contrats : clauses de reprise à prévoir</h2>",
          tableau(["Contrat", "Clause", "Pourquoi", "Où"], [[f"<b>{e(a)}</b>", e(b), e(c), e(d)] for a, b, c, d in PRA.CONTRATS], cls="pra"),
          "<h2>6. Calendrier légal d'une crise</h2>",
          "<p>H0 : le moment où l'incident est connu. Les délais courent dès cette heure-là, y compris la nuit et le week-end.</p>",
          tableau(["Échéance", "Action", "Qui", "Texte"], [[f"<b>{e(a)}</b>", e(b), e(c), e(d)] for a, b, c, d in PRA.CALENDRIER]),
          "<h3>Cellule de crise</h3>",
          tableau(["Rôle", "Qui", "Mission"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in J.CELLULE]),
          "<p>Détail des notifications et fiches réflexes : volet juridique, section 6.</p>",
          "<h2 class='saut'>7. Ce que le point 15 doit livrer</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in PRA.EXIGENCES_P15) + "</ul>",
          "<h2>8. Faire vivre le PRA</h2>",
          tableau(["Quoi", "Qui", "Quand"], [[f"<b>{e(a)}</b>", e(b), e(c)] for a, b, c in PRA.GOUVERNANCE]),
          "<h2>9. Points à faire valider</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in PRA.A_VALIDER) + "</ul>",
          "</body></html>"]
    return "\n".join(H)


# ---------------------------------------------------------------------------
# CCTP
# ---------------------------------------------------------------------------
def doc_cctp(lot):
    H = entete(f"CCTP · Lot {lot['num']} : {lot['titre']}", "Modèle de cahier des clauses techniques particulières, à compléter par les "
               "services achats de l'AMU (CCAP, règlement de la consultation, bordereau de prix).")
    H.append("<div class='note-dpo'><b>Modèle.</b> Les références de produits sont celles du chiffrage du projet, données à titre "
             "indicatif : dans le marché, chacune est suivie de « ou équivalent ». Les exigences numérotées sont vérifiées à la recette.</div>")
    if lot.get("attention"):
        H.append(f"<div class='alerte'><b>Avant la consultation</b> : {e(lot['attention'])}</div>")
    H += ["<h2>1. Objet</h2>", f"<p>{e(lot['objet'])}</p>", f"<p><b>Hors du lot</b> : {e(lot['hors_lot'])}</p>",
          "<h2>2. Documents de référence</h2><p>Dossier de conception RudyLink Infrastructure, version 2 de l'infrastructure : "
          + ", ".join(e(r) for r in lot["references"]) + ".</p>",
          "<h2>3. Quantités</h2>",
          tableau(["Repère", "Désignation (indicative)", "Quantité", "Remarque"],
                  [[e(a), e(b) + " <i>ou équivalent</i>", str(q), e(n)] for a, b, q, n in lot["quantites"]]),
          "<h2>4. Exigences techniques</h2>"]
    k = 0
    for titre, liste in lot["exigences"]:
        H.append(f"<h3>{e(titre)}</h3>")
        lignes = []
        for x in liste:
            k += 1
            lignes.append([f"<b>L{lot['num']}-{k:02d}</b>", e(x), "☐"])
        H.append(tableau(["N°", "Exigence", "Conforme"], lignes))
    H.append("<h2 class='saut'>5. Clauses communes à tous les lots</h2>")
    for titre, liste in CC.COMMUNES.items():
        H.append(f"<h3>{e(titre)}</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in liste) + "</ul>")
    H.append("<h2>6. Réponse attendue du candidat</h2><ul>"
             "<li>Un mémoire technique qui reprend chaque exigence numérotée et indique comment elle est satisfaite (ou l'écart proposé).</li>"
             "<li>Les fiches techniques, la consommation électrique, les dates de fin de support et la politique de correctifs.</li>"
             "<li>Le plan de recette proposé et le planning d'intervention, compatible avec le calendrier universitaire.</li></ul>"
             "</body></html>")
    return "\n".join(H)


def doc_guide():
    H = entete("Construire un cahier des charges et un CCTP", "Guide pour le client : quelles pièces écrire, dans quel ordre, et "
               "comment utiliser les modèles de CCTP de ce dossier.")
    H += ["<h2>1. Les pièces d'un marché</h2>", tableau(["Pièce", "Rôle"], [[f"<b>{e(a)}</b>", e(b)] for a, b in CC.PIECES]),
          "<h2>2. Démarche</h2><ol>" + "".join(f"<li>{e(x)}</li>" for x in CC.DEMARCHE) + "</ol>",
          "<h2>3. Sommaire type d'un cahier des charges</h2><ol>" + "".join(f"<li>{e(x)}</li>" for x in CC.SOMMAIRE_CDC) + "</ol>",
          "<h2>4. Les quatre modèles de CCTP</h2>",
          tableau(["Lot", "Objet", "Fichier"], [[str(l["num"]), e(l["titre"]), f"<code>cctp_lot{l['num']}.pdf</code>"] for l in CC.LOTS]),
          "<p>Le lot énergie et locaux techniques (onduleurs, climatisation, extinction, baies) reprend l'étude du point 14 ; les prestations "
          "d'intégration et de recette du chiffrage sont réparties dans les lots.</p>",
          "<h2>5. Où sont les exigences de sécurité</h2><p>Les clauses communes reprennent la PSSI : "
          + ", ".join(f"{c} ({e(PSSI[c][2])})" for c in ("M-ADM-2", "M-ADM-3", "M-POS-2", "M-FOU-1")) + ". Les tests de recette du filtrage "
          "sont ceux de la matrice des flux. Une exigence de sécurité écrite dans le CCTP coûte peu ; la même, ajoutée après la livraison, "
          "coûte un avenant.</p></body></html>"]
    return "\n".join(H)


def main():
    PP.verifier()
    OUT.mkdir(parents=True, exist_ok=True)
    docs = [("charte_informatique", doc_charte), ("volet_juridique", doc_volet), ("pra_juridique", doc_pra), ("guide_cdc_cctp", doc_guide)]
    docs += [(f"cctp_lot{l['num']}", (lambda l=l: doc_cctp(l))) for l in CC.LOTS]
    for nom, f in docs:
        page = OUT / f"{nom}.html"
        page.write_text(f(), encoding="utf-8")
        pdf(page, OUT / f"{nom}.pdf")
        print(f"  {page.relative_to(ROOT)} -> .pdf")
    (OUT / "README.md").write_text(
        "# Aspects juridiques et chartes (point 19)\n<!-- onglet: Juridique -->\n\n"
        "| Document | Contenu |\n|---|---|\n"
        "| **[charte_informatique.pdf](charte_informatique.pdf)** | Charte des utilisateurs, annexe A administrateurs, annexe B usage de l'IA |\n"
        "| **[volet_juridique.pdf](volet_juridique.pdf)** | Cadre légal, registre des traitements, AIPD (vidéoprotection, IA, géolocalisation), "
        "politique de journalisation, AI Act, gestion de crise (volet gouvernance du PRA) |\n"
        "| **[pra_juridique.pdf](pra_juridique.pdf)** | PRA, volet juridique : obligations de continuité, DMIA et PDMA exigées par service "
        "(entrée du point 15), règles de restauration, contrats, calendrier légal des 72 premières heures |\n"
        "| **[guide_cdc_cctp.pdf](guide_cdc_cctp.pdf)** | Construire un cahier des charges et un CCTP |\n"
        + "".join(f"| [cctp_lot{l['num']}.pdf](cctp_lot{l['num']}.pdf) | CCTP lot {l['num']} : {l['titre']} |\n" for l in CC.LOTS)
        + "\nRégénérer : `python3 juridique/build.py` (sources : `juridique/donnees.py`, `charte.py`, `cctp.py`). "
          "Propositions du concepteur, à valider par le DPO et le service juridique de l'AMU.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
