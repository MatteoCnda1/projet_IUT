#!/usr/bin/env python3
"""Point 02 · Communication sur la société fictive : produit les livrables de livrables/communication/.

  python3 communication/build.py

Logos, PDF (charte, plaquette, organisation), modèles Office, societe.json (lu par GesTT),
puis copie des PDF livrés dans livrables/site_web/documents/. Le site lui-même (HTML, CSS)
s'édite à la main.
Les modèles Word et PowerPoint demandent python-docx et python-pptx ; sans eux, ils sont sautés.
"""
import shutil
import marque, rendu, documents

RACINE = documents.RACINE
SITE_DOCS = {
    "livrables/communication/charte_graphique.pdf": "charte_graphique.pdf",
    "livrables/communication/plaquette_rudylink_infrastructure.pdf": "plaquette_rudylink_infrastructure.pdf",
    "livrables/communication/organisation_projet.pdf": "organisation_projet.pdf",
    "livrables/plan_cablage/implantation.pdf": "plan_cablage_implantation.pdf",
    "livrables/plan_cablage/synoptique.pdf": "plan_cablage_synoptique.pdf",
    "livrables/energie_refroidissement/energie_refroidissement.pdf": "energie_refroidissement.pdf",
}


def main():
    print("logos :", len(marque.ecrire_logos(documents.SORTIE / "logo")), "fichiers SVG")
    print("PDF   :", ", ".join(documents.produire(rendu)))
    try:
        import bureautique
        print("Office:", ", ".join(bureautique.produire(rendu)))
    except ImportError as err:
        print(f"Office: sauté ({err.name} absent : pip install python-docx python-pptx)")
    dest = RACINE / "livrables" / "site_web" / "documents"
    dest.mkdir(parents=True, exist_ok=True)
    for src, nom in SITE_DOCS.items():
        shutil.copy2(RACINE / src, dest / nom)
    print("site  :", len(SITE_DOCS), "PDF copiés dans livrables/site_web/documents/")


if __name__ == "__main__":
    main()
