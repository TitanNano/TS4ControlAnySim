import traceback

import services  # pylint: disable=import-error

from sims.sim_info import SimInfo  # pylint: disable=import-error
from sims.sim import Sim  # pylint: disable=import-error
from distributor.ops import SetIsNpc  # pylint: disable=import-error
from venues.zone_director_residential import ZoneDirectorResidentialBase  # pylint: disable=import-error
from objects.components.sim_inventory_component import SimInventoryComponent  # pylint: disable=import-error,E0611

import control_any_sim.cheats

from control_any_sim.util.inject import (
    inject_method_to,
    inject_field_to,
    inject_property_to,
)
from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.services.interactions import InteractionsService
from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger
from control_any_sim.services.integrity import IntegrityService


@inject_field_to(SimInfo, "is_npc", (SetIsNpc))
def canys_sim_info_is_npc(original, self):
    try:
        if services.active_sim_info() == self:
            return False

        if services.active_household_id() == self.household_id:
            selection_group = SelectionGroupService.get(
                services.active_household_id(), True
            )

            if not selection_group:
                return False

            return selection_group.is_household_npc(self)

        return True
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@inject_property_to(SimInfo, "is_selectable")
def canys_sim_info_is_selectable(original, self):
    try:
        active_household_id = services.active_household_id()
        client = services.client_manager().get_client_by_household_id(
            active_household_id
        )

        if client is None:
            return False

        return self in client.selectable_sims
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@inject_method_to(SimInfo, "get_is_enabled_in_skewer")
def canys_sim_info_get_is_enabled_in_skewer(original, self, consider_active_sim=True):
    try:
        selection_group = SelectionGroupService.get(
            services.active_household_id(), True
        )

        if selection_group and selection_group.is_household_npc(self):
            return False

        return original(self, consider_active_sim)
    except BaseException:
        Logger.log(traceback.format_exc())
        return True


@inject_property_to(Sim, "is_selected")
def canys_sim_info_is_selected(original, self):
    try:
        active_household_id = services.active_household_id()
        client = services.client_manager().get_client_by_household_id(
            active_household_id
        )

        if client is not None:
            return self is client.active_sim

        return False
    except BaseException:
        Logger.log(traceback.format_exc())
        return original(self)


@GameEvents.on_zone_spin_up
def canys_init_services(_zone, household_id, _active_sim_id):
    SelectionGroupService.get(household_id)


InteractionsService.bootstrap()


@inject_method_to(ZoneDirectorResidentialBase, "_is_any_sim_always_greeted")
def canys_zone_director_residential_base_is_any_sim_always_greeted(original, self):
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
def tn_sim_inventory_component_allow_ui(original, self):
    try:
        if self.owner.is_selected:
            return True

        return original(self)
    except BaseException:
        Logger.error(traceback.format_exc())
        return original(self)


@GameEvents.on_loading_screen_animation_finished
def canys_validate_version(_zone):
    IntegrityService.check_integrety(control_any_sim.__version__)


Logger.log("starting control_any_sim")
