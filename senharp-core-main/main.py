from pathlib import Path
from senharp_core.entities import Scenario
from senharp_core.model import Model
from senharp_core.parameters import Parameters

def main() -> None:
    params = Parameters()
    for scenario in Scenario:
        model = Model(params, scenario)
        collector = model.run()
        collector.export(Path("outputs") / scenario.value)
        final = collector.macro_rows[-1]
        print(f"{scenario.value:12s} | NeedsIndex={final['mean_needs_index']:.2f} | soutien={final['mean_vote_probability']:.2%} | politique active={bool(final['policy_active'])}")

if __name__ == "__main__":
    main()
