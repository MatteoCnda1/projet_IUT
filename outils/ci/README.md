# outils/ci/ : intégration continue du dépôt

La CI (`.github/workflows/ci.yml`) tourne sur GitHub Actions à chaque `push` (toutes les branches), à chaque pull request
(quelle que soit la branche de base, `revue/*` comprises) et à la demande (onglet *Actions*, « Run workflow »).
Trois jobs en parallèle, **environ 5 minutes** en tout (la génération est le plus long) :

| Job | Ce qu'il vérifie | Bloquant | Durée |
|---|---|---|---|
| **Python** | `python -m compileall` sur tous les scripts ; `ruff check` avec `ruff.toml` : erreurs de syntaxe, noms indéfinis (F821), imports et variables inutiles (F401, F841), f-strings vides (F541), séquences d'échappement invalides (W605). Puis le style (E, W, B, SIM), affiché pour information | oui (sauf le style) | < 1 min |
| **Cohérence** | `verifier_coherence.py` : plan d'adressage, matrice des flux, montants cités dans les README, liens, règles GesTT, fichiers interdits et secrets. Puis `orthographe.py` (fautes fréquentes) pour information | oui (sauf l'orthographe) | < 1 min |
| **Génération** | installe poppler, les polices DejaVu, Chrome (déjà sur le runner), la CLI draw.io (sous Xvfb) et les paquets Python, lance toute la chaîne (`generer_tout.sh`), puis `verifier_a_jour.py` : les livrables texte suivis par git doivent être ceux que produit la chaîne, et les PDF/PNG doivent avoir été produits. En cas d'échec, les livrables régénérés sont publiés en artefact `livrables-regeneres` (3 jours ; un quota d'artefacts atteint ne fait pas échouer le job). Les SVG de matplotlib et le site vitrine ne sont pas comparés | oui | 4 à 6 min |

Si le job **Génération** échoue sur « Livrables à jour » : quelqu'un a modifié une source (script, `donnees.py`, `flux.py`…)
sans relancer la chaîne, ou a modifié un livrable à la main. Relancer la chaîne en local et committer les livrables, ou
télécharger l'artefact `livrables-regeneres` (et `correctif-livrables`, un `git apply`-able des fichiers texte) depuis la page du run.

## Lancer les contrôles en local

Depuis la racine du dépôt :

```bash
python3 outils/ci/verifier_coherence.py                 # tous les contrôles de cohérence (bibliothèque standard seulement)
python3 outils/ci/verifier_coherence.py adressage flux   # seulement certains (liste : --liste)
python3 outils/ci/orthographe.py                        # fautes fréquentes (non bloquant ; --strict pour un code retour)

pip install -r requirements.txt                         # une fois (la CI fige les versions : -c outils/ci/contraintes.txt)
pip install ruff
python3 -m compileall -q . && ruff check --config outils/ci/ruff.toml .

touch /tmp/repere                                       # chaîne complète puis contrôle « à jour »
bash outils/ci/generer_tout.sh
python3 outils/ci/verifier_a_jour.py --repere /tmp/repere
```

`verifier_a_jour.py` compare l'arbre de travail à l'**index** git : sur un dépôt propre, c'est le dernier commit. Si vous
avez des modifications en cours, faites `git add` de ce qui sert de référence avant de lancer la chaîne.

Outils système de la chaîne : `poppler-utils` (pdftotext, pdftoppm), Google Chrome ou Chromium, la CLI draw.io
(`drawio`, paquet .deb de [drawio-desktop](https://github.com/jgraph/drawio-desktop/releases)), polices DejaVu.
Sans Chrome ou draw.io, la chaîne tourne quand même mais ne régénère pas les PDF ou les PNG (`--strict` en fait une erreur).

## Ordre de la chaîne

`generer_tout.sh` est la référence (l'ordre du README racine fait tourner `architecture/reseau/build.py` avant le plan
de câblage, dont il lit pourtant `resume.json`) :

1. `cablage/salles.py`, `etude_rssi.py`, `plan_cablage.py`, `rapport.py` : le plan de câblage, lu par presque tout le reste ;
2. `architecture/reseau/build.py` : plan d'adressage, architectures L2 et L3, schémas draw.io ;
3. `energie/energie.py` puis `chiffrage/estimation.py` : le chiffrage reprend le lot énergie ;
4. `roadmap/build.py` ;
5. `securite/build.py`, puis `juridique/build.py` (qui reprend la PSSI) ;
6. `architecture/audit/generer_rapport_audit.py` et `traitement_audit.py` (relit adressage, énergie et chiffrage) ;
7. `communication/build.py` : charte, plaquette, organisation et modèles Office (le site vitrine `livrables/site_web/` est maintenu à la main par son auteur, hors de la chaîne).

Boucle connue : `cablage/plan_cablage.py` relit la liste des équipements de `chiffrage/estimation.json` pour
`implantation.html`. Après l'ajout ou le retrait d'un équipement dans `chiffrage/estimation.py`, lancer la chaîne deux fois.

## Ce qui varie d'une exécution à l'autre

Neutralisé par `verifier_a_jour.py` (liste `VARIABLES`) : la date de génération du sous-titre des documents HTML
(`· 20/11/2026<br>`) et le « Généré le » de `livrables/plan_cablage/README.md`.

Non comparés, seulement vérifiés comme produits : les PDF (date de création, rendu de Chrome), PNG, DOCX/PPTX (dates
internes) et les SVG de matplotlib (date et identifiants aléatoires : `svg.hashsalt` n'est pas fixé dans les scripts).
Les CSV, JSON, Markdown, HTML, `.drawio` et les SVG des logos sont reproductibles : ils doivent être identiques à git.

Le plan de câblage dépend du calcul numérique (numpy, scipy, OpenCV, poppler) : la CI fige les paquets Python sur les
versions qui ont produit les livrables suivis (`contraintes.txt`). Pour monter une version, la changer dans ce fichier,
relancer la chaîne, vérifier les écarts de `livrables/plan_cablage/*.csv` et committer.

## Contrôles de cohérence (`verifier_coherence.py`)

| Nom | Contrôle |
|---|---|
| `adressage` | `livrables/plan_adressage/*.csv` : numéros et noms de VLAN uniques, réseaux valides et sans chevauchement, passerelle = première adresse, préfixe IPv6 `4nnn::/64` du VLAN *n*, adresses des équipements dans leur sous-réseau, sans doublon, même terminaison IPv4/IPv6, passerelle IPv6 identique dans les deux fichiers |
| `flux` | `securite/flux.py` et `livrables/securite/matrice_flux.csv` : objets et zones connus, chaque VLAN ou hôte cité existe au plan d'adressage, chaque VRF a sa zone, services bien formés ; les zones proposées (IA) sont signalées |
| `montants` | montants cités dans `README.md`, `livrables/energie_refroidissement/README.md` et `livrables/audit/README.md` = `chiffrage/estimation.json`, `livrables/energie_refroidissement/resume.json` (et la v1 archivée) ; totaux du chiffrage, lot énergie et quantités du plan de câblage repris à l'identique |
| `liens` | liens relatifs des Markdown du dépôt et des HTML de `livrables/` : la cible existe (avertissement si elle n'est pas suivie par git) |
| `gestt` | règles de dépôt (CLAUDE.md) : aucun fichier de `livrables/` au-delà de 20 Mo ; dans `livrables/depots/pxx/` : extensions acceptées, 20 fichiers et 20 Mo au plus, pas de sous-dossier, nommage `RLI-Pxx-…` (avertissement) |
| `hygiene` | aucun `__pycache__`, `.pyc`, `.bkp`, `.dtmp`, verrou `.$…`, `keys_vault`, clé ou certificat suivi par git ; pas de clé privée PEM ni de jeton (GitHub, AWS, Slack, Vault) dans le contenu |

### Ajouter un contrôle

Dans `verifier_coherence.py`, écrire une fonction décorée, qui ne s'appuie que sur la bibliothèque standard :

```python
@controle("baies", "Baies du plan de câblage")
def controle_baies(r):
    for i, b in enumerate(lire_csv("livrables/plan_cablage/baies.csv"), start=2):
        if int(b["hauteur_U"]) > 42:
            r.erreur(f"{b['local']} : {b['hauteur_U']}U dans une baie 42U", "livrables/plan_cablage/baies.csv", i)
    r.ok("baies.csv : hauteurs compatibles")
```

`r.erreur(message, fichier, ligne)` fait échouer la CI (et annote le fichier dans la PR), `r.avert(...)` signale sans
bloquer, `r.ok(...)` affiche ✔. Pour lire une constante d'un script sans l'exécuter (il importerait matplotlib) :
`constantes("securite/flux.py", "ZONES")`. Le contrôle est lancé automatiquement, et seul avec
`python3 outils/ci/verifier_coherence.py baies`. Une valeur volontairement variable dans un livrable texte (date,
compteur) se neutralise dans la liste `VARIABLES` de `verifier_a_jour.py`.

## Dette suivie dans `ruff.toml`

`[lint.per-file-ignores]` neutralise les erreurs déjà présentes au 20/11/2026 (imports et variables inutiles, f-strings
sans champ, `\g` dans `generer_rapport_audit.py`). Une fois le fichier corrigé, retirer sa ligne : la règle redevient
bloquante pour lui aussi. Le code des archives (`*/archives/`) n'est pas contrôlé.

## Fichiers

| Fichier | Rôle |
|---|---|
| `../../.github/workflows/ci.yml` | le workflow GitHub Actions |
| `generer_tout.sh` | chaîne complète, dans l'ordre des dépendances (`--strict` : outil manquant = erreur) |
| `verifier_a_jour.py` | après la chaîne : livrables texte identiques à git, binaires bien produits |
| `verifier_coherence.py` | contrôles de cohérence (ci-dessus) |
| `orthographe.py` | fautes fréquentes (liste `FAUTES`), non bloquant |
| `sortie_ci.py` | affichage ✔ / ✘ / ⚠, annotations et résumé GitHub, appels git |
| `ruff.toml` | règles ruff bloquantes et dette tolérée |
| `contraintes.txt` | versions exactes des paquets Python pour la CI (`../../requirements.txt` donne les minimums) |
