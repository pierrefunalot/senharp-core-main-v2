"""Graph-generation utilities for SEN-HARP Core v0.3.

The module reads the model collector and generates a compact set of
baseline diagnostics before activation of voting and policy packages.

Typical use
-----------
from senharp_core.graphs import generate_baseline_graphs

paths = generate_baseline_graphs(
    model=model_trajectory,
    output_dir="outputs/graphs/baseline_seed_1761",
    show=False,
)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_DPI = 180


def collector_frames(
    model: Any,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return macro, firm and household DataFrames from a model collector."""

    collector = model.collector

    macro_df = pd.DataFrame(
        collector.macro_rows
    )
    firm_df = pd.DataFrame(
        collector.firm_rows
    )
    household_df = pd.DataFrame(
        collector.household_rows
    )

    return (
        macro_df,
        firm_df,
        household_df,
    )


def _require_columns(
    dataframe: pd.DataFrame,
    columns: Iterable[str],
    dataframe_name: str,
) -> None:
    """Raise a clear error when required columns are absent."""

    missing = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing:
        raise KeyError(
            f"Colonnes manquantes dans {dataframe_name}: "
            f"{missing}"
        )


def _first_existing_column(
    dataframe: pd.DataFrame,
    candidates: Iterable[str],
) -> str | None:
    """Return the first candidate column present in a DataFrame."""

    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    return None


def _prepare_period_column(
    dataframe: pd.DataFrame,
    dataframe_name: str,
) -> pd.DataFrame:
    """Return a copy with a numeric, sorted period column."""

    _require_columns(
        dataframe=dataframe,
        columns=["period"],
        dataframe_name=dataframe_name,
    )

    result = dataframe.copy()
    result["period"] = pd.to_numeric(
        result["period"],
        errors="raise",
    )

    return result.sort_values(
        "period"
    )


def _save_or_show(
    figure: plt.Figure,
    output_path: str | Path | None,
    show: bool,
) -> Path | None:
    """Save a figure, optionally display it, and close it otherwise."""

    saved_path: Path | None = None

    if output_path is not None:
        saved_path = Path(
            output_path
        )
        saved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        figure.savefig(
            saved_path,
            dpi=DEFAULT_DPI,
            bbox_inches="tight",
        )

    if show:
        plt.show()
    else:
        plt.close(
            figure
        )

    return saved_path


def _aggregate_firm_series(
    firm_df: pd.DataFrame,
    value_column: str,
) -> pd.Series:
    """Aggregate one firm-level variable by period."""

    prepared = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )

    _require_columns(
        dataframe=prepared,
        columns=[value_column],
        dataframe_name="firm_df",
    )

    return (
        prepared
        .groupby("period")[value_column]
        .sum()
        .sort_index()
    )


def plot_employment_and_unemployment(
    firm_df: pd.DataFrame,
    household_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot private employment and unemployment by period."""

    firms = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )
    households = _prepare_period_column(
        dataframe=household_df,
        dataframe_name="household_df",
    )

    employment_column = _first_existing_column(
        firms,
        [
            "total_employment",
            "private_jobs",
            "employment",
        ],
    )

    if employment_column is not None:
        private_jobs = (
            firms
            .groupby("period")[employment_column]
            .sum()
            .sort_index()
        )
    else:
        _require_columns(
            dataframe=households,
            columns=["employment_status"],
            dataframe_name="household_df",
        )

        private_jobs = (
            households
            .assign(
                is_employed=(
                    households["employment_status"]
                    .astype(str)
                    .str.upper()
                    .ne("UNEMPLOYED")
                )
            )
            .groupby("period")["is_employed"]
            .sum()
            .sort_index()
        )

    _require_columns(
        dataframe=households,
        columns=["employment_status"],
        dataframe_name="household_df",
    )

    unemployed = (
        households
        .assign(
            is_unemployed=(
                households["employment_status"]
                .astype(str)
                .str.upper()
                .eq("UNEMPLOYED")
            )
        )
        .groupby("period")["is_unemployed"]
        .sum()
        .sort_index()
    )

    figure, axis = plt.subplots(
        figsize=(8, 5)
    )

    axis.plot(
        private_jobs.index,
        private_jobs.values,
        label="Emploi privé",
    )
    axis.plot(
        unemployed.index,
        unemployed.values,
        label="Chômage",
    )

    axis.set_title(
        "Emploi privé et chômage"
    )
    axis.set_xlabel(
        "Période"
    )
    axis.set_ylabel(
        "Nombre de ménages"
    )
    axis.grid(
        True,
        alpha=0.3,
    )
    axis.legend()

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_output_and_emissions(
    macro_df: pd.DataFrame,
    firm_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot actual output and industrial emissions."""

    macro = _prepare_period_column(
        dataframe=macro_df,
        dataframe_name="macro_df",
    )

    _require_columns(
        dataframe=macro,
        columns=["industrial_emissions"],
        dataframe_name="macro_df",
    )

    actual_output = _aggregate_firm_series(
        firm_df=firm_df,
        value_column="actual_output",
    )

    emissions = (
        macro
        .drop_duplicates("period")
        .set_index("period")[
            "industrial_emissions"
        ]
        .sort_index()
    )

    figure, output_axis = plt.subplots(
        figsize=(8, 5)
    )
    emissions_axis = output_axis.twinx()

    output_axis.plot(
        actual_output.index,
        actual_output.values,
        label="Output réalisé",
    )
    emissions_axis.plot(
        emissions.index,
        emissions.values,
        label="Émissions industrielles",
    )

    output_axis.set_title(
        "Output réalisé et émissions industrielles"
    )
    output_axis.set_xlabel(
        "Période"
    )
    output_axis.set_ylabel(
        "Output réalisé"
    )
    emissions_axis.set_ylabel(
        "Émissions industrielles"
    )
    output_axis.grid(
        True,
        alpha=0.3,
    )

    lines = (
        output_axis.get_lines()
        + emissions_axis.get_lines()
    )
    labels = [
        line.get_label()
        for line in lines
    ]
    output_axis.legend(
        lines,
        labels,
        loc="best",
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_income_and_needs_index(
    macro_df: pd.DataFrame,
    household_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot mean economic disposable income and mean NeedsIndex."""

    macro = _prepare_period_column(
        dataframe=macro_df,
        dataframe_name="macro_df",
    )
    households = _prepare_period_column(
        dataframe=household_df,
        dataframe_name="household_df",
    )

    income_column = _first_existing_column(
        macro,
        [
            "mean_economic_disposable_income",
            "mean_economic_income",
        ],
    )

    if income_column is not None:
        mean_income = (
            macro
            .drop_duplicates("period")
            .set_index("period")[
                income_column
            ]
            .sort_index()
        )
    else:
        _require_columns(
            dataframe=households,
            columns=[
                "economic_disposable_income",
            ],
            dataframe_name="household_df",
        )
        mean_income = (
            households
            .groupby("period")[
                "economic_disposable_income"
            ]
            .mean()
            .sort_index()
        )

    if "mean_needs_index" in macro.columns:
        mean_needs = (
            macro
            .drop_duplicates("period")
            .set_index("period")[
                "mean_needs_index"
            ]
            .sort_index()
        )
    else:
        _require_columns(
            dataframe=households,
            columns=["needs_index"],
            dataframe_name="household_df",
        )
        mean_needs = (
            households
            .groupby("period")[
                "needs_index"
            ]
            .mean()
            .sort_index()
        )

    figure, income_axis = plt.subplots(
        figsize=(8, 5)
    )
    needs_axis = income_axis.twinx()

    income_axis.plot(
        mean_income.index,
        mean_income.values,
        label="Revenu économique disponible moyen",
    )
    needs_axis.plot(
        mean_needs.index,
        mean_needs.values,
        label="NeedsIndex moyen",
    )

    income_axis.set_title(
        "Revenu économique et NeedsIndex"
    )
    income_axis.set_xlabel(
        "Période"
    )
    income_axis.set_ylabel(
        "Revenu économique moyen"
    )
    needs_axis.set_ylabel(
        "NeedsIndex moyen"
    )
    income_axis.grid(
        True,
        alpha=0.3,
    )

    lines = (
        income_axis.get_lines()
        + needs_axis.get_lines()
    )
    labels = [
        line.get_label()
        for line in lines
    ]
    income_axis.legend(
        lines,
        labels,
        loc="best",
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_needs_index_distribution(
    household_df: pd.DataFrame,
    period: int | None = None,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot the NeedsIndex distribution at one period."""

    households = _prepare_period_column(
        dataframe=household_df,
        dataframe_name="household_df",
    )

    _require_columns(
        dataframe=households,
        columns=["needs_index"],
        dataframe_name="household_df",
    )

    selected_period = (
        int(households["period"].max())
        if period is None
        else int(period)
    )

    selected = households.loc[
        households["period"] == selected_period
    ].copy()

    if selected.empty:
        raise ValueError(
            f"Aucune observation pour la période "
            f"{selected_period}."
        )

    figure, axis = plt.subplots(
        figsize=(8, 5)
    )

    if "employment_status" in selected.columns:
        for status, group in selected.groupby(
            selected[
                "employment_status"
            ].astype(str)
        ):
            axis.hist(
                group["needs_index"],
                bins=20,
                alpha=0.55,
                label=status,
            )
        axis.legend()
    else:
        axis.hist(
            selected["needs_index"],
            bins=20,
            alpha=0.7,
        )

    axis.axvline(
        100.0,
        linestyle="--",
        label="Seuil 100",
    )
    axis.set_title(
        f"Distribution du NeedsIndex à t={selected_period}"
    )
    axis.set_xlabel(
        "NeedsIndex"
    )
    axis.set_ylabel(
        "Nombre de ménages"
    )
    axis.grid(
        True,
        alpha=0.3,
    )

    handles, labels = axis.get_legend_handles_labels()
    if labels:
        axis.legend(
            handles,
            labels,
        )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_financial_stocks(
    macro_df: pd.DataFrame,
    firm_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot firm debt and public debt when the latter is available."""

    firms = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )
    macro = _prepare_period_column(
        dataframe=macro_df,
        dataframe_name="macro_df",
    )

    if "total_debt" in firms.columns:
        firm_debt = (
            firms
            .groupby("period")["total_debt"]
            .sum()
            .sort_index()
        )
    elif {
        "brown_loans",
        "green_loans",
    }.issubset(firms.columns):
        firm_debt = (
            firms
            .assign(
                total_debt=(
                    firms["brown_loans"]
                    + firms["green_loans"]
                )
            )
            .groupby("period")["total_debt"]
            .sum()
            .sort_index()
        )
    else:
        raise KeyError(
            "Impossible de calculer la dette des firmes: "
            "colonnes total_debt ou brown_loans/green_loans absentes."
        )

    public_debt_column = _first_existing_column(
        macro,
        [
            "public_debt",
            "government_debt",
            "total_public_debt",
        ],
    )

    figure, axis = plt.subplots(
        figsize=(8, 5)
    )

    axis.plot(
        firm_debt.index,
        firm_debt.values,
        label="Dette des firmes",
    )

    if public_debt_column is not None:
        public_debt = (
            macro
            .drop_duplicates("period")
            .set_index("period")[
                public_debt_column
            ]
            .sort_index()
        )
        axis.plot(
            public_debt.index,
            public_debt.values,
            label="Dette publique",
        )

    axis.set_title(
        "Stocks de dette"
    )
    axis.set_xlabel(
        "Période"
    )
    axis.set_ylabel(
        "Unités monétaires"
    )
    axis.grid(
        True,
        alpha=0.3,
    )
    axis.legend()

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_climate_state(
    macro_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot atmospheric temperature and climate damage."""

    macro = _prepare_period_column(
        dataframe=macro_df,
        dataframe_name="macro_df",
    )

    _require_columns(
        dataframe=macro,
        columns=[
            "atmospheric_temperature",
            "climate_damage",
        ],
        dataframe_name="macro_df",
    )

    macro = (
        macro
        .drop_duplicates("period")
        .set_index("period")
        .sort_index()
    )

    figure, temperature_axis = plt.subplots(
        figsize=(8, 5)
    )
    damage_axis = temperature_axis.twinx()

    temperature_axis.plot(
        macro.index,
        macro["atmospheric_temperature"],
        label="Température atmosphérique",
    )
    damage_axis.plot(
        macro.index,
        macro["climate_damage"],
        label="Dommage climatique",
    )

    temperature_axis.set_title(
        "Température et dommage climatique"
    )
    temperature_axis.set_xlabel(
        "Période"
    )
    temperature_axis.set_ylabel(
        "Température"
    )
    damage_axis.set_ylabel(
        "Dommage climatique"
    )
    temperature_axis.grid(
        True,
        alpha=0.3,
    )

    lines = (
        temperature_axis.get_lines()
        + damage_axis.get_lines()
    )
    labels = [
        line.get_label()
        for line in lines
    ]
    temperature_axis.legend(
        lines,
        labels,
        loc="best",
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_capital_and_climate_losses(
    firm_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot productive capital and climate-related capital losses."""

    firms = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )

    _require_columns(
        dataframe=firms,
        columns=[
            "brown_capital",
            "green_capital",
            "climate_capital_loss",
        ],
        dataframe_name="firm_df",
    )

    aggregate = (
        firms
        .groupby("period")
        .agg(
            brown_capital=(
                "brown_capital",
                "sum",
            ),
            green_capital=(
                "green_capital",
                "sum",
            ),
            climate_capital_loss=(
                "climate_capital_loss",
                "sum",
            ),
        )
        .sort_index()
    )

    figure, capital_axis = plt.subplots(
        figsize=(8, 5)
    )
    loss_axis = capital_axis.twinx()

    capital_axis.plot(
        aggregate.index,
        aggregate["brown_capital"],
        label="Capital brun",
    )
    capital_axis.plot(
        aggregate.index,
        aggregate["green_capital"],
        label="Capital vert",
    )
    loss_axis.plot(
        aggregate.index,
        aggregate["climate_capital_loss"],
        label="Pertes climatiques de capital",
    )

    capital_axis.set_title(
        "Capital productif et pertes climatiques"
    )
    capital_axis.set_xlabel(
        "Période"
    )
    capital_axis.set_ylabel(
        "Stock de capital"
    )
    loss_axis.set_ylabel(
        "Perte climatique de capital"
    )
    capital_axis.grid(
        True,
        alpha=0.3,
    )

    lines = (
        capital_axis.get_lines()
        + loss_axis.get_lines()
    )
    labels = [
        line.get_label()
        for line in lines
    ]
    capital_axis.legend(
        lines,
        labels,
        loc="best",
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def plot_sector_output(
    firm_df: pd.DataFrame,
    period: int | None = None,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot actual output by sector at one period."""

    firms = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )

    _require_columns(
        dataframe=firms,
        columns=[
            "sector",
            "actual_output",
        ],
        dataframe_name="firm_df",
    )

    selected_period = (
        int(firms["period"].max())
        if period is None
        else int(period)
    )

    selected = firms.loc[
        firms["period"] == selected_period
    ].copy()

    if selected.empty:
        raise ValueError(
            f"Aucune observation de firme pour "
            f"la période {selected_period}."
        )

    selected["sector_label"] = (
        selected["sector"]
        .astype(str)
        .str.replace(
            "Sector.",
            "",
            regex=False,
        )
    )

    sector_output = (
        selected
        .groupby("sector_label")[
            "actual_output"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    figure, axis = plt.subplots(
        figsize=(8, 5)
    )

    axis.bar(
        sector_output.index,
        sector_output.values,
    )

    axis.set_title(
        f"Output réalisé par secteur à t={selected_period}"
    )
    axis.set_xlabel(
        "Secteur"
    )
    axis.set_ylabel(
        "Output réalisé"
    )
    axis.tick_params(
        axis="x",
        rotation=35,
    )
    axis.grid(
        True,
        axis="y",
        alpha=0.3,
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def compute_accounting_gaps(
    macro_df: pd.DataFrame,
    firm_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute core accounting and biophysical identity gaps."""

    macro = _prepare_period_column(
        dataframe=macro_df,
        dataframe_name="macro_df",
    ).drop_duplicates(
        "period"
    )

    firms = _prepare_period_column(
        dataframe=firm_df,
        dataframe_name="firm_df",
    )

    result = pd.DataFrame(
        {
            "period": sorted(
                macro["period"].unique()
            )
        }
    )

    indexed_macro = macro.set_index(
        "period"
    )

    if {
        "modelled_economy_emissions",
        "industrial_emissions",
        "land_use_emissions",
    }.issubset(macro.columns):
        result[
            "modelled_emissions_gap"
        ] = result["period"].map(
            (
                indexed_macro[
                    "modelled_economy_emissions"
                ]
                - indexed_macro[
                    "industrial_emissions"
                ]
                - indexed_macro[
                    "land_use_emissions"
                ]
            )
        )

    if {
        "world_emissions",
        "modelled_economy_emissions",
        "rest_of_world_emissions",
    }.issubset(macro.columns):
        result[
            "world_emissions_gap"
        ] = result["period"].map(
            (
                indexed_macro[
                    "world_emissions"
                ]
                - indexed_macro[
                    "modelled_economy_emissions"
                ]
                - indexed_macro[
                    "rest_of_world_emissions"
                ]
            )
        )

    if {
        "industrial_emissions",
    }.issubset(macro.columns) and (
        "production_emissions"
        in firms.columns
    ):
        firm_emissions = (
            firms
            .groupby("period")[
                "production_emissions"
            ]
            .sum()
        )

        result[
            "firm_macro_emissions_gap"
        ] = result["period"].map(
            indexed_macro[
                "industrial_emissions"
            ]
            - firm_emissions
        )

    for column in macro.columns:
        if column.endswith(
            "_gap"
        ):
            result[column] = result[
                "period"
            ].map(
                indexed_macro[column]
            )

    return result


def plot_accounting_gaps(
    macro_df: pd.DataFrame,
    firm_df: pd.DataFrame,
    output_path: str | Path | None = None,
    show: bool = False,
) -> Path | None:
    """Plot absolute accounting gaps available in the collector."""

    gaps = compute_accounting_gaps(
        macro_df=macro_df,
        firm_df=firm_df,
    )

    gap_columns = [
        column
        for column in gaps.columns
        if column != "period"
    ]

    if not gap_columns:
        raise KeyError(
            "Aucun écart comptable ou biophysique "
            "n'a pu être construit."
        )

    figure, axis = plt.subplots(
        figsize=(8, 5)
    )

    for column in gap_columns:
        axis.plot(
            gaps["period"],
            gaps[column].abs(),
            label=column,
        )

    axis.set_title(
        "Écarts absolus des identités comptables"
    )
    axis.set_xlabel(
        "Période"
    )
    axis.set_ylabel(
        "Écart absolu"
    )
    axis.grid(
        True,
        alpha=0.3,
    )
    axis.legend(
        fontsize="small",
    )

    figure.tight_layout()

    return _save_or_show(
        figure=figure,
        output_path=output_path,
        show=show,
    )


def generate_baseline_graphs(
    model: Any,
    output_dir: str | Path = "outputs/graphs/baseline",
    show: bool = False,
    strict: bool = False,
) -> dict[str, Path]:
    """Generate a standard baseline graph pack.

    Parameters
    ----------
    model
        A fully simulated SEN-HARP model.
    output_dir
        Destination directory for PNG files.
    show
        Display figures interactively when True.
    strict
        Raise immediately when one graph cannot be produced.
        When False, unavailable graphs are skipped.

    Returns
    -------
    dict[str, Path]
        Mapping from graph name to generated file path.
    """

    macro_df, firm_df, household_df = (
        collector_frames(
            model=model,
        )
    )

    destination = Path(
        output_dir
    )
    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    graph_jobs = {
        "employment_unemployment": (
            plot_employment_and_unemployment,
            {
                "firm_df": firm_df,
                "household_df": household_df,
            },
        ),
        "output_emissions": (
            plot_output_and_emissions,
            {
                "macro_df": macro_df,
                "firm_df": firm_df,
            },
        ),
        "income_needs_index": (
            plot_income_and_needs_index,
            {
                "macro_df": macro_df,
                "household_df": household_df,
            },
        ),
        "needs_distribution": (
            plot_needs_index_distribution,
            {
                "household_df": household_df,
            },
        ),
        "financial_stocks": (
            plot_financial_stocks,
            {
                "macro_df": macro_df,
                "firm_df": firm_df,
            },
        ),
        "climate_state": (
            plot_climate_state,
            {
                "macro_df": macro_df,
            },
        ),
        "capital_climate_losses": (
            plot_capital_and_climate_losses,
            {
                "firm_df": firm_df,
            },
        ),
        "sector_output": (
            plot_sector_output,
            {
                "firm_df": firm_df,
            },
        ),
        "accounting_gaps": (
            plot_accounting_gaps,
            {
                "macro_df": macro_df,
                "firm_df": firm_df,
            },
        ),
    }

    generated: dict[str, Path] = {}

    for graph_name, (
        function,
        arguments,
    ) in graph_jobs.items():
        output_path = (
            destination
            / f"{graph_name}.png"
        )

        try:
            saved_path = function(
                **arguments,
                output_path=output_path,
                show=show,
            )
        except (
            KeyError,
            ValueError,
            TypeError,
        ) as error:
            if strict:
                raise

            print(
                f"[graphs] Graphique ignoré "
                f"({graph_name}): {error}"
            )
            continue

        if saved_path is not None:
            generated[
                graph_name
            ] = saved_path

    return generated
