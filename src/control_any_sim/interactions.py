import traceback

import services  # pylint: disable=import-error

from interactions.base.immediate_interaction import ImmediateSuperInteraction  # pylint: disable=import-error,no-name-in-module

from singletons import DEFAULT  # pylint: disable=import-error
from event_testing.results import TestResult  # pylint: disable=import-error
from sims4.utils import flexmethod  # pylint: disable=import-error

from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.util.logger import Logger


class SimMakeSelectableInteraction(ImmediateSuperInteraction):
    # pylint: disable=too-few-public-methods

    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        try:
            inst_or_cls = inst if inst is not None else cls

            Logger.log("testing SimMakeSelectableInteraction, context: {} {}"
                       .format(args, kwargs))

            if target:
                info_target = target.sim_info

            Logger.log('info_target: {}'.format(info_target))

            if context is not None and context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log('info_target: {}'.format(info_target))

            sim_is_selectable = (SelectionGroupService
                                 .get(0).is_selectable(info_target.id))

            Logger.log("sim_is_selectable: {}".format(sim_is_selectable))

            if sim_is_selectable:
                fail = TestResult(False, "sim is already selectable", inst)
                Logger.log('fail result: {}'.format(repr(fail)))
                return fail

            if target is None or target.sim_info.id != info_target.id:
                return TestResult.TRUE

            return (super(SimMakeSelectableInteraction, inst_or_cls)
                    .test(*args, target=target, context=context, **kwargs))

        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self, timeline):
        Logger.log("running make selectable interaction...")
        try:
            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            SelectionGroupService \
                .get(services.active_household_id()) \
                .make_sim_selectable(sim_info)

            Logger.log("sim is now selectable!")

            services.get_first_client().set_active_sim_by_id(sim_info.id)

            Logger.log("sim is now active!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())


class SimMakeNotSelectableInteraction(ImmediateSuperInteraction):
    # pylint: disable=too-few-public-methods

    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        inst_or_cls = inst if inst is not None else cls

        Logger.log("testing SimMakeNotSelectableInteraction, context: {} {}"
                   .format(args, kwargs))

        if target:
            info_target = target.sim_info

        Logger.log('info_target: {}'.format(info_target))

        if context is not None and context.target_sim_id is not None:
            target_id = context.target_sim_id
            info_target = services.sim_info_manager().get(target_id)

        Logger.log('info_target: {}'.format(info_target))

        if cls.must_be_selectable(info_target):
            return TestResult(False, "sim is in active household and has to be selectable")

        sim_is_selectable = (SelectionGroupService
                             .get(0).is_selectable(info_target.id))

        Logger.log("sim_is_selectable: {}".format(sim_is_selectable))

        if not sim_is_selectable:
            return TestResult(False, "sim is not selectable", inst)

        if target is None or target.sim_info.id != info_target.id:
            return TestResult.TRUE

        return (super(SimMakeNotSelectableInteraction, inst_or_cls)
                .test(*args, target=target, context=context, **kwargs))

    def _run_interaction_gen(self, timeline):
        Logger.log("running make not selectable interaction...")
        try:
            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            SelectionGroupService \
                .get(services.active_household_id()) \
                .remove_sim(sim_info)

            Logger.log("sim is now not selectable anymore!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())

    @classmethod
    def must_be_selectable(cls, sim_info):
        return services.active_household_id() == sim_info.household_id


class SimAddRoomMateInteraction(ImmediateSuperInteraction):
    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        try:
            Logger.log("testing SimAddRoomMateInteraction, context: {} {}".format(args, kwargs))

            inst_or_cls = inst if inst is not None else cls
            roommate_service = services.get_roommate_service()
            household_id = context.sim.sim_info.household_id

            if roommate_service is None:
                return TestResult.NONE

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log('info_target: {}'.format(info_target))

            if context.sim.sim_info.id == info_target.id:
                return TestResult(False, "sim can not be it's own roommate", inst)

            if roommate_service.is_sim_info_roommate(info_target, household_id):
                return TestResult(False, "sim is already roommate of this household")

            return (super(SimAddRoomMateInteraction, inst_or_cls)
                    .test(*args, target=target, context=context, **kwargs))
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self, timeline):
        try:
            Logger.log("running turn into roommate interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info
            home_zone_id = self.get_sim_info_home_zone_id(self.context.sim.sim_info)

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            services.get_roommate_service().add_roommate(sim_info, home_zone_id)

            Logger.log("sim is now a roommate!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())

    @staticmethod
    def get_sim_info_home_zone_id(sim_info):
        if sim_info.household is None:
            return 0

        home_zone_id = sim_info.household.home_zone_id

        if not home_zone_id:
            return sim_info.roommate_zone_id

        return home_zone_id


class SimRemoveRoomMateInteraction(ImmediateSuperInteraction):
    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        try:
            inst_or_cls = inst if inst is not None else cls
            roommate_service = services.get_roommate_service()

            if roommate_service is None:
                return TestResult.NONE

            Logger.log("testing SimRemoveRoomMateInteraction, context: {} {}"
                       .format(args, kwargs))

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            household_id = context.sim.sim_info.household_id

            Logger.log('info_target: {}'.format(info_target))

            if context.sim.sim_info.id == info_target.id:
                return TestResult(False, "sim can not be it's own roommate", inst)

            if not roommate_service.is_sim_info_roommate(info_target, household_id):
                return TestResult(False, "sim is not a roommate of current household", inst)

            return (super(SimRemoveRoomMateInteraction, inst_or_cls)
                    .test(*args, target=target, context=context, **kwargs))
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self, timeline):
        try:
            Logger.log("running remove roommate interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            services.get_roommate_service().remove_roommate(sim_info)

            Logger.log("sim is now not a roommate anymore!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())


class SimHouseholdNpcOnInteraction(ImmediateSuperInteraction):
    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        try:
            inst_or_cls = inst if inst is not None else cls
            selection_group = SelectionGroupService.get(services.active_household_id())

            Logger.log("testing SimHouseholdNpcOnInteraction, context: {} {}"
                       .format(args, kwargs))

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log('info_target: {}'.format(info_target))

            if selection_group.is_household_npc(info_target):
                return TestResult(False, "sim is already a household npc", inst)

            if info_target.household_id != services.active_household_id():
                return TestResult(False, "sim is not a member of the active household", inst)

            return (super(SimHouseholdNpcOnInteraction, inst_or_cls)
                    .test(*args, target=target, context=context, **kwargs))
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self, timeline):
        try:
            Logger.log("running household npc on interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            selection_group = SelectionGroupService.get(services.active_household_id())
            selection_group.add_household_npc(sim_info)

            Logger.log("sim is now a household npc!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())


class SimHouseholdNpcOffInteraction(ImmediateSuperInteraction):
    @flexmethod
    def test(cls, inst, *args, target=DEFAULT, context=None, **kwargs) -> TestResult:  # pylint: disable=no-self-argument
        try:
            inst_or_cls = inst if inst is not None else cls
            selection_group = SelectionGroupService.get(services.active_household_id())

            Logger.log("testing SimHouseholdNpcOffInteraction, context: {} {}"
                       .format(args, kwargs))

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log('info_target: {}'.format(info_target))

            if not selection_group.is_household_npc(info_target):
                return TestResult(False, "sim is not a household npc", inst)

            if info_target.household_id != services.active_household_id():
                return TestResult(False, "sim is not a member of the active household", inst)

            return (super(SimHouseholdNpcOffInteraction, inst_or_cls)
                    .test(*args, target=target, context=context, **kwargs))
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self, timeline):
        try:
            Logger.log("running household npc off interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = (services.sim_info_manager()
                            .get(self.context.target_sim_id))

            Logger.log("got sim info {} {}"
                       .format(sim_info.first_name, sim_info.last_name))

            selection_group = SelectionGroupService.get(services.active_household_id())
            selection_group.remove_household_npc(sim_info)

            Logger.log("sim is now a normal household member!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
