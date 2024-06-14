"""Main entry point for canys mod."""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Callable

import services
from distributor.ops import SetIsNpc
from objects.components.sim_inventory_component import (
    SimInventoryComponent,
)
from protocolbuffers import Sims_pb2
from server.client import Client
from sims.sim import Sim
from sims.sim_info import SimInfo
from venues.zone_director_residential import (
    ZoneDirectorResidentialBase,
)

import control_any_sim.cheats
from control_any_sim import ts4_services
from control_any_sim.services.integrity import IntegrityService
from control_any_sim.services.interactions_service import InteractionsService
from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.inject import (
    inject_field_to,
    inject_method_to,
    inject_property_to,
)
from control_any_sim.util.logger import Logger

if TYPE_CHECKING:
    from careers.career_enums import CareerCategory
    from zone import Zone


@inject_field_to(SimInfo, "is_npc", (SetIsNpc))
def canys_sim_info_is_npc(original: Callable[[SimInfo], bool], self: SimInfo) -> bool:
    """
    Override of the SimInfo::is_npc field.

    Returns true if a sim is not active and not a member of the current household.

    Sims that have been marked as household NPCs also return False when they are not active.
    """
    try:
        if services.active_sim_info() == self:
            return False

        if services.active_household_id() == self.household_id:
            selection_group = SelectionGroupService.get_existing()

            if not selection_group:
                return False

            return selection_group.is_household_npc(self)
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)
    else:
        return True


@inject_property_to(SimInfo, "is_selectable")
def canys_sim_info_is_selectable(
    original: Callable[[SimInfo], bool],
    self: SimInfo,
) -> bool:
    """
    Override of the SimInfo::is_selectable property.

    Makes all sims selectable that have been added to the client.
    """
    try:
        active_household_id = services.active_household_id()
        client = services.client_manager().get_client_by_household_id(
            active_household_id,
        )

        if client is None:
            return False

        return self in client.selectable_sims
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@inject_method_to(SimInfo, "get_is_enabled_in_skewer")
def canys_sim_info_get_is_enabled_in_skewer(
    original: Callable[[SimInfo, bool], bool],
    self: SimInfo,
    consider_active_sim: bool = True,  # noqa: FBT001, FBT002
) -> bool:
    """
    Override for SimInfo::get_is_enabled_in_skewer method.

    Returns false if a sim has been marked as household NPC. Otherwise the call is forwarded to the original implementation.
    """
    try:
        selection_group = SelectionGroupService.get_existing()

        if not selection_group:
            return original(self, consider_active_sim)

        if selection_group.is_household_npc(self):
            return False

        if selection_group.is_custom_sim(self.id):
            return True

        return original(self, consider_active_sim and can_consider_active_sim())

    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self, consider_active_sim)


def can_consider_active_sim() -> bool:
    """Check if the active sim is part of the current household."""
    client = ts4_services.client_manager().get_active_client()

    if client is None:
        return True

    active_sim_info: SimInfo = client.active_sim_info

    return active_sim_info.household_id == services.active_household_id()


@inject_property_to(Sim, "is_selected")
def canys_sim_info_is_selected(original: Callable[[Sim], bool], self: Sim) -> bool:
    """
    Override for Sim::is_selected property.

    Reduces the logic to wether the Sim is active in the client or not.
    """
    try:
        client = ts4_services.client_manager().get_active_client()

        if client is None:
            return False

        return self is client.active_sim

    except BaseException:
        Logger.log(traceback.format_exc())
        return original(self)


@GameEvents.on_zone_spin_up
def canys_init_services(_zone: Zone, household_id: int, _active_sim_id: int) -> None:
    """Game event listener for when a zone has been spun up."""
    SelectionGroupService.get(household_id)


@inject_method_to(ZoneDirectorResidentialBase, "_is_any_sim_always_greeted")
def canys_zone_director_residential_base_is_any_sim_always_greeted(
    original: Callable[[ZoneDirectorResidentialBase], bool],
    self: ZoneDirectorResidentialBase,
) -> bool:
    """
    Override for ZoneDirectorResidentialBase::_is_any_sim_always_greeted.

    Allows all sims in the selection group to be always greeted if any of them belongs to the lot household.
    """
    try:
        active_lot_household = services.current_zone().get_active_lot_owner_household()
        selection_group = SelectionGroupService.get(services.active_household_id())

        if active_lot_household is None:
            return original(self)

        for sim_info in active_lot_household.sim_infos:
            if sim_info.id not in selection_group.selectable_sims:
                continue

            return True

        return original(self)
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@inject_method_to(SimInventoryComponent, "allow_ui")
def tn_sim_inventory_component_allow_ui(
    original: Callable[[SimInventoryComponent], bool],
    self: SimInventoryComponent,
) -> bool:
    """
    Override for SimInventoryComponent::allow_ui method.

    Allows the inventory UI for every Sim that is currently selected.
    """
    try:
        if self.owner.is_selected:
            return True

        return original(self)
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@GameEvents.on_loading_screen_animation_finished
def canys_validate_version(_zone: Zone) -> None:
    """Game event callback for when the loading screen has disapeared."""
    IntegrityService.check_integrety(control_any_sim.__version__)


@inject_method_to(Client, "_get_selector_visual_type")
def canys_client_get_selector_visual_type(
    original: Callable[[Client, SimInfo], tuple[int, CareerCategory]],
    self: Client,
    sim_info: SimInfo,
) -> tuple[int, CareerCategory]:
    """
    Override for Client::_get_selector_visual_type method.

    Clear selector visual type override for controled sims.
    """
    try:
        Logger.log("getting selector visual type")

        selection_group = SelectionGroupService.get_existing()

        (original_type, original_career_category) = original(self, sim_info)

        if not selection_group:
            return (original_type, original_career_category)

        if original_type == Sims_pb2.SimPB.OTHER:
            Logger.log("original type is OTHER")
            sim_zone_id = sim_info.zone_id

            # Override default behavior if the sim is in the current zone.
            if sim_zone_id == services.current_zone_id():
                Logger.log("sim is in current zone so return NORMAL")
                return (Sims_pb2.SimPB.NORMAL, None)

        return (original_type, original_career_category)
    except Exception as err:
        Logger.error(f"{err}")
        Logger.error(traceback.format_exc())

        return original(self, sim_info)


Logger.log("starting control_any_sim...")

InteractionsService.bootstrap()
