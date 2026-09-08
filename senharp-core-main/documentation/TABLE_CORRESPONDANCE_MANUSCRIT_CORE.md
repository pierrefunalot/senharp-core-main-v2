# Correspondance entre le manuscrit, Factuel et Core actuel

## Mode d’emploi

Ce tableau indique si chaque mécanisme annoncé dans le manuscrit historique est
présent dans Core et comment son implémentation a évolué. « Factuel » désigne le
fichier historique `sen harp factuel.py`, utilisé comme source d’inspiration et
non comme spécification exécutable normative.

| Domaine | Manuscrit / Factuel | Core actuel | Statut et différence à signaler |
|---|---|---|---|
| Agents | Ménages, firmes, banques, État, banque centrale, nature | Même structure générale | Continuité architecturale |
| Secteurs | Six secteurs productifs | Agriculture, énergie, logement, transport, industrie, technologie | Aligné |
| PIB | Agrégat utilisé dans les trajectoires | PIB nominal et réel explicites, somme des demandes finales réalisées C + I privé + G courant + I public | Core est plus transparent ; pas de stocks d’invendus |
| Investissement privé | Accumulation brun/vert | Décision, crédit, livraison, rationnement et accumulation séparés | Renforcé et recalibré |
| Capital initial | Calibration Factuel | Échelle explicite `initial_private_capital_scale=12.5`, part verte 5 % | À documenter comme calibration, non comme estimation |
| Emploi | Demande des firmes et appariement | Demande effective, production cible, emploi ciblé et emploi rempli séparés | Diagnostic plus explicite |
| Productivité | Paramétrage historique | Productivité réelle commune calibrée ; pas de différenciation sectorielle ad hoc | Choix de simplicité |
| Taxe carbone des firmes | Présente | Présente, recette inscrite au budget | Aligné |
| Taxe carbone des ménages | Absente ou indirecte dans Factuel | Taxe directe sur le panier sectoriel des ménages | Addition substantielle |
| Carbon Tax | Prix carbone | Recettes vers budget général, sans redistribution automatique | Choix explicite |
| Green Deal | Transition intégrée | Taxe, crédit différencié, investissement public vert, dividende progressif et garantie d’emploi | Plus complet |
| Indexation Green Deal | Mentionnée dans le manuscrit historique | Désactivée | Choix ultérieur assumé |
| Capital vert public | Investissement public | Stock public distinct fournissant des services productifs à partir de t+1 | Formalisation renforcée |
| Garantie d’emploi | Éléments présents dans Factuel | 30 % des chômeurs résiduels inscrits lorsque le Green Deal est actif | Addition ; limitée au Green Deal |
| Crédit brun post-growth | Interdiction/contrainte | Plafond initial de 20 %, règle graduelle possible | Alignement simplifié avec Factuel |
| Capital brun échoué | Retrait accéléré | Rétention 96 % après les autres opérations prévues par le scheduling | Effet renforcé puis recalibré |
| Taxe carbone post-growth | Mention contradictoire dans le manuscrit | Aucune taxe carbone | Core corrige l’erreur identifiée |
| Revenu de base | Présent dans Factuel/manuscrit | Module conservé, ratio fixé à zéro dans E5/E6 | Désactivé pour comparabilité et budget |
| Cumul BI + chômage | Risque de cumul | Mécanisme d’offset disponible, sans effet avec BI nul | Sécurisé mais inactif centralement |
| UBS | Services universels et socialisation | Substitution de dépenses contraintes, achats publics planifiés/réalisés, rationnement | Désormais proche de Factuel |
| UBS dans Needs | Bénéfice social | Aucun bonus direct ; effet via baisse du coût contraint | Évite le double comptage |
| Ticket modérateur UBS | Reste à charge | 60 % dans les quatre domaines | Calibration visant besoins élevés et dette maîtrisée |
| Rebond de consommation UBS | Dépense privée libérée | 90 % redépensés, 10 % non redépensés | Paramètre explicite |
| RTT post-growth | Présente dans l’esprit de Factuel | Réduction de 20 % sur trois périodes, salaire de base maintenu | Addition substantielle |
| Dépenses publiques | Dépenses et services | G courant, I public, transferts, garantie d’emploi et UBS distingués | Comptabilité renforcée |
| Dette publique | Ratio dette/PIB | Dette d’ouverture, intérêts, déficit et dette de clôture suivis | Aligné, dynamique PG encore à surveiller |
| Needs Index | Accessibilité, revenu relatif, services, territoire | Même famille ; composante directe de service public neutralisée dans le protocole | Évite une baisse mécanique observée lors du diagnostic |
| Inégalités | Résultats distributifs | Gini du revenu disponible et du Needs Index | Addition simple demandée |
| Ressources | Dimension matérielle | Usage matériel proportionnel à la production sectorielle ; pas de stock | Périmètre volontairement minimal |
| Émissions ménages | Absentes dans Factuel selon l’audit | Présentes via consommation | Addition Core |
| Climat | Cycle carbone, température, dommage | Bloc carbone–température–dommage conservé et testé | Aligné dans son principe |
| Politique | Vote et réversibilité | OFF, FIXED et ENDOGENOUS ; rejet et réactivation | Formalisation expérimentale renforcée |
| Contrefactuel politique | Comparaison annoncée | Paires E1/E2, E3/E4, E5/E6 avec mêmes seeds | Plus reproductible dans Core |
| Soutien politique | Probabilités et élections | Probabilité moyenne et vote réalisé collectés séparément | Distinction conforme au guide |
| H1–H4 | Hypothèses de réalisme du manuscrit | Diagnostics internes seed par seed, règle de 80 % | Ne pas qualifier de validation empirique externe |
| Figures 4–11 | Figures du manuscrit | Génération automatisée depuis les collectors | Ajout récent |
| Significativité | Kruskal–Wallis et tests deux à deux dans Factuel | Kruskal–Wallis, Mann–Whitney, correction de Holm, étoiles et CSV | Core ajoute traçabilité et correction multiple |

## Figures de résultats

| Figure du manuscrit | Sortie Core | Construction actuelle |
|---|---|---|
| Figure 4 — PIB | `manuscript_figure_04_real_gdp.png` | Trajectoires politique/fixe et écarts appariés aux élections |
| Figure 5 — Dette/PIB | `manuscript_figure_05_debt_to_gdp.png` | Même construction |
| Figure 6 — Needs Index | `manuscript_figure_06_needs_index.png` | Même construction |
| Figure 7 — Votes | `manuscript_figure_07_vote_shares.png` | Distribution du soutien électoral réalisé |
| Figure 8 — Réélection | `manuscript_figure_08_reelection.png` | Moyenne ± un écart-type par échéance |
| Figure 9 — Gagnants/perdants | `manuscript_figure_09_support_subgroups.png` | Soutien selon variation du Needs Index depuis t=0 |
| Figure 10 — Émissions cumulées | `manuscript_figure_10_cumulative_emissions.png` | Distributions fixe et politique |
| Figure 11 — Température | `manuscript_figure_11_temperature.png` | Trajectoires et écarts appariés |

Les figures conceptuelles 1 à 3 du manuscrit ne sont pas produites par les
simulations. Elles doivent être jointes au manuscrit ou transmises comme sources
graphiques distinctes.

## Différences nécessitant une mise à jour du manuscrit

1. La taxe carbone touche désormais directement les ménages.
2. Le Green Deal ne comporte plus d’indexation salariale spécifique.
3. Le post-growth ne comporte pas de taxe carbone et son revenu de base central
   est nul.
4. Les UBS réduisent les dépenses contraintes avec un ticket modérateur de 60 %.
5. Le post-growth comporte une RTT compensée de 20 %.
6. Le PIB possède désormais une définition nominale et réelle explicite.
7. Les résultats chiffrés, p-values et affirmations de significativité du
   manuscrit historique doivent être recalculés avec la campagne Core finale.
8. La convention des écarts doit être écrite partout comme
   `politique endogène − politique fixe` ; une phrase du manuscrit sur le signe
   des écarts de Needs Index est actuellement contradictoire.
