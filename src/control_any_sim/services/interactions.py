import services  # pylint: disable=import-error

from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger


class InteractionsService:

    sim_interactions = (
        16489283597599966859,
        10989771389858450567,
        18214597616328370004,
        16534221441995016557,
        13559468593102065089,
        12276091593751358701
    )

    @classmethod
    def bootstrap(cls):
        GameEvents.on_add_sim(cls.inject_into_sim)
        GameEvents.on_add_sim(cls.inject_into_relationship_panel)

    @classmethod
    def inject_into_sim(cls, sim):
        affordance_manager = services.affordance_manager()
        injected_interactions = []

        for interaction_id in cls.sim_interactions:
            interaction_class = affordance_manager.get(interaction_id)

            if interaction_class is None:
                Logger.log('interaction {} not found in affordance_manager'
                           .format(interaction_id))
                continue

            injected_interactions.append(interaction_class)

        sim._super_affordances = (sim._super_affordances
                                  + tuple(injected_interactions))

    @classmethod
    def inject_into_relationship_panel(cls, sim):
        affordance_manager = services.affordance_manager()
        injected_interactions = []

        for interaction_id in cls.sim_interactions:
            interaction_class = affordance_manager.get(interaction_id)

            if interaction_class is None:
                Logger.log('interaction {} not found in affordance_manager'
                           .format(interaction_id))
                continue

            injected_interactions.append(interaction_class)

        sim._relation_panel_affordances = (sim._relation_panel_affordances
                                           + tuple(injected_interactions))
