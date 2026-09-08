# SEN-HARP Core

SEN-HARP — Society–Economy–Nature with Heterogeneous Agents,finite Resources and Politics — is an agent-based stock-flow
consistent model designed to study the economic, social, environmental and political dynamics of sustainability transitions.

## Current version

This repository contains SEN-HARP Core v0.5.

The current version includes:

- heterogeneous households;
- firms distributed across six productive sectors;
- commercial banks and a central bank;
- labour, consumption, investment and credit mechanisms;
- government taxation, expenditure, deficit and public debt;
- household and industrial emissions;
- pollution accumulation and climate damages;
- the household-level NeedsIndex;
- elections, policy rejection and policy reactivation;
- a carbon-tax package;
- a Green Deal package;
- household carbon pricing and progressive Green Deal recycling;
- nominal and real GDP accounting with an expenditure decomposition;
- a Post-Growth package including:
  - brown-credit restriction;
  - accelerated retirement of brown capital;
  - an optional universal basic income mechanism (disabled in the reference experiments);
  - universal basic services substituting for part of constrained private spending;
  - a compensated 20% working-time reduction in the reference experiments.

The model currently passes 84 automated tests (confirmed on 7 September 2026).

The current validation layer also includes:

- disposable-income and Needs Index Gini coefficients;
- a Green Deal Job Guarantee (with reference-calibration indexation disabled);
- minimal sectoral material-use accounting;
- four seed-level realism-hypothesis diagnostics.
- a common labour-productivity calibration that aligns period-0 and
  first-effective-demand employment around the 90% reference target.

## Seven experiments

The reference protocol contains seven experiments:

| ID | Scenario | Policy mode |
|---|---|---|
| E0 | Baseline | OFF |
| E1 | Carbon Tax | FIXED |
| E2 | Carbon Tax | ENDOGENOUS |
| E3 | Green Deal | FIXED |
| E4 | Green Deal | ENDOGENOUS |
| E5 | Post-Growth | FIXED |
| E6 | Post-Growth | ENDOGENOUS |

FIXED experiments keep the transition package active throughout
the simulation.

ENDOGENOUS experiments allow households to vote on the package.
The package may be rejected and subsequently reactivated.

Each central experiment exports both its explicit configuration and a
`resolved_parameters.json` file containing every effective parameter value.

## Robustness and sensitivity

Run the 30 paired seeds and bootstrap summaries with:

```powershell
python scripts/run_robustness.py --seeds 30
```

Run the central-seed OAT screen and create the 300-point Latin Hypercube with:

```powershell
python scripts/run_sensitivity.py oat --seeds 1
python scripts/run_sensitivity.py lhs-design --samples 300
python scripts/run_sensitivity.py lhs-run --limit 20 --seeds 1
python scripts/analyze_validation.py
```

For the full protocols specified in the guide, replace `--seeds 1` by
`--seeds 30` and remove the Latin Hypercube pilot limit by using `--limit 300`.
These full sensitivity campaigns are intentionally explicit because they are
computationally much larger than the seven central experiments.

## Repository structure

```text
senharp_core/
    model.py
    entities.py
    parameters.py
    collector.py
    ...

tests/
    ...

notebooks/
    01_run_seven_experiments.ipynb
    02_analyse_seven_experiments.ipynb

experiments/
    seven_experiments.json

ENVIRONMENT.txt
requirements.txt
README.md
# Manuscript figures

The paired robustness campaign automatically exports manuscript Figures 4–11
to `OUTPUT/figures/`. Solid lines represent endogenous political feedback and
dashed lines the same-seed fixed-policy counterfactual. Statistical results
shown on the figures are also written to
`OUTPUT/manuscript_figure_statistical_tests.csv` (Kruskal–Wallis omnibus tests
and Holm-corrected pairwise Mann–Whitney tests).
