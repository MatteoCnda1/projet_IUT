"""Affichage commun aux scripts de outils/ci/ : ✔ / ✘ / ⚠ en local, annotations et résumé dans GitHub Actions.

Bibliothèque standard seulement (les contrôles doivent tourner sans rien installer).
"""
import contextlib
import os
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent.parent
GITHUB = bool(os.environ.get("GITHUB_ACTIONS"))
MAX_ANNOTATIONS = 40  # GitHub n'en affiche qu'une partie : au-delà, le journal suffit

# La console Windows ou un terminal mal réglé ne doivent pas faire échouer l'affichage des ✔ / ✘
for flux in (sys.stdout, sys.stderr):
    with contextlib.suppress(AttributeError):
        flux.reconfigure(encoding="utf-8", errors="replace")


def _echapper(texte):
    """Échappement des annotations GitHub (workflow commands)."""
    return str(texte).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


class Rapport:
    """Collecte les résultats d'une série de contrôles et produit le bilan."""

    def __init__(self, titre):
        self.titre = titre
        self.sections = []  # [titre, nb erreurs, nb avertissements]
        self.erreurs = 0
        self.avertissements = 0
        self._annotations = 0

    def section(self, titre):
        self.sections.append([titre, 0, 0])
        print(f"\n== {titre}")

    def ok(self, message):
        print(f"✔ {message}")

    def info(self, message):
        print(f"  {message}")

    def _annoter(self, niveau, message, fichier, ligne):
        if not GITHUB or self._annotations >= MAX_ANNOTATIONS:
            return
        self._annotations += 1
        loc = ""
        if fichier:
            loc = f" file={fichier}" + (f",line={ligne}" if ligne else "")
        titre = self.sections[-1][0] if self.sections else self.titre
        print(f"::{niveau}{loc},title={_echapper(titre)}::{_echapper(message)}")

    def erreur(self, message, fichier=None, ligne=None):
        self.erreurs += 1
        if self.sections:
            self.sections[-1][1] += 1
        lieu = f"{fichier}:{ligne} : " if fichier and ligne else (f"{fichier} : " if fichier else "")
        print(f"✘ {lieu}{message}")
        self._annoter("error", message, fichier, ligne)

    def avert(self, message, fichier=None, ligne=None):
        self.avertissements += 1
        if self.sections:
            self.sections[-1][2] += 1
        lieu = f"{fichier}:{ligne} : " if fichier and ligne else (f"{fichier} : " if fichier else "")
        print(f"⚠ {lieu}{message}")
        self._annoter("warning", message, fichier, ligne)

    def bilan(self):
        """Affiche le bilan, l'écrit dans le résumé GitHub et renvoie le code de retour (0 = tout va bien)."""
        en_erreur = sum(1 for _, e, _ in self.sections if e)
        print(f"\n== Bilan : {self.titre}")
        if self.erreurs:
            print(f"✘ {self.erreurs} erreur(s) dans {en_erreur} contrôle(s) sur {len(self.sections)}, "
                  f"{self.avertissements} avertissement(s)")
        else:
            print(f"✔ {len(self.sections)} contrôle(s) passé(s), {self.avertissements} avertissement(s)")
        resume = os.environ.get("GITHUB_STEP_SUMMARY")
        if resume:
            lignes = [f"### {self.titre}", "", "| Contrôle | Résultat |", "|---|---|"]
            for titre, e, a in self.sections:
                etat = f"✘ {e} erreur(s)" if e else "✔"
                if a:
                    etat += f" · ⚠ {a} avertissement(s)"
                lignes.append(f"| {titre} | {etat} |")
            with open(resume, "a", encoding="utf-8") as f:
                f.write("\n".join(lignes) + "\n\n")
        return 1 if self.erreurs else 0


def git(*args, binaire=False, verifier=True):
    """Lance git depuis la racine du dépôt et renvoie sa sortie (texte, ou octets si binaire=True)."""
    res = subprocess.run(["git", *args], cwd=RACINE, capture_output=True, check=verifier)
    return res.stdout if binaire else res.stdout.decode("utf-8", errors="replace")


def fichiers_suivis():
    """Chemins (relatifs à la racine) des fichiers suivis par git, ou None hors d'un dépôt git."""
    try:
        sortie = git("ls-files", "-z", binaire=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p.decode("utf-8") for p in sortie.split(b"\0") if p]
