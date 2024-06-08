"""
Core service of the mod.

Handles all the patching to make selectable NPC sims possible.
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import services
from objects import ALL_HIDDEN_REASONS
from objects.components.types import (
    INVENTORY_COMPONENT,
)
from sims.sim_info_lod import SimInfoLODLevel
from typing_extensions import Self, TypeVar

from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger
from control_any_sim.util.serialize import Serializable

if TYPE_CHECKING:
    from server.client import Client
    from sims.sim import Sim
    from sims.sim_info import SimInfo
    from zone import Zone


def get_home_dir() -> str:
    """Get path to mods install dir."""
    dir_name = Path(__file__).resolve().parent

    return str(dir_name / ".." / ".." / "..")


HOME_DIR = get_home_dir()


C = TypeVar("C", bound="SelectionGroupService")


class SelectionGroupService(Serializable):
    """Service to manage the selection group."""

    instance: Self | None = None
    zone_is_setup = False
    household_id: int
    selectable_sims: list[int]
    household_npcs: list[int]

    @classmethod
    def get(
        cls: type[SelectionGroupService],
        household_id: int,
    ) -> SelectionGroupService:
        """Get current instance of the service for the given household_id."""
        cls.instance = cls._get_instance(household_id)

        if not cls.instance.zone_is_setup:
            cls.instance.setup_zone()
            cls.instance.persist_state()

        return cls.instance

    @classmethod
    def get_existing(cls: type[SelectionGroupService]) -> SelectionGroupService | None:
        """Get the already initialized instance or None."""
        if not cls.instance:
            return None

        return cls.instance

    @classmethod
    def _get_instance(
        cls: type[SelectionGroupService],
        household_id: int,
    ) -> SelectionGroupService:
        if cls.instance is not None:
            return cls.instance

        Logger.log(f"selection group: no instance, {household_id}")

        # restore state
        try:
            with Path(HOME_DIR + "/selection_group.json").open(
                encoding="utf8",
            ) as file_handler:
                state = file_handler.read()

            Logger.log(f"restored state: {state}")
        except BaseException:
            state = None

        if state is None:
            return cls(household_id)

        # deserialize
        try:
            instance = cls.deserialize(state)

            if instance.household_id != household_id:
                return cls(household_id)

            return instance
        except BaseException:
            return cls(household_id)

    @property
    def client(self: Self) -> Client:
        """Get the current game client."""
        return services.get_first_client()

    def __init__(
        self: Self,
        household_id: int,
        selectable_sims: list[int] | None = None,
        zone_is_setup: bool | None = None,  # noqa: ARG002
        household_npcs: list[int] | None = None,
    ) -> None:
        """Create a new instance if the service."""
        self.household_id = household_id
        self.selectable_sims = selectable_sims if selectable_sims is not None else []
        self.household_npcs = household_npcs if household_npcs is not None else []

        if self.selectable_sims is None or len(self.selectable_sims) == 0:
            self.update_selectable_sims()

        GameEvents.on_zone_teardown(self.on_zone_teardown)
        GameEvents.on_active_sim_changed(self.on_active_sim_changed)

    def persist_state(self: Self) -> None:
        """Write current state of the service to disk."""
        data = self.serialize()

        with (Path(HOME_DIR) / "selection_group.json").open(
            "w",
            encoding="utf8",
        ) as file_handler:
            file_handler.write(data)

    def update_selectable_sims(self: Self) -> None:
        """Set selection group to all currently selectable sims."""
        selectable_sims = self.client.selectable_sims

        self.selectable_sims = [sim_info.id for sim_info in selectable_sims]

    def on_zone_teardown(self: Self, _zone: Zone, _client: Client) -> None:
        """
        Event handler for when the current zone is beeing teared down.

        Performs cleanup actions and removes all modifications from the game.
        """
        Logger.log("on_zone_teardown: tearing down SelectionGroupService")

        if not self.zone_is_setup:
            Logger.log("SelectionGroupService is already teared down")
            return

        self.persist_state()
        self.cleanup_sims()

        GameEvents.remove_zone_teardown(self.on_zone_teardown)

        self.zone_is_setup = False
        self.__class__.instance = None

    def make_sim_selectable(self: Self, sim_info: SimInfo) -> None:
        """Make the game add the provided sim info to the skewer."""
        if sim_info.is_selectable:
            return

        # request lod before adding to make sure everything is loaded
        sim_info.request_lod(SimInfoLODLevel.ACTIVE)

        self.client.add_selectable_sim_info(sim_info)

        currently_active_sim: SimInfo = self.client.active_sim_info

        # force the game to update now selectable NPC tracker information
        self.client.set_active_sim_by_id(sim_info.id)
        self.client.set_active_sim_by_id(currently_active_sim.id)

    def remove_sim(self: Self, sim_info: SimInfo) -> None:
        """Remove a sim info from the skewer."""
        if sim_info == self.client.active_sim_info:
            self.client.set_next_sim()

        self.client.remove_selectable_sim_by_id(sim_info.id)

    def setup_zone(self: Self) -> None:
        """Perform setup operations when the zone spins up."""
        if len(self.household_npcs) > 0:
            self.client.send_selectable_sims_update()

        for sim_info_id in self.selectable_sims:
            try:
                sim_info = services.sim_info_manager().get(sim_info_id)

                self.make_sim_selectable(sim_info)
            except BaseException:  # noqa: PERF203
                Logger.error(f"failed to add sim to skewer: {sim_info_id}")
                Logger.error(traceback.format_exc())

        self.client.selectable_sims.add_watcher(self, self.update_selectable_sims)
        self.update_selectable_sims()
        self.zone_is_setup = True

    def is_selectable(self: Self, sim_id: int) -> bool:
        """Check if the sim id is currently selectable."""
        test = sim_id in self.selectable_sims

        Logger.log(f"is sim {sim_id} in selectable list: {test}")

        return test

    def on_active_sim_changed(self: Self, _old_sim: Sim, _new_sim: Sim) -> None:
        """Event handler for when the active sim changes."""
        if self.client is None:
            Logger.log("active sim changed but we have no client, yet?")
            return

        sim_info: SimInfo = self.client.active_sim_info

        if sim_info is None:
            Logger.log("sim selection changed but no sim is selected")
            return

        if sim_info.household_id == self.household_id:
            return

        try:
            sim_info.request_lod(SimInfoLODLevel.ACTIVE)

            Logger.log(f"sim {sim_info!r} lod is now: {sim_info.lod}")

            if sim_info.zone_id > 0:
                Logger.log(f"Sim zone id is set: {sim_info.zone_id!r}")
                sim_info.away_action_tracker.refresh(on_travel_away=True)

            sim_info.relationship_tracker.clean_and_send_remaining_relationship_info()
            sim_info.publish_all_commodities()

            sim_instance = sim_info.get_sim_instance(
                allow_hidden_flags=ALL_HIDDEN_REASONS,
            )

            if sim_instance is not None:
                inventory = sim_instance.get_component(INVENTORY_COMPONENT)
                inventory.publish_inventory_items()
            else:
                Logger.log(f"there is no sim instance for {sim_info!r}")

        except BaseException:
            Logger.error(f"updating newly active sim: {sim_info!r}")
            Logger.error(traceback.format_exc())

    def cleanup_sims(self: Self) -> None:
        """Remove non household sims from the skewer."""
        for sim_info_id in self.selectable_sims:
            sim_info = services.sim_info_manager().get(sim_info_id)

            if sim_info is None:
                Logger.log(
                    f"sim with id {sim_info_id} does not exist and shouldn't apear here",
                )
                continue

            if sim_info.household_id == self.household_id:
                continue

            Logger.log(
                f"{sim_info} is not in household, removing to avoid teardown issues",
            )

            self.remove_sim(sim_info)

    def add_household_npc(self: Self, sim_info: SimInfo) -> None:
        """Add a sim as household NPC."""
        if sim_info == self.client.active_sim_info:
            self.client.set_next_sim()

        self.household_npcs.append(sim_info.id)
        self.client.send_selectable_sims_update()

    def remove_household_npc(self: Self, sim_info: SimInfo) -> None:
        """Remove a sim from household NPCs list."""
        self.household_npcs.remove(sim_info.id)
        self.client.send_selectable_sims_update()

    def is_household_npc(self: Self, sim_info: SimInfo) -> bool:
        """Check if a given SimInfo is a household NPC."""
        return sim_info.id in self.household_npcs
