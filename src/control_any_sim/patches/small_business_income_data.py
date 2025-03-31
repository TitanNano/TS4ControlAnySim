"""Patches for the SmallBusinessIncomeData class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from small_business.small_business_income_data import SmallBusinessIncomeData

from control_any_sim.util.inject import (
    inject_method_to,
)

if TYPE_CHECKING:
    from sims.sim import Sim


@inject_method_to(SmallBusinessIncomeData, "_should_apply_markup_for_gain")
def canys_should_apply_markup_for_gain(original: Callable[[SmallBusinessIncomeData, Sim, Any, Any], bool], self: SmallBusinessIncomeData, target_sim: Sim, interaction: Any, tags: Any | None = None) -> bool:  # noqa: ANN401
    """
    Override for SmallBusinessIncomeData::_should_apply_markup_for_gain method.

    Fixes bug in the original implementation when the interaction.sim is not present.

    Returns:
        If the markup should be applied.

    """
    if target_sim is None:
        return False

    # set an interaction sim when none is present. The original function incorrectly checks for a null value and runs into an attribute error otherwise.
    if interaction is not None and self.is_sim_an_employee(target_sim.sim_info) and isinstance(interaction.sim, property):
        interaction.sim = target_sim

    return original(self, target_sim, interaction, tags)
