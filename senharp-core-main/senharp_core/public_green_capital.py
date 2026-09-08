"""Accumulation of government-owned green capital."""

from .entities import Government
from .parameters import Parameters


def accumulate_public_green_capital(
    government: Government,
    period: int,
    params: Parameters,
) -> dict[str, float]:
    """Update the closing public green-capital stock.

    Public green investment delivered in period t enters the
    closing stock and becomes available from period t+1.

    The first implementation uses the same depreciation rate
    as private productive capital to avoid introducing an
    additional calibration parameter.
    """

    depreciation_rate = (
        params.capital_depreciation_rate
    )

    if not 0.0 <= depreciation_rate <= 1.0:
        raise ValueError(
            "capital_depreciation_rate must be "
            "between zero and one."
        )

    opening_public_green_capital = max(
        0.0,
        government.public_green_capital,
    )

    realised_public_green_investment = max(
        0.0,
        government.realised_public_green_investment,
    )

    government.public_green_capital_depreciation = 0.0

    # Period 0 represents the initial state.
    if period == 0:
        return {
            "opening_public_green_capital": (
                opening_public_green_capital
            ),
            "public_green_capital_depreciation": 0.0,
            "realised_public_green_investment": 0.0,
            "closing_public_green_capital": (
                opening_public_green_capital
            ),
            "public_green_capital_identity_gap": 0.0,
        }

    public_green_capital_depreciation = (
        depreciation_rate
        * opening_public_green_capital
    )

    closing_public_green_capital = max(
        0.0,
        (
            opening_public_green_capital
            - public_green_capital_depreciation
            + realised_public_green_investment
        ),
    )

    government.public_green_capital_depreciation = (
        public_green_capital_depreciation
    )

    government.public_green_capital = (
        closing_public_green_capital
    )

    identity_gap = (
        closing_public_green_capital
        - opening_public_green_capital
        + public_green_capital_depreciation
        - realised_public_green_investment
    )
    if abs(identity_gap) < 1e-10:
        identity_gap = 0.0

    return {
        "opening_public_green_capital": (
            opening_public_green_capital
        ),
        "public_green_capital_depreciation": (
            public_green_capital_depreciation
        ),
        "realised_public_green_investment": (
            realised_public_green_investment
        ),
        "closing_public_green_capital": (
            closing_public_green_capital
        ),
        "public_green_capital_identity_gap": (
            identity_gap
        ),
    }
