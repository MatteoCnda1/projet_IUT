#!/usr/bin/env python3
"""Vérification orthographique ciblée (non bloquante) : fautes fréquentes du français, sur le texte des livrables.

    python3 outils/ci/orthographe.py            avertissements seulement, code retour 0
    python3 outils/ci/orthographe.py --strict   code retour 1 s'il reste une faute

Pas de dictionnaire général (codespell et consorts sont anglais : des centaines de faux positifs sur un dépôt français),
mais une liste courte de fautes qu'on sait reconnaître sans ambiguïté. Textes lus : Markdown suivis par git et HTML de
livrables/ (hors archives), sans le code (blocs ``` et `…`, <code>, <pre>, <style>, <script>).
Ajouter une faute : une ligne dans FAUTES (motif, correction). Bibliothèque standard seulement.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sortie_ci import RACINE, Rapport, fichiers_suivis  # noqa: E402

FAUTES = [
    (r"\baddresse\b", "adresse"),
    (r"\bparmis\b", "parmi"),
    (r"\bmalgrés\b", "malgré"),
    (r"\bmalgré qu", "bien que (+ subjonctif)"),
    (r"\bquelque soi(?:en)?t\b", "quel(le)(s) que soit / soient"),
    (r"\bd[ée]v[ée]lop(?!p)\w*|\bd[ée]v[ée]ll\w*|\bdevelopp\w*", "développement, développer"),
    (r"\benvironement\w*", "environnement"),
    (r"\bnott?ament\b", "notamment"),
    (r"\bapparament\b", "apparemment"),
    (r"\baggrég\w*|\baggregats?\b", "agrégat, agréger (un seul g)"),  # pas « aggregatable » (anglais, IPv6)
    (r"\brédondan\w*", "redondance, redondant"),
    (r"\b(?:nécéss|nécesaire|neccess|necessaire)\w*", "nécessaire"),
    (r"\boccurences?\b", "occurrence"),
    (r"\bparamêtres?\b", "paramètre"),
    (r"\b(?:acc|succ|proc|exc)és\b", "accès, succès, procès, excès"),
    (r"\bsytèmes?\b", "système"),
    (r"\ben terme de\b", "en termes de"),
    (r"\bpallier à\b", "pallier (sans « à »)"),
    (r"\brésaux\b", "réseaux"),
    (r"\bd[ée]pendences?\b", "dépendance"),
    (r"\bindépendemment\b", "indépendamment"),
    (r"\bfréquement\b", "fréquemment"),
    (r"\brécement\b", "récemment"),
    (r"\bamm[ée]lior\w*", "amélioration, améliorer"),
    (r"\bhébergment\w*", "hébergement"),
    (r"\bcyber-sécurité\b", "cybersécurité"),
    (r"\bconnection\b", "connexion (en français)"),
    (r"\blanguage\b", "langage (en français)"),
    (r"\bcrypt(?:age|er|ée?s?)\b", "chiffrement, chiffrer (vocabulaire ANSSI)"),
    (r"\b(le|la|les|de|des|du|un|une|et|en|à|que|qui|pour|par|sur|dans|est|ne|pas)\s+\1\b", "mot répété"),
    (r"(?<![.\w/])\.\.(?![./\w])", "double point"),
]
MOTIFS = [(re.compile(m, re.IGNORECASE), c) for m, c in FAUTES]

CODE_MD = re.compile(r"```.*?```|`[^`\n]*`", re.S)
CODE_HTML = re.compile(r"<(style|script|code|pre)\b.*?</\1>", re.S | re.I)
BALISE = re.compile(r"<[^>]+>")


def texte_lisible(chemin, brut):
    """Texte à relire, en gardant les retours à la ligne (pour donner le bon numéro de ligne)."""
    blanc = lambda m: re.sub(r"[^\n]", " ", m.group(0))  # noqa: E731
    if chemin.endswith(".md"):
        return CODE_MD.sub(blanc, brut)
    sans_code = BALISE.sub(blanc, CODE_HTML.sub(blanc, brut))
    return html.unescape(sans_code)


def main(args):
    strict = "--strict" in args
    r = Rapport("Orthographe (fautes fréquentes, non bloquant)")
    r.section("Fautes fréquentes dans les Markdown et les HTML de livrables/")
    suivis = fichiers_suivis() or []
    fichiers = [p for p in suivis if p.endswith(".md") or (p.startswith("livrables/") and p.endswith(".html"))]
    fichiers = [p for p in fichiers if "/archives/" not in p]
    for p in sorted(fichiers):
        texte = texte_lisible(p, (RACINE / p).read_text(encoding="utf-8", errors="replace"))
        for motif, correction in MOTIFS:
            for m in motif.finditer(texte):
                ligne = texte.count("\n", 0, m.start()) + 1
                r.avert(f"« {m.group(0)} » → {correction}", p, ligne)
    if not r.avertissements:
        r.ok(f"{len(fichiers)} fichiers relus, aucune des {len(FAUTES)} fautes suivies")
    code = r.bilan()
    return 1 if strict and r.avertissements else code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
