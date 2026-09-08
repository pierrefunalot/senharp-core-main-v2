"""Run OAT screening and create/replay the Latin Hypercube design."""

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from senharp_core.parameters import Parameters
from senharp_core.validation_protocol import (
    FIXED_IDS,
    OAT_PARAMETERS,
    latin_hypercube_design,
    load_protocol_config,
    run_experiment_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["oat", "lhs-design", "lhs-run"])
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--first-seed", type=int, default=1761)
    parser.add_argument("--samples", type=int, default=300)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", default="outputs/sensitivity")
    args = parser.parse_args()

    config = load_protocol_config(PROJECT_ROOT / "experiments/seven_experiments.json")
    experiments = [e for e in config["experiments"] if e["id"] in FIXED_IDS]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    if args.mode == "lhs-design":
        latin_hypercube_design(args.samples, args.first_seed).to_csv(
            output / "latin_hypercube_design.csv", index=False
        )
        return

    rows = []
    trajectory_rows = []
    if args.mode == "oat":
        base = Parameters()
        for name in OAT_PARAMETERS:
            for multiplier in [0.0, 0.5, 1.0, 1.5, 2.0]:
                print(name, multiplier, flush=True)
                extra = {name: float(getattr(base, name)) * multiplier}
                for seed in range(args.first_seed, args.first_seed + args.seeds):
                    for experiment in experiments:
                        result = run_experiment_summary(config, experiment, seed, extra)
                        final = result[-1] | {
                            "sensitivity_parameter": name,
                            "multiplier": multiplier,
                        }
                        final["cumulative_industrial_emissions"] = sum(
                            row["industrial_emissions"] for row in result
                        )
                        final["cumulative_material_use"] = sum(
                            row["material_use"] for row in result
                        )
                        rows.append(final)
        pd.DataFrame(rows).to_csv(output / "oat_results.csv", index=False)
        return

    design_path = output / "latin_hypercube_design.csv"
    if not design_path.exists():
        latin_hypercube_design(args.samples, args.first_seed).to_csv(design_path, index=False)
    design = pd.read_csv(design_path).head(args.limit)
    for _, design_row in design.iterrows():
        design_id = int(design_row.pop("design_id"))
        extra = design_row.to_dict()
        extra["green_deal_carbon_dividend_share"] = (
            1.0 - extra["green_deal_public_investment_share"]
        )
        print("design", design_id, flush=True)
        for seed in range(args.first_seed, args.first_seed + args.seeds):
            for experiment in experiments:
                result = run_experiment_summary(config, experiment, seed, extra)
                trajectory_rows.extend(
                    row | {"design_id": design_id}
                    for row in result
                )
                final = result[-1] | {"design_id": design_id}
                final["cumulative_industrial_emissions"] = sum(
                    row["industrial_emissions"] for row in result
                )
                final["cumulative_material_use"] = sum(
                    row["material_use"] for row in result
                )
                rows.append(final)
    pd.DataFrame(rows).to_csv(output / "latin_hypercube_results.csv", index=False)
    pd.DataFrame(trajectory_rows).to_csv(
        output / "latin_hypercube_trajectories.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
