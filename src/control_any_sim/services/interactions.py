"""Service to inject new interactions into the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import services

from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger

if TYPE_CHECKING:
    from sims.sim import Sim
    from type import Self


class InteractionsService:
    """Injects new interactions into the game."""

    sim_interactions = (
        16489283597599966859,
        10989771389858450567,
        18214597616328370004,
        16534221441995016557,
        13559468593102065089,
        12276091593751358701,
    )

    @classmethod
    def bootstrap(cls: type[Self]) -> None:
        """Boostrap service and inject event listeners."""
        Logger.log("bootstrapping interactions service...")
        GameEvents.on_add_sim(cls.inject_into_sim)
        GameEvents.on_add_sim(cls.inject_into_relationship_panel)

    @classmethod
    def inject_into_sim(cls: type[Self], sim: Sim) -> None:
        """Event listener that runs every time a new sim is added."""
        affordance_manager = services.affordance_manager()
        injected_interactions = []

        for interaction_id in cls.sim_interactions:
            interaction_class = affordance_manager.get(interaction_id)

            if interaction_class is None:
                Logger.log(
                    f"interaction {interaction_id} not found in affordance_manager",
                )
                continue

            injected_interactions.append(interaction_class)

        sim._super_affordances = sim._super_affordances + tuple(injected_interactions)  # noqa: SLF001

    @classmethod
    def inject_into_relationship_panel(cls: type[Self], sim: Sim) -> None:
        """Event listener that adds interactions to the relationship panel everytime a sim is loaded."""
        affordance_manager = services.affordance_manager()
        injected_interactions = []

        for interaction_id in cls.sim_interactions:
            interaction_class = affordance_manager.get(interaction_id)

            if interaction_class is None:
                Logger.log(
                    f"interaction {interaction_id} not found in affordance_manager",
                )
                continue

            injected_interactions.append(interaction_class)

        sim._relation_panel_affordances = sim._relation_panel_affordances + tuple(  # noqa: SLF001
            injected_interactions,
        )
