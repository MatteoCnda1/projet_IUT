#!/usr/bin/env python3
"""Après la chaîne de génération : les livrables suivis par git sont-ils à jour avec leurs sources ?

    touch /tmp/repere && bash outils/ci/generer_tout.sh && python3 outils/ci/verifier_a_jour.py --repere /tmp/repere
    python3 outils/ci/verifier_a_jour.py --patch maj_livrables.patch     (écrit le correctif des fichiers texte)

La référence est l'index git (le dernier commit sur un dépôt propre ; en local, `git add` ce qui doit servir de référence).
  - Fichiers texte (csv, json, md, html, drawio, css, txt, svg écrits par le projet) : ils doivent être identiques une fois
    neutralisées les dates de génération (liste VARIABLES ci-dessous). Une différence = livrable pas à jour : ✘.
  - Fichiers non comparables octet à octet (pdf, png, docx, pptx, svg de matplotlib) : pas de comparaison. Avec --repere,
    on vérifie qu'ils ont bien été produits par la chaîne (plus récents que le repère, non vides, du bon format).
  - Un fichier produit mais non suivi par git, ou supprimé par la chaîne : ✘.
Code retour 0 si tout est à jour, 1 sinon.
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sortie_ci import RACINE, Rapport, git  # noqa: E402

TEXTE = {".csv", ".json", ".md", ".html", ".drawio", ".css", ".txt", ".svg"}
# Dossiers où la chaîne écrit : un fichier non suivi qui y apparaît est un livrable oublié dans git
SORTIES = ("livrables/", "chiffrage/", "roadmap/", "architecture/")

# Ce qui change à chaque exécution, volontairement : (fichiers concernés, motif, remplacement, explication)
VARIABLES = [
    (re.compile(r"\.html$"), re.compile(r"(class='sous'>[^\n]*?· )\d{2}/\d{2}/\d{4}(<br>)"), r"\1<date>\2",
     "date de génération (sous-titre des documents)"),
    (re.compile(r"^livrables/plan_cablage/README\.md$"), re.compile(r"Généré le \d{2}/\d{2}/\d{4}"), "Généré le <date>",
     "date de génération du README du plan de câblage"),
]
# SVG produits par matplotlib : non comparables d'une machine à l'autre (version de matplotlib inscrite dans le
# fichier, métrique des polices, arrondis), même avec svg.hashsalt fixé et sans date -> seulement vérifiés comme produits
MATPLOTLIB = re.compile(rb"Created with matplotlib|<dc:date>|https://matplotlib\.org")

# Fichiers binaires que la chaîne doit réécrire à chaque passage (contrôle --repere).
# Le site vitrine (livrables/site_web/) est maintenu à la main par son auteur : la chaîne n'y écrit rien.
PRODUITS = re.compile(r"^(livrables/(?!archives/|depots/|site_web/).*\.(pdf|png|svg|docx|pptx)"
                      r"|architecture/[^/]+\.png|architecture/audit/[^/]+\.pdf)$")
SIGNATURES = {".pdf": b"%PDF-", ".png": b"\x89PNG", ".docx": b"PK\x03\x04", ".pptx": b"PK\x03\x04"}


def normaliser(chemin, contenu):
    texte = contenu.decode("utf-8", errors="replace")
    for fichiers, motif, rempl, _ in VARIABLES:
        if fichiers.search(chemin):
            texte = motif.sub(rempl, texte)
    return texte


def extrait(avant, apres, max_lignes=12, largeur=110):
    """Lignes qui diffèrent, coupées autour de la première différence (les HTML ont des lignes très longues)."""
    out = []
    for groupe in difflib.SequenceMatcher(None, avant, apres).get_grouped_opcodes(0):
        for tag, i1, i2, j1, j2 in groupe:
            if tag == "equal":
                continue
            moins, plus = avant[i1:i2], apres[j1:j2]
            for k in range(max(len(moins), len(plus))):
                a = moins[k] if k < len(moins) else ""
                b = plus[k] if k < len(plus) else ""
                col = next((n for n, (x, y) in enumerate(zip(a, b, strict=False)) if x != y), min(len(a), len(b)))
                d = max(0, col - largeur // 3)
                if a:
                    out.append(f"    - {'…' if d else ''}{a[d:d + largeur]}")
                if b:
                    out.append(f"    + {'…' if d else ''}{b[d:d + largeur]}")
                if len(out) >= max_lignes:
                    return out + ["    (…)"]
    return out


def etat_git():
    """[(XY, chemin)] de git status (arbre de travail comparé à l'index), fichiers non suivis compris."""
    git("update-index", "-q", "--really-refresh", verifier=False)  # copies qui gardent leur date (shutil.copy2)
    brut = git("status", "--porcelain=v1", "-z", "--untracked-files=all", binaire=True).split(b"\0")
    out, i = [], 0
    while i < len(brut):
        e = brut[i].decode("utf-8")
        i += 1
        if not e:
            continue
        xy, chemin = e[:2], e[3:]
        if xy[0] in "RC":
            i += 1  # renommage : le chemin d'origine suit
        out.append((xy, chemin))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repere", type=Path, help="fichier créé juste avant la chaîne : les binaires doivent être plus récents")
    ap.add_argument("--patch", type=Path, help="écrit ici le git diff des fichiers texte pas à jour")
    args = ap.parse_args()
    r = Rapport("Livrables à jour avec leurs sources")

    r.section("Fichiers texte comparés à git (dates de génération neutralisées)")
    pas_a_jour, dates_seules, binaires = [], [], 0
    for xy, chemin in etat_git():
        if xy == "??":
            if chemin.startswith(SORTIES):
                r.erreur("produit par la chaîne mais pas suivi par git : l'ajouter (ou l'ignorer dans .gitignore)", chemin)
            continue
        if xy[1] == "D":
            r.erreur("suivi par git mais supprimé ou plus produit par la chaîne", chemin)
            continue
        if xy[1] != "M":
            continue
        actuel = (RACINE / chemin).read_bytes()
        if Path(chemin).suffix.lower() not in TEXTE or MATPLOTLIB.search(actuel[:2000]):
            binaires += 1
            continue
        ref = git("show", f":{chemin}", binaire=True)
        a, b = normaliser(chemin, ref), normaliser(chemin, actuel)
        if a == b:
            dates_seules.append(chemin)
            continue
        pas_a_jour.append(chemin)
        r.erreur("pas à jour avec ses sources : la chaîne le régénère autrement", chemin)
        for ligne in extrait(a.splitlines(), b.splitlines()):
            print(ligne)
    if not pas_a_jour:
        r.ok("tous les fichiers texte suivis sont identiques à ce que produit la chaîne")
    if dates_seules:
        r.info(f"{len(dates_seules)} fichier(s) ne diffèrent que par la date de génération (neutralisée)")
    r.info(f"{binaires} fichier(s) binaires ou non reproductibles modifiés (non comparés : pdf, png, docx, pptx, svg matplotlib)")
    if pas_a_jour:
        r.info("Correction : relancer `bash outils/ci/generer_tout.sh` puis committer les livrables (dans la CI : "
               "artefacts « livrables-regeneres » et « correctif-livrables », à appliquer par git apply).")
        if args.patch:
            args.patch.write_text(git("diff", "--", *pas_a_jour), encoding="utf-8")
            r.info(f"correctif écrit dans {args.patch}")

    if args.repere:
        r.section("Fichiers binaires produits par la chaîne")
        t0 = args.repere.stat().st_mtime
        produits = [p for p in git("ls-files", "-z").split("\0") if PRODUITS.match(p)]
        manquants = 0
        for p in produits:
            f = RACINE / p
            if not f.exists() or f.stat().st_size == 0:
                r.erreur("absent ou vide après la chaîne", p)
                manquants += 1
            elif f.stat().st_mtime < t0:
                r.erreur("pas régénéré par la chaîne (outil absent : Chrome, draw.io ? étape sautée ?)", p)
                manquants += 1
            else:
                sig = SIGNATURES.get(f.suffix.lower())
                debut = f.read_bytes()[:4096]
                if (sig and not debut.startswith(sig)) or (f.suffix == ".svg" and b"<svg" not in debut):
                    r.erreur(f"contenu inattendu pour un {f.suffix}", p)
                    manquants += 1
        if not manquants:
            r.ok(f"{len(produits)} fichiers pdf / png / svg / docx / pptx régénérés, non vides et du bon format")
    return r.bilan()


if __name__ == "__main__":
    sys.exit(main())
