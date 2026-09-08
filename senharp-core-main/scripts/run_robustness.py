"""Run paired multi-seed validation and export bootstrap diagnostics."""

import argparse
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from senharp_core.validation_protocol import (
    export_robustness_analysis,
    load_protocol_config,
    run_experiment_summary,
    write_resolved_parameter_manifest,
)
from senharp_core.robustness_graphs import export_manuscript_figures
from senharp_core.empirical_validation import export_realism_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--first-seed", type=int, default=1761)
    parser.add_argument("--output", default="outputs/robustness_30_seeds")
    args = parser.parse_args()

    config = load_protocol_config(PROJECT_ROOT / "experiments/seven_experiments.json")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    write_resolved_parameter_manifest(config, output, args.first_seed)

    rows = []
    needs_snapshots = []
    for seed in range(args.first_seed, args.first_seed + args.seeds):
        print(f"seed {seed}", flush=True)
        for experiment in config["experiments"]:
            rows.extend(
                run_experiment_summary(
                    config, experiment, seed, needs_snapshots=needs_snapshots
                )
            )

    trajectories = pd.DataFrame(rows)
    trajectories.to_csv(output / "trajectories.csv", index=False)
    needs = pd.DataFrame(needs_snapshots)
    needs.to_csv(output / "needs_index_snapshots.csv", index=False)
    export_robustness_analysis(trajectories, output)
    export_manuscript_figures(trajectories, output, needs)
    export_realism_validation(trajectories, needs, output)


if __name__ == "__main__":
    main()
