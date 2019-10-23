import traceback

import services   # pylint: disable=import-error


from sims.sim_info import SimInfo  # pylint: disable=import-error
from sims.sim import Sim  # pylint: disable=import-error
from distributor.ops import SetIsNpc  # pylint: disable=import-error

from venues.zone_director_residential import ZoneDirectorResidentialBase  # pylint: disable=import-error

from control_any_sim.util.inject import inject_method_to, inject_field_to, inject_property_to
from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.services.interactions import InteractionsService
from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger


@inject_field_to(SimInfo, 'is_npc', (SetIsNpc))
def tn_sim_info_is_npc(self):
    return (services.active_sim_info() != self
            and services.active_household_id() != self.household_id)


@inject_property_to(SimInfo, 'is_selectable')
def tn_sim_info_is_selectable(self):
    active_household_id = services.active_household_id()
    client = (services.client_manager()
              .get_client_by_household_id(active_household_id))

    if client is None:
        return False

    return self in client.selectable_sims


@inject_property_to(Sim, 'is_selected')
def tn_sim_info_is_selected(self):
    active_household_id = services.active_household_id()
    client = (services.client_manager()
              .get_client_by_household_id(active_household_id))

    if client is not None:
        return self is client.active_sim

    return False


@GameEvents.on_zone_spin_up
def tn_init_services(_zone, household_id, _active_sim_id):
    try:
        SelectionGroupService.get(household_id)
    except BaseException:
        Logger.log(traceback.format_exc())


InteractionsService.bootstrap()


@inject_method_to(ZoneDirectorResidentialBase, '_is_any_sim_always_greeted')
def tn_zone_director_residential_base_is_any_sim_always_greeted(original,
                                                                self):
    active_lot_household = (services.current_zone()
                            .get_active_lot_owner_household())

    for sim_info in active_lot_household.sim_infos:
        if sim_info.id not in (SelectionGroupService
                               .get(services.active_household_id()).selectable_sims):
            continue

        return True

    return original(self)
