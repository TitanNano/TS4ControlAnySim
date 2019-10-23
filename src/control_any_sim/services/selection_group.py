from os import path
import traceback

import services  # pylint: disable=import-error

from control_any_sim.util.serialize import serialize
from control_any_sim.util.game_events import GameEvents
from control_any_sim.util.logger import Logger
from sims.sim_info_lod import SimInfoLODLevel  # pylint: disable=import-error


def get_home_dir():
    dir_name = path.dirname(path.abspath(__file__))
    home_dir = path.normpath(path.join(dir_name, '../../../'))

    return home_dir


HOME_DIR = get_home_dir()


@serialize
class SelectionGroupService:

    instance = None
    zone_is_setup = False

    @classmethod
    def get(cls, household_id):
        Logger.log('get selection group instance')

        cls.instance = cls.get_instance(household_id)

        if not cls.instance.zone_is_setup:
            cls.instance.setup_zone()
            cls.instance.persist_state()

        return cls.instance

    @classmethod
    def get_instance(cls, household_id):
        Logger.log('class instance exists {}'.format(cls.instance is not None))

        if cls.instance is not None:
            return cls.instance

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
        return services.client_manager().get_client_by_household_id(self.household_id)

    def __init__(self, household_id, selectable_sims=None, zone_is_setup=None):  # pylint: disable=unused-argument
        self.household_id = household_id
        self.selectable_sims = selectable_sims

        if self.selectable_sims is None:
            self.update_selectable_sims()

        GameEvents.on_zone_teardown(self.on_zone_teardown)

    def persist_state(self):
        data = self.serialize()  # pylint: disable=no-member

        file_handler = open(path.join(HOME_DIR, 'selection_group.json'), 'w')
        file_handler.write(data)
        file_handler.close()

    def update_selectable_sims(self):
        selectable_sims = self.client.selectable_sims

        self.selectable_sims = [sim_info.id for sim_info in selectable_sims]

    def on_zone_teardown(self, _zone, _client):
        Logger.log('on_zone_teardown')

        # client.selectable_sims.remove_watcher(self)
        self.persist_state()
        self.zone_is_setup = False
        self.__class__.instance = None

    def make_sim_selectable(self, sim_info):
        if sim_info.is_selectable:
            return

        self.client.add_selectable_sim_info(sim_info)

        currently_active_sim = self.client.active_sim_info

        self.client.set_active_sim_by_id(sim_info.id)
        sim_info.request_lod(SimInfoLODLevel.ACTIVE)

        Logger.log("sim {} lod is now: {}".format(sim_info, sim_info.lod))

        sim_info.away_action_tracker.refresh(on_travel_away=True)

        for rel in sim_info.relationship_tracker:
            rel_sim_info = rel.get_other_sim_info(sim_info.id)

            Logger.log("{} has relationship: {}".format(sim_info, rel_sim_info))
            Logger.log("{} has lod: {}".format(rel_sim_info, rel_sim_info.lod))

        self.client.set_active_sim_by_id(currently_active_sim.id)

    def remove_sim(self, sim_info):
        self.client.remove_selectable_sim_by_id(sim_info.id)

    def setup_zone(self):
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
