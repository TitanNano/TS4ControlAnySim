import traceback

import zone  # pylint: disable=import-error
import sims  # pylint: disable=import-error
import services  # pylint: disable=import-error

from zone_types import ZoneState  # pylint: disable=import-error

from control_any_sim.util.inject import inject_method_to
from control_any_sim.util.logger import Logger


class GameEvents:
    zone_teardown_handlers = list()
    zone_spin_up_handlers = list()
    add_sim_handlers = list()
    loading_screen_animation_finished_handlers = list()

    @classmethod
    def on_zone_teardown(cls, handler):
        cls.zone_teardown_handlers.append(handler)

    @classmethod
    def remove_zone_teardown(cls, handler):
        if handler not in cls.zone_teardown_handlers:
            return

        cls.zone_teardown_handlers.remove(handler)

    @classmethod
    def emit_zone_teardown(cls, current_zone, client):
        Logger.log(
            "registered zone teardown handlers: {}".format(
                len(cls.zone_teardown_handlers)
            )
        )

        for handler in cls.zone_teardown_handlers:
            handler(current_zone, client)

    @classmethod
    def on_zone_spin_up(cls, handler):
        cls.zone_spin_up_handlers.append(handler)

    @classmethod
    def emit_zone_spin_up(cls, current_zone, household_id, active_sim_id):
        for handler in cls.zone_spin_up_handlers:
            handler(current_zone, household_id, active_sim_id)

    @classmethod
    def on_add_sim(cls, handler):
        cls.add_sim_handlers.append(handler)

    @classmethod
    def emit_add_sim(cls, sim):
        for handler in cls.add_sim_handlers:
            handler(sim)

    @classmethod
    def on_active_sim_changed(cls, handler):
        services.get_first_client().register_active_sim_changed(handler)

    @classmethod
    def on_loading_screen_animation_finished(cls, handler):
        cls.loading_screen_animation_finished_handlers.append(handler)

    @classmethod
    def emit_loading_screen_animation_finished(cls, current_zone):
        for handler in cls.loading_screen_animation_finished_handlers:
            handler(current_zone)


@inject_method_to(zone.Zone, "on_teardown")
def canys_zone_on_teardown(original, self, client):
    try:
        Logger.log("Zone.on_teardown event occurred")
        GameEvents.emit_zone_teardown(self, client)
    except BaseException:
        Logger.error(traceback.format_exc())

    return original(self, client)


@inject_method_to(zone.Zone, "do_zone_spin_up")
def canys_zone_do_zone_spin_up(original, self, household_id, active_sim_id):
    try:
        result = original(self, household_id, active_sim_id)

        def callback():
            try:
                Logger.log("zone_spin_up event occurred")
                GameEvents.emit_zone_spin_up(self, household_id, active_sim_id)
            except BaseException:
                Logger.error(traceback.format_exc())

        self.register_callback(ZoneState.RUNNING, callback)

        return result
    except BaseException:
        Logger.error(traceback.format_exc())


@inject_method_to(sims.sim.Sim, "on_add")
def canys_sim_on_add(original, self):
    try:
        Logger.log("Sim.on_add event occurred")
        result = original(self)

        GameEvents.emit_add_sim(self)

        return result
    except BaseException:
        Logger.error(traceback.format_exc())


@inject_method_to(zone.Zone, "on_loading_screen_animation_finished")
def canys_zone_on_loading_screen_animation_finished(original, self):
    try:
        Logger.log("Zone.on_loading_screen_animation_finished event occurred")
        GameEvents.emit_loading_screen_animation_finished(self)
    except BaseException:
        Logger.error(traceback.format_exc())

    return original(self)
