# Énergie et refroidissement (point 14)

Document principal : **[energie_refroidissement.pdf](energie_refroidissement.pdf)**. Tout est calculé par `energie/energie.py` à partir du chiffrage et du plan de câblage (`python3 energie/energie.py && python3 chiffrage/estimation.py`).

| | |
|---|---|
| Salle serveur | 4.15 kW typique, 5.42 kW en pointe, 2 baies 42U |
| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B) + 1 pack batterie chacun : 24 min même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |
| Climatisation | 2 climatiseurs techniques 7.1 kW (1 en secours), allée froide, consigne 27 °C · ventilation des locaux techniques |
| Efficacité | PUE 1.34 (contre 1.41 pour une salle classique) · 61 557 kWh/an · ≈ 3.2 t CO₂/an |
| Finances | Investissement 57 000 € HT · 14 711 € HT/an · 130 555 € HT sur 5 ans |

Fichiers : `energie_refroidissement.pdf` (et `.html`), `schemas/` (alimentation électrique, plan de la salle serveur), `bilan_puissance.csv`, `resume.json` (repris par le chiffrage).

La première version (Gemini) est dans l'historique git (commit 1fbc1c1). Écarts corrigés : Tier III, groupe électrogène et extinction au gaz sortis du périmètre (options chiffrées), free-cooling impossible au sous-sol, switchs C9200L à une seule alimentation, PUE réaliste, consommation des locaux techniques et des bornes ajoutée, prix du kWh aligné sur le chiffrage.
