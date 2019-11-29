from os import path
import traceback

import services  # pylint: disable=import-error

from control_any_sim.util.serialize import serialize
from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger
from sims.sim_info_lod import SimInfoLODLevel  # pylint: disable=import-error
from objects import ALL_HIDDEN_REASONS  # pylint: disable=import-error,E0611
from objects.components.types import INVENTORY_COMPONENT  # pylint: disable=import-error,E0611


def get_home_dir():
    dir_name = path.dirname(path.abspath(__file__))
    home_dir = path.normpath(path.join(dir_name, '../../../'))

    return home_dir


HOME_DIR = get_home_dir()


@serialize
class SelectionGroupService:

    instance = None
    zone_is_setup = False
    household_id = None
    selectable_sims = None
    household_npcs = None

    @classmethod
    def get(cls, household_id, no_init=False):
        if no_init and not cls.instance:
            return None

        cls.instance = cls.get_instance(household_id)

        if no_init:
            return cls.instance

        if not cls.instance.zone_is_setup:
            cls.instance.setup_zone()
            cls.instance.persist_state()

        return cls.instance

    @classmethod
    def get_instance(cls, household_id):
        if cls.instance is not None:
            return cls.instance

        Logger.log("selection group: no instance, {}".format(household_id))

        # restore state
        try:
            file_handler = open(HOME_DIR + '/selection_group.json')
        except BaseException:
            file_handler = None

        if file_handler is None or not file_handler.readable():
            return cls(household_id)

        state = file_handler.read()
        file_handler.close()

        Logger.log('restored state: {}'.format(state))

        # deserialize
        instance = cls.deserialize(state)  # pylint: disable=no-member

        if instance.household_id != household_id:
            return cls(household_id)

        return instance

    @property
    def client(self):
        return services.get_first_client()

    def __init__(self, household_id, selectable_sims=None, zone_is_setup=None, household_npcs=None):  # pylint: disable=unused-argument
        self.household_id = household_id
        self.selectable_sims = selectable_sims
        self.household_npcs = household_npcs if household_npcs is not None else list()

        if self.selectable_sims is None or len(self.selectable_sims) == 0:
            self.update_selectable_sims()

        GameEvents.on_zone_teardown(self.on_zone_teardown)
        GameEvents.on_active_sim_changed(self.on_active_sim_changed)

    def persist_state(self):
        data = self.serialize()  # pylint: disable=no-member

        file_handler = open(path.join(HOME_DIR, 'selection_group.json'), 'w')
        file_handler.write(data)
        file_handler.close()

    def update_selectable_sims(self):
        selectable_sims = self.client.selectable_sims

        self.selectable_sims = [sim_info.id for sim_info in selectable_sims]

    def on_zone_teardown(self, _zone, _client):
        Logger.log('on_zone_teardown: tearing down SelectionGroupService')

        if not self.zone_is_setup:
            Logger.log("SelectionGroupService is already teared down")
            return

        self.persist_state()
        self.cleanup_sims()

        GameEvents.remove_zone_teardown(self.on_zone_teardown)

        self.zone_is_setup = False
        self.__class__.instance = None

    def make_sim_selectable(self, sim_info):
        if sim_info.is_selectable:
            return

        self.client.add_selectable_sim_info(sim_info)

        currently_active_sim = self.client.active_sim_info

        # force the game to update now selectable NPC tracker information
        self.client.set_active_sim_by_id(sim_info.id)
        self.client.set_active_sim_by_id(currently_active_sim.id)

    def remove_sim(self, sim_info):
        self.client.remove_selectable_sim_by_id(sim_info.id)

    def setup_zone(self):
        if len(self.household_npcs) > 0:
            self.client.send_selectable_sims_update()

        for sim_info_id in self.selectable_sims:
            try:
                sim_info = services.sim_info_manager().get(sim_info_id)

                self.make_sim_selectable(sim_info)
            except BaseException:
                Logger.log("Error while adding sim to skewer: {}".format(sim_info))
                Logger.log(traceback.format_exc())

        self.client.selectable_sims.add_watcher(self, self.update_selectable_sims)
        self.zone_is_setup = True

    def is_selectable(self, sim_id):
        test = sim_id in self.selectable_sims

        Logger.log("is sim {} in selectable list: {}".format(sim_id, test))

        return test

    def on_active_sim_changed(self, _old_sim, _new_sim):

        if self.client is None:
            Logger.log("active sim changed but we have no client, yet?")
            return

        sim_info = self.client.active_sim_info

        if sim_info is None:
            Logger.log("sim selection changed but no sim is selected")
            return

        if sim_info.household_id == self.household_id:
            return

        try:
            sim_info.request_lod(SimInfoLODLevel.ACTIVE)

            Logger.log("sim {} lod is now: {}".format(sim_info, sim_info.lod))

            sim_info.away_action_tracker.refresh(on_travel_away=True)
            sim_info.relationship_tracker.clean_and_send_remaining_relationship_info()
            sim_info.publish_all_commodities()

            sim_instance = sim_info.get_sim_instance(allow_hidden_flags=ALL_HIDDEN_REASONS)

            if sim_instance is not None:
                inventory = sim_instance.get_component(INVENTORY_COMPONENT)
                inventory.publish_inventory_items()
            else:
                Logger.log('there is no sim instance for {}'.format(sim_info))

        except BaseException:
            Logger.log("Error while updating newly active sim: {}".format(sim_info))
            Logger.log(traceback.format_exc())

    def cleanup_sims(self):
        for sim_info_id in self.selectable_sims:
            sim_info = services.sim_info_manager().get(sim_info_id)

            if sim_info.household_id == self.household_id:
                return

            Logger.log("{} is not in household, removing to avoid teardown issues".format(sim_info))

            self.remove_sim(sim_info)

    def add_household_npc(self, sim_info):
        self.household_npcs.append(sim_info.id)
        self.client.send_selectable_sims_update()

    def remove_household_npc(self, sim_info):
        self.household_npcs.remove(sim_info.id)
        self.client.send_selectable_sims_update()

    def is_household_npc(self, sim_info):
        return sim_info.id in self.household_npcs
