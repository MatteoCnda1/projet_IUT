#!/usr/bin/env python3
"""Point 02 · Communication sur la société fictive : produit les livrables de livrables/communication/.

  python3 communication/build.py

Logos, PDF (charte, plaquette, organisation), modèles Office, societe.json (lu par GesTT).
Le site vitrine (livrables/site_web/) n'est ni copié ni réécrit ici : il est maintenu à la main par son auteur.
Les modèles Word et PowerPoint demandent python-docx et python-pptx ; sans eux, ils sont sautés
(avec un avertissement : les modèles déjà livrés gardent alors leurs anciens chiffres).
"""
import marque, rendu, documents


def main():
    print("logos :", len(marque.ecrire_logos(documents.SORTIE / "logo")), "fichiers SVG")
    print("PDF   :", ", ".join(documents.produire(rendu)))
    try:
        import bureautique
        print("Office:", ", ".join(bureautique.produire(rendu)))
    except ImportError as err:
        print(f"Office: sauté ({err.name} absent : pip install python-docx python-pptx). "
              "⚠ Les modèles Office livrés gardent leurs anciens chiffres.")


if __name__ == "__main__":
    main()
