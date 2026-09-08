# SEN-HARP Core v0.5 — robustesse et reproductibilité

Ce document complète et actualise le guide v0.4. La version v0.5 ajoute une
taxe carbone sur la consommation des ménages, le recyclage 50/50 du Green
Deal, la calibration factuelle du crédit initial, la nouvelle calibration de
l'investissement et la comptabilité du PIB par la dépense.

## Règles de réplication

- Chaque expérience archive sa configuration et toutes les valeurs résolues
  de `Parameters` dans `resolved_parameters.json`.
- E1/E2, E3/E4 et E5/E6 ont les mêmes paramètres et le même seed économique ;
  seul `PolicyMode` diffère.
- Les figures économiques comparent E0, E1, E3 et E5 ; les figures politiques
  E2, E4 et E6 ; l'endogénéité est étudiée par paires.
- Le contrôle est `python -m pytest -q --tb=short --cache-clear`.
- Le seed 1761 est central ; la robustesse emploie au moins 30 seeds appariés.

## PIB

Sans consommations intermédiaires ni inventaires, le PIB marchand réalisé est
la dépense finale livrée : consommation des ménages + investissement privé +
consommation publique + investissement public. Les transferts, le revenu de
base et le dividende carbone ne sont pas ajoutés directement au PIB.

## Critères de robustesse

- intervalles bootstrap et fréquence du signe des contrastes ;
- signe stable dans au moins 80 % des calibrations plausibles ;
- classement des scénarios présenté comme une fréquence ;
- sensibilité OAT puis globale ;
- aucune conclusion causale fondée sur le seul seed central.
