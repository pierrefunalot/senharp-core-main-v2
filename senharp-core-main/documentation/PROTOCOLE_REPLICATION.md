# SEN-HARP Core — protocole de réplication et de transmission

## 1. Contenu à transmettre

Inclure :

- `senharp_core/` ;
- `scripts/` ;
- `tests/` ;
- `experiments/` ;
- `notebooks/` ;
- `README.md`, `ENVIRONMENT.txt`, `requirements.txt` et `.gitignore` ;
- le présent dossier `documentation/` ;
- le guide original
  `Guide_lecture_SEN_HARP_Core_v0.4_7_experiences.docx` ;
- le manuscrit seulement si les droits et le statut de soumission permettent sa
  transmission ;
- une sélection clairement identifiée de résultats définitifs.

Exclure de l’archive de code :

- `.venv/` ;
- `.pytest_cache/` ;
- tous les `__pycache__/` ;
- `.ipynb_checkpoints/` ;
- sorties anciennes ou intermédiaires ;
- journaux et fichiers temporaires.

Nom d’archive conseillé :

```text
SEN-HARP_Core_v0.5_handover_2026-09-08.zip
```

## 2. Pré-requis

- Windows 10 ou 11 ;
- Python 3.12.x ;
- terminal PowerShell ouvert à la racine contenant `senharp_core/`.

Vérifier l’interpréteur :

```powershell
python --version
python -c "import sys; print(sys.executable)"
```

## 3. Création de l’environnement

Pour une reprise propre :

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

La présence de `(.venv)` au début de l’invite confirme l’activation.

## 4. Validation du code

Commande recommandée sous Windows, sans utilisation du cache pytest :

```powershell
python -m pytest tests -q --tb=short -p no:cacheprovider
```

Résultat de référence au 7 septembre 2026 :

```text
84 passed, 14 warnings
```

Les avertissements connus sont des `PyparsingDeprecationWarning` émis par
Matplotlib. Ils ne constituent pas des échecs de modèle.

## 5. Diagnostic sur un seul seed

```powershell
python scripts/run_robustness.py --seeds 1 --first-seed 1761 --output outputs/diagnostic_seed_1761
```

Cette commande exécute les sept expériences sur le seed 1761 et produit les
tables, validations et figures. Elle doit être utilisée avant une campagne
longue après toute modification structurelle.

## 6. Campagne de robustesse de 300 seeds

```powershell
python scripts/run_robustness.py --seeds 300 --first-seed 1761 --output outputs/robustness_300_seeds_manuscript
```

Il s’agit de 300 seeds appariés pour chacune des sept expériences, soit 2 100
runs de 26 périodes. La génération des figures est automatique à la fin de la
commande.

Principales sorties :

```text
trajectories.csv
needs_index_snapshots.csv
seed_level_outcomes.csv
paired_contrasts.csv
bootstrap_contrast_summary.csv
ranking_frequencies.csv
realism_hypothesis_seed_results.csv
realism_hypothesis_summary.csv
manuscript_figure_statistical_tests.csv
resolved_parameters/
figures/
```

## 7. Figures du manuscrit

Dans `outputs/robustness_300_seeds_manuscript/figures/` :

```text
manuscript_figure_04_real_gdp.png
manuscript_figure_05_debt_to_gdp.png
manuscript_figure_06_needs_index.png
manuscript_figure_07_vote_shares.png
manuscript_figure_08_reelection.png
manuscript_figure_09_support_subgroups.png
manuscript_figure_10_cumulative_emissions.png
manuscript_figure_11_temperature.png
```

Convention : ligne pleine = politique endogène ; ligne pointillée = politique
fixe ; panneau inférieur = différence appariée politique moins fixe.

Le fichier `manuscript_figure_statistical_tests.csv` est la source à conserver
avec les figures. Les p-values imprimées ne doivent jamais être retranscrites
manuellement depuis l’image.

## 8. Régénération des figures à partir d’une campagne existante

Le script `analyze_validation.py` utilise encore, pour sa section robustness,
un chemin historique codé en dur. Tant que ce point n’est pas corrigé, la
méthode garantie consiste à laisser `run_robustness.py` générer les figures à la
fin de la campagne. Ne pas supposer que `--root` redirige cette section.

## 9. Sensibilité OAT et Latin Hypercube

Criblage OAT central :

```powershell
python scripts/run_sensitivity.py oat --seeds 1 --first-seed 1761 --output outputs/sensitivity
```

Création d’un plan Latin Hypercube de 300 calibrations :

```powershell
python scripts/run_sensitivity.py lhs-design --samples 300 --first-seed 1761 --output outputs/sensitivity
```

Exécution des 300 calibrations sur un seed :

```powershell
python scripts/run_sensitivity.py lhs-run --limit 300 --seeds 1 --first-seed 1761 --output outputs/sensitivity
```

Analyse de la sensibilité :

```powershell
python scripts/analyze_validation.py --section lhs --root outputs/sensitivity
```

Attention : la campagne de 300 seeds et le Latin Hypercube de 300 calibrations
répondent à deux questions différentes. La première mesure l’incertitude
stochastique ; la seconde la sensibilité aux paramètres.

## 10. Contrôles après exécution

Vérifier systématiquement :

1. que les sept identifiants E0 à E6 figurent dans `trajectories.csv` ;
2. que chaque seed apparaît dans les sept expériences ;
3. que chaque paire FIXED/ENDOGENOUS possède les mêmes paramètres résolus ;
4. que les échéances électorales correspondent aux périodes 4, 9, 14, 19, 24 ;
5. que les écarts appariés utilisent le même seed à gauche et à droite ;
6. que les identités PIB, crédit, investissement, achats publics et UBS restent
   dans les tolérances testées ;
7. que `manuscript_figure_statistical_tests.csv` accompagne toute figure
   publiée ;
8. que les affirmations du manuscrit sont réécrites à partir de la campagne
   finale et non des résultats historiques de Factuel.

## 11. Reproductibilité documentaire

Avant l’envoi final, mettre à jour dans `ENVIRONMENT.txt` :

- date d’exécution ;
- version exacte de Python ;
- commande pytest ;
- nombre de tests réussis ;
- système d’exploitation.

Conserver également une copie de :

- `experiments/seven_experiments.json` ;
- tous les fichiers de `resolved_parameters/` ;
- la sortie textuelle de pytest ;
- la commande exacte de campagne ;
- les CSV sources des figures.

Le destinataire pourra ainsi distinguer le code, la calibration, les données
simulées et les interprétations scientifiques.
