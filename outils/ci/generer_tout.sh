#!/usr/bin/env bash
# Chaîne complète de génération des livrables, dans l'ordre des dépendances entre scripts.
#
#   bash outils/ci/generer_tout.sh            depuis la racine du dépôt (ou d'ailleurs : le script s'y place)
#   bash outils/ci/generer_tout.sh --strict   outil système absent = erreur (c'est le mode de la CI)
#   PYTHON=.venv/bin/python bash outils/ci/generer_tout.sh
#
# Ordre (qui lit quoi) :
#   cablage/salles.py            plans PDF            -> cablage/build/ (non suivi par git)
#   cablage/etude_rssi.py        cablage/build/       -> livrables/plan_cablage/wifi/
#   cablage/plan_cablage.py      + wifi/bornes.json   -> livrables/plan_cablage/ (resume.json lu par presque tout le reste)
#   cablage/rapport.py           resume.json          -> livrables/plan_cablage/README.md
#   architecture/reseau/build.py resume.json          -> plan d'adressage, architectures L2 et L3, schémas drawio
#   energie/energie.py           resume.json + lignes fixes de chiffrage/estimation.json -> livrables/energie_refroidissement/
#   chiffrage/estimation.py      resume.json + energie_refroidissement/resume.json        -> chiffrage/estimation.*
#   communication/build.py       chiffrage, énergie, câblage (copie leurs PDF dans site_web/documents/)
#   roadmap/build.py             chiffrage/estimation.json -> roadmap/index.html
#   securite/build.py            architecture/reseau/donnees.py -> livrables/securite/
#   juridique/build.py           securite/, chiffrage, plan de câblage -> livrables/juridique/
#   architecture/audit/generer_rapport_audit.py   rapport d'audit du 15/11/2026 (texte figé)
#   architecture/audit/traitement_audit.py        relit plan d'adressage, énergie et chiffrage -> livrables/audit/
#
# Boucle connue : cablage/plan_cablage.py (implantation.html) relit la liste des équipements de chiffrage/estimation.json,
# qui dépend elle-même du plan de câblage. Partant d'un état cohérent (celui de git), un seul passage suffit ; après une
# modification de chiffrage/estimation.py qui ajoute ou retire un équipement, relancer la chaîne une seconde fois.
set -euo pipefail

cd "$(dirname "$0")/../.."
PYTHON="${PYTHON:-python3}"
STRICT=0
[[ "${1:-}" == "--strict" ]] && STRICT=1

# Groupes repliables dans le journal GitHub Actions, texte simple en local
debut() { if [[ -n "${GITHUB_ACTIONS:-}" ]]; then echo "::group::$1"; else echo "== $1"; fi; }
fin()   { if [[ -n "${GITHUB_ACTIONS:-}" ]]; then echo "::endgroup::"; fi; }

manque=0
outil() {  # outil <nom affiché> <commande>... : au moins une des commandes doit exister
    local nom=$1; shift
    for c in "$@"; do
        if command -v "$c" >/dev/null 2>&1; then echo "✔ $nom : $(command -v "$c")"; return; fi
    done
    echo "✘ $nom introuvable ($*)"
    manque=1
}
debut "Outils système"
"$PYTHON" --version
outil "poppler (pdftotext)" pdftotext
outil "poppler (pdftoppm)" pdftoppm
outil "Chrome / Chromium" google-chrome chromium
outil "CLI draw.io" drawio
fin
if (( manque )); then
    if (( STRICT )); then echo "✘ outil manquant : arrêt (mode --strict)"; exit 1; fi
    echo "⚠ outil manquant : les PDF ou PNG correspondants ne seront pas régénérés"
fi

ETAPES=(
    cablage/salles.py
    cablage/etude_rssi.py
    cablage/plan_cablage.py
    cablage/rapport.py
    architecture/reseau/build.py
    energie/energie.py
    chiffrage/estimation.py
    communication/build.py
    roadmap/build.py
    securite/build.py
    juridique/build.py
    architecture/audit/generer_rapport_audit.py
    architecture/audit/traitement_audit.py
)

total=$SECONDS
for etape in "${ETAPES[@]}"; do
    debut "$etape"
    t0=$SECONDS
    if ! "$PYTHON" "$etape"; then
        fin
        echo "✘ échec de $etape"
        exit 1
    fi
    fin
    echo "✔ $etape ($(( SECONDS - t0 )) s)"
done
echo "✔ chaîne complète en $(( SECONDS - total )) s"
