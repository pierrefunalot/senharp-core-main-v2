# SEN-HARP Core — note d’évolution et de transmission

**État documenté : 8 septembre 2026**  
**Version déclarée dans le dépôt : Core v0.5**  
**Dernière validation communiquée : 84 tests réussis, 14 avertissements externes**

## 1. Objet

Cette note accompagne la transmission de l’état actuel de SEN-HARP Core à la
personne à l’origine du noyau reçu. Elle expose les modifications intervenues
depuis le point d’arrêt décrit par le document
`Guide_lecture_SEN_HARP_Core_v0.4_7_experiences.docx`, sans présenter les choix
de calibration comme des résultats empiriquement établis.

Le point de départ v0.4 comprenait 62 tests et s’arrêtait après l’intégration
des UBS comme service additionnel. Il ne comprenait notamment ni substitution
automatique des UBS à la consommation privée, ni réduction du temps de travail,
ni garantie d’emploi additionnelle, ni taxe carbone directe des ménages.

## 2. Résumé des évolutions majeures

L’architecture générale du noyau a été conservée : `model.py` ordonnance les
mécanismes, `parameters.py` centralise la calibration, `entities.py` définit les
états des agents et `collector.py` constitue l’interface d’analyse. Les ajouts
ont été isolés dans des modules spécialisés et assortis de tests.

Les principales évolutions sont les suivantes :

1. comptabilité explicite du PIB nominal et réel par la demande finale ;
2. recalibration du capital, de l’investissement et de la demande de travail ;
3. taxe carbone appliquée aux consommations des ménages en plus des firmes ;
4. recyclage propre au Green Deal entre investissement public vert et dividende
   carbone ;
5. garantie d’emploi limitée au Green Deal ;
6. substitution simple des UBS à une partie des dépenses privées contraintes ;
7. suppression du revenu de base dans les expériences post-growth de référence ;
8. réduction de 20 % du temps de travail sans réduction du salaire de base dans
   le scénario post-growth ;
9. comptabilité matérielle sectorielle minimale, sans stock de ressources ni
   dynamique détaillée des matières ;
10. indicateurs de Gini, validation interne, campagnes multi-seeds et figures du
    manuscrit avec tests statistiques exportés.

## 3. Architecture temporelle conservée

Les conventions centrales du guide v0.4 restent valables :

- la production de la période utilise le capital d’ouverture ;
- seul l’investissement livré entre dans le capital de clôture et devient
  productif à la période suivante ;
- achats publics, investissement et UBS peuvent être rationnés physiquement ;
- le dommage climatique de fin de période affecte le capital de la période
  suivante ;
- une élection modifie l’état du package pour les périodes suivantes ;
- les générateurs aléatoires économiques et politiques restent séparés ;
- les graphiques utilisent les tables collectées et non une relecture directe
  des objets après simulation.

## 4. Modifications économiques et sociales

### 4.1. PIB

Le module `senharp_core/gdp.py` calcule désormais :

\[
PIB = C_{ménages}+I_{privé}+G_{courant}+I_{public}.
\]

Le PIB nominal est évalué aux prix courants. Le PIB réel utilise les prix de la
période initiale. Les invendus sont exclus, car Core ne possède pas encore de
stock d’inventaires. Des écarts d’identité contrôlent la correspondance avec
les ventes des firmes.

### 4.2. Capital, investissement et demande effective

La calibration a été revue pour éviter un investissement privé négligeable et
une crise d’emploi purement produite par une incohérence entre l’état initial et
la dynamique :

| Paramètre central | Valeur actuelle | Interprétation |
|---|---:|---|
| `initial_private_capital_scale` | 12,5 | Échelle du capital privé initial |
| `initial_green_capital_share` | 0,05 | Part verte initiale du capital privé |
| `initial_investment_rate` | 0,07 | Taux brut initial d’investissement |
| `capital_depreciation_rate` | 0,03 | Dépréciation périodique |
| `min_firm_animal_spirits` | 0,035 | Borne basse de croissance désirée |
| `max_firm_animal_spirits` | 0,045 | Borne haute de croissance désirée |
| `initial_capacity_utilization` | 0,80 | Utilisation initiale générique |
| `production_adjustment_speed` | 0,25 | Ajustement de la production à la demande |

La demande effective passée intervient dans la production planifiée et les
cibles d’emploi. La calibration initiale conserve une cible de taux d’emploi
privé de 90 %, sans règle ad hoc imposant ensuite un taux d’emploi donné.

### 4.3. Travail, salaires et protection contre le chômage

- `calibrated_real_labor_productivity = 165.0` fournit une productivité réelle
  commune ; la désagrégation sectorielle n’a pas été utilisée pour masquer la
  faiblesse de la demande agrégée.
- `nominal_wage_growth_rate = 0.0` : la hausse nominale automatique testée a été
  abandonnée.
- `unemployment_replacement_rate = 0.60` produit, selon la formule du module de
  revenu, une allocation égale à 40 % du salaire de base. L’intitulé du
  paramètre mérite donc une attention particulière.
- le Green Deal inscrit après l’appariement 30 % des chômeurs résiduels dans la
  garantie d’emploi à chaque période active (`green_deal_job_guarantee_entry_rate`).
- le post-growth réduit progressivement le temps de travail de 20 % sur trois
  périodes actives, sans baisse du salaire de base ; le coût est initialement
  assumé par les entreprises.

### 4.4. Fiscalité carbone

La taxe carbone porte maintenant sur deux assiettes :

- firmes : coût lié au capital brun, avec recette publique correspondante ;
- ménages : prélèvement sur le panier sectoriel selon des poids carbone
  explicites (`household_carbon_tax.py`).

Le scénario Carbon Tax verse la recette au budget général sans redistribution
automatique. Le Green Deal partage la recette de référence à parts égales entre
investissement public vert et dividende carbone progressif. Le post-growth ne
reçoit pas de taxe carbone : une mention contraire dans le manuscrit historique
est considérée comme une erreur de celui-ci.

### 4.5. Green Deal

Le package actif réunit :

- le socle de tarification carbone ;
- un taux de crédit vert de 0 % et brun de 5 %, avant marge bancaire ;
- un investissement public vert alimenté par 50 % des recettes carbone ;
- un dividende carbone redistributif alimenté par les 50 % restants ;
- une garantie d’emploi pour une fraction des chômeurs résiduels ;
- aucune indexation salariale propre au Green Deal.

L’investissement public annoncé reste soumis à la capacité productive et au
rationnement du marché. Le capital public livré demeure propriété publique et
fournit ensuite des services productifs aux firmes.

### 4.6. Post-growth

La calibration des expériences E5 et E6 est actuellement :

| Instrument | Valeur de référence | Fonction |
|---|---:|---|
| Plafond initial de crédit brun | 0,20 | Limite l’autorisation du crédit brun |
| Rétention du capital brun | 0,96 | Retrait accéléré du capital brun hérité |
| Revenu de base | 0,00 | Mécanisme présent mais désactivé |
| UBS, échelle du programme | 0,20 | Active la substitution calibrée |
| Dépense libérée non redépensée | 0,10 | Limite le rebond de consommation |
| Ticket modérateur | 0,60 | Reste à charge dans chaque domaine UBS |
| Réduction du temps de travail | 0,20 | RTT sans baisse du salaire de base |
| Montée en charge RTT et UBS | 3 périodes | Évite une rupture instantanée |
| Multiplicateur direct d’émissions | 1,00 | Neutralise le raccourci exogène |

Le plafond de crédit brun possède aussi une règle de diminution graduelle dans
les paramètres généraux. La décarbonation doit provenir principalement du
crédit, de l’investissement, de la composition du capital, de la production et
de la consommation, et non d’une réduction exogène des émissions.

### 4.7. UBS inspirés de Factuel

Les UBS ne sont ni un transfert monétaire ni un terme ajouté directement à
l’équation du Needs Index. Ils socialisent une fraction des dépenses
essentielles dans quatre domaines : agriculture/alimentation, énergie,
logement et transport.

Pour chaque domaine, Core distingue :

- la part du panier essentiel ;
- la fraction ciblée par socialisation ;
- le coût administratif de fourniture ;
- le ticket modérateur payé par le ménage ;
- la dépense publique planifiée puis réellement livrée.

Le ticket modérateur est actuellement fixé à 60 % dans les quatre domaines.
La prestation réduit le coût privé contraint et agit donc sur le Needs Index par
le canal d’accessibilité financière. Elle n’entre pas comme bonus autonome dans
le Needs Index. Le revenu libéré est redépensé à 90 %, les 10 % restants étant
neutralisés pour limiter un rebond mécanique.

## 5. Environnement, inégalités et validation

### 5.1. Environnement

Le bloc climat conserve les émissions économiques, le reste du monde, le cycle
du carbone, le forçage, la température et les dommages. Le module
`resources.py` ajoute uniquement une comptabilité de l’usage matériel fondée
sur la production sectorielle. Il ne modélise ni stock épuisable, ni marché des
matières, conformément au choix de rester simple.

### 5.2. Inégalités

Le collector publie un Gini du revenu disponible économique et un Gini du
Needs Index. Aucun ensemble plus large d’indicateurs distributifs n’a été
introduit.

### 5.3. Hypothèses de réalisme

`empirical_validation.py` formalise quatre diagnostics de validité générative :

- H1 : Carbon Tax et Green Deal réduisent les émissions mais restent sous une
  réduction stylisée de 55 % sur l’horizon ;
- H2 : une charge de dépenses contraintes plus élevée est associée à un soutien
  politique plus faible aux élections ;
- H3 : une même politique produit des résultats territoriaux différents ;
- H4 : le Green Deal est socialement et politiquement plus durable que la taxe
  carbone isolée.

Ils sont évalués seed par seed et déclarés robustes si leur critère est vérifié
dans au moins 80 % des seeds. Ce sont des tests internes des mécanismes posés,
pas une validation causale externe sur données européennes.

## 6. Protocole expérimental

Le fichier `experiments/seven_experiments.json` définit :

| ID | Scénario | Mode |
|---|---|---|
| E0 | Baseline | OFF |
| E1 | Carbon Tax | FIXED |
| E2 | Carbon Tax | ENDOGENOUS |
| E3 | Green Deal | FIXED |
| E4 | Green Deal | ENDOGENOUS |
| E5 | Post-Growth | FIXED |
| E6 | Post-Growth | ENDOGENOUS |

Les paires E1/E2, E3/E4 et E5/E6 partagent la même calibration économique et le
même seed. Les contrastes politique moins politique fixe isolent donc l’effet
de l’intermittence électorale à chocs appariés.

Le protocole central couvre 26 observations, de 0 à 25. Les élections ont lieu
aux périodes internes 4, 9, 14, 19 et 24, affichées comme échéances 5, 10, 15,
20 et 25 dans les figures du manuscrit.

## 7. Figures et statistiques du manuscrit

La campagne de robustesse génère les figures de résultats 4 à 11 : PIB,
dette/PIB, Needs Index, vote, réélection, gagnants/perdants, émissions cumulées
et température. Dans les figures comparatives, une ligne pleine représente le
modèle politique endogène et une ligne pointillée la politique fixe
contrefactuelle.

Les tests reproduisent la famille non paramétrique utilisée dans Factuel :

- Kruskal–Wallis global entre scénarios ;
- Mann–Whitney deux à deux ;
- correction de Holm des comparaisons multiples ;
- `ns`, `*`, `**`, `***` pour les seuils 5 %, 1 % et 0,1 %.

Toutes les valeurs sont conservées dans
`manuscript_figure_statistical_tests.csv`. Pour les trajectoires, le test global
utilise une moyenne temporelle par seed afin de ne pas traiter les périodes
d’un même run comme des observations indépendantes.

## 8. Choix testés puis abandonnés ou neutralisés

- augmentation de l’allocation chômage de 40 % à 50 % du salaire de base :
  abandonnée ;
- croissance nominale automatique du salaire : remise à zéro ;
- diminution discrétionnaire de la productivité pour atteindre directement un
  taux de chômage cible : abandonnée ;
- règle de lissage de l’emploi : non introduite, car elle aurait masqué la
  dynamique de demande ;
- modification de la propension marginale à consommer propre au post-growth :
  non retenue ;
- revenu de base post-growth : mécanisme conservé mais calibration centrale à
  zéro ;
- composante directe de services publics dans le Needs Index : neutralisée dans
  les sept expériences afin d’éviter un double comptage avec la réduction des
  dépenses contraintes ;
- effet exogène propre au post-growth sur les émissions : multiplicateur fixé à
  un dans E5 et E6.

## 9. État de validation et limites

La dernière exécution communiquée est :

```text
84 passed, 14 warnings
```

Les avertissements proviennent d’alias dépréciés utilisés par Matplotlib dans
Pyparsing ; ils ne signalent pas une erreur de SEN-HARP.

Les tests garantissent les propriétés explicitement codées : neutralité,
activation des packages, identités comptables, intégration de mécanismes et
reproductibilité ciblée. Ils ne garantissent ni que toute équation est la seule
formulation scientifiquement possible, ni que la calibration reproduit toutes
les séries européennes.

Points restant ouverts : validation empirique externe, justification sourcée de
chaque plage de sensibilité, absence de commerce extérieur et d’inventaires,
calibration du coût budgétaire post-growth, et révision du texte quantitatif du
manuscrit après la campagne définitive.

## 10. Fichiers structurants ajoutés ou renforcés

- `gdp.py` : PIB nominal/réel et décomposition C–I–G ;
- `household_carbon_tax.py` : taxe carbone des ménages ;
- `job_guarantee.py` : garantie d’emploi Green Deal ;
- `resources.py` : usage matériel sectoriel minimal ;
- `inequality.py` : coefficients de Gini ;
- `empirical_validation.py` : H1–H4 ;
- `robustness_graphs.py` : figures de robustesse et du manuscrit ;
- `manuscript_statistics.py` : tests et étoiles auditables ;
- `validation_protocol.py` : campagnes appariées, contrastes et manifests.

Cette liste complète le guide v0.4 ; elle ne remplace pas la lecture du
scheduling effectif dans `model.py`.
