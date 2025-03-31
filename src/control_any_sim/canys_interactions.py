"""New interactions added by the mod."""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, TypeVar

import services
from event_testing.results import TestResult
from interactions.base.immediate_interaction import ImmediateSuperInteraction
from sims4.utils import flexmethod
from singletons import DEFAULT

from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.util.logger import Logger

if TYPE_CHECKING:
    from interactions.context import InteractionContext
    from scheduling import Timeline
    from sims.sim_info import SimInfo
    from typing_extensions import Self


class SimMakeSelectableInteraction(ImmediateSuperInteraction):
    """New sim interaction to add a sim to the selection group."""

    C = TypeVar("C", bound="SimMakeSelectableInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if interaction is available."""
        try:
            inst_or_cls = inst if inst is not None else cls

            Logger.log(
                f"testing SimMakeSelectableInteraction, context: {args} {kwargs}",
            )

            if target:
                info_target = target.sim_info

            Logger.log(f"info_target: {info_target}")

            if context is not None and context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log(f"info_target: {info_target}")

            sim_is_selectable = SelectionGroupService.get(0).is_selectable(
                info_target.id,
            )

            Logger.log(f"sim_is_selectable: {sim_is_selectable}")

            if sim_is_selectable:
                fail = TestResult(False, "sim is already selectable", inst)  # noqa: FBT003
                Logger.log(f"fail result: {fail!r}")
                return fail

            if target is None or target.sim_info.id != info_target.id:
                return TestResult.TRUE

            return super(SimMakeSelectableInteraction, inst_or_cls).test(
                *args,
                target=target,
                context=context,
                **kwargs,
            )

        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        Logger.log("running make selectable interaction...")
        try:
            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            SelectionGroupService.get(
                services.active_household_id(),
            ).make_sim_selectable(sim_info)

            Logger.log("sim is now selectable!")

            services.get_first_client().set_active_sim_by_id(sim_info.id)

            Logger.log("sim is now active!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False


class SimMakeNotSelectableInteraction(ImmediateSuperInteraction):
    """New sim interaction to remove a sim from the interaction group."""

    C = TypeVar("C", bound="SimMakeNotSelectableInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if interaction is available for this sim."""
        inst_or_cls = inst if inst is not None else cls

        Logger.log(
            f"testing SimMakeNotSelectableInteraction, context: {args} {kwargs}",
        )

        if target:
            info_target = target.sim_info

        Logger.log(f"info_target: {info_target}")

        if context is not None and context.target_sim_id is not None:
            target_id = context.target_sim_id
            info_target = services.sim_info_manager().get(target_id)

        Logger.log(f"info_target: {info_target}")

        if cls._must_be_selectable(info_target):
            return TestResult(
                False,  # noqa: FBT003
                "sim is in active household and has to be selectable",
            )

        sim_is_selectable = SelectionGroupService.get(0).is_selectable(info_target.id)

        Logger.log(f"sim_is_selectable: {sim_is_selectable}")

        if not sim_is_selectable:
            return TestResult(False, "sim is not selectable", inst)  # noqa: FBT003

        if target is None or target.sim_info.id != info_target.id:
            return TestResult.TRUE

        return super(SimMakeNotSelectableInteraction, inst_or_cls).test(
            *args,
            target=target,
            context=context,
            **kwargs,
        )

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        Logger.log("running make not selectable interaction...")
        try:
            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            service: SelectionGroupService = SelectionGroupService.get(
                services.active_household_id(),
            )

            service.remove_sim(
                sim_info,
            )

            Logger.log("sim is now not selectable anymore!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False

    @classmethod
    def _must_be_selectable(cls, sim_info: SimInfo) -> bool:
        return services.active_household_id() == sim_info.household_id


class SimAddRoomMateInteraction(ImmediateSuperInteraction):
    """New sim interaction to quickly add them as roommates."""

    C = TypeVar("C", bound="SimAddRoomMateInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: InteractionContext,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if the sim can be added as a roommate."""
        try:
            Logger.log(
                f"testing SimAddRoomMateInteraction, context: {args} {kwargs}",
            )

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

            Logger.log(f"info_target: {info_target}")

            if context.sim.sim_info.id == info_target.id:
                return TestResult(False, "sim can not be it's own roommate", inst)  # noqa: FBT003

            if roommate_service.is_sim_info_roommate(info_target, household_id):
                return TestResult(False, "sim is already roommate of this household")  # noqa: FBT003

            return super(SimAddRoomMateInteraction, inst_or_cls).test(
                *args,
                target=target,
                context=context,
                **kwargs,
            )
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        try:
            Logger.log("running turn into roommate interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info
            home_zone_id = self.get_sim_info_home_zone_id(self.context.sim.sim_info)

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            services.get_roommate_service().add_roommate(sim_info, home_zone_id)

            Logger.log("sim is now a roommate!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False

    @staticmethod
    def _get_sim_info_home_zone_id(sim_info: SimInfo) -> int:
        if sim_info.household is None:
            return 0

        home_zone_id = sim_info.household.home_zone_id

        if not home_zone_id:
            return sim_info.roommate_zone_id

        return home_zone_id


class SimRemoveRoomMateInteraction(ImmediateSuperInteraction):
    """New sim interaction to quickly remove roommates from the household."""

    C = TypeVar("C", bound="SimRemoveRoomMateInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: InteractionContext,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if the sim can be removed from the household roommates."""
        try:
            inst_or_cls = inst if inst is not None else cls
            roommate_service = services.get_roommate_service()

            if roommate_service is None:
                return TestResult.NONE

            Logger.log(
                f"testing SimRemoveRoomMateInteraction, context: {args} {kwargs}",
            )

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            household_id = context.sim.sim_info.household_id

            Logger.log(f"info_target: {info_target}")

            if context.sim.sim_info.id == info_target.id:
                return TestResult(False, "sim can not be it's own roommate", inst)  # noqa: FBT003

            if not roommate_service.is_sim_info_roommate(info_target, household_id):
                return TestResult(
                    False,  # noqa: FBT003
                    "sim is not a roommate of current household",
                    inst,
                )

            return super(SimRemoveRoomMateInteraction, inst_or_cls).test(
                *args,
                target=target,
                context=context,
                **kwargs,
            )
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        try:
            Logger.log("running remove roommate interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            services.get_roommate_service().remove_roommate(sim_info)

            Logger.log("sim is now not a roommate anymore!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False


class SimHouseholdNpcOnInteraction(ImmediateSuperInteraction):
    """New sim interaction to turn household members into autonomus NPCs."""

    C = TypeVar("C", bound="SimHouseholdNpcOnInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: InteractionContext = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if sim can be turned into a household NPC."""
        try:
            inst_or_cls = inst if inst is not None else cls
            selection_group = SelectionGroupService.get(services.active_household_id())

            Logger.log(
                f"testing SimHouseholdNpcOnInteraction, context: {args} {kwargs}",
            )

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log(f"info_target: {info_target}")

            if selection_group.is_household_npc(info_target):
                return TestResult(False, "sim is already a household npc", inst)  # noqa: FBT003

            if info_target.household_id != services.active_household_id():
                return TestResult(
                    False,  # noqa: FBT003
                    "sim is not a member of the active household",
                    inst,
                )

            return super(SimHouseholdNpcOnInteraction, inst_or_cls).test(
                *args,
                target=target,
                context=context,
                **kwargs,
            )
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        try:
            Logger.log("running household npc on interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            selection_group = SelectionGroupService.get(services.active_household_id())
            selection_group.add_household_npc(sim_info)

            Logger.log("sim is now a household npc!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False


class SimHouseholdNpcOffInteraction(ImmediateSuperInteraction):
    """New sim interaction to remove a household member from the NPC list."""

    C = TypeVar("C", bound="SimHouseholdNpcOffInteraction")

    @flexmethod
    def test(
        cls: type[C],  # noqa: N805
        inst: C,
        *args: Any,  # noqa: ANN401
        target: DEFAULT = DEFAULT,
        context: InteractionContext,
        **kwargs: Any,  # noqa: ANN401
    ) -> TestResult:
        """Test if the sim is a household NPC and can be removed."""
        try:
            inst_or_cls = inst if inst is not None else cls
            selection_group = SelectionGroupService.get(services.active_household_id())

            Logger.log(
                f"testing SimHouseholdNpcOffInteraction, context: {args} {kwargs}",
            )

            if target:
                info_target = target.sim_info

            if context.target_sim_id is not None:
                target_id = context.target_sim_id
                info_target = services.sim_info_manager().get(target_id)

            Logger.log(f"info_target: {info_target}")

            if not selection_group.is_household_npc(info_target):
                return TestResult(False, "sim is not a household npc", inst)  # noqa: FBT003

            if info_target.household_id != services.active_household_id():
                return TestResult(
                    False,  # noqa: FBT003
                    "sim is not a member of the active household",
                    inst,
                )

            return super(SimHouseholdNpcOffInteraction, inst_or_cls).test(
                *args,
                target=target,
                context=context,
                **kwargs,
            )
        except BaseException:
            Logger.log(traceback.format_exc())

    def _run_interaction_gen(self: Self, timeline: Timeline) -> bool:
        try:
            Logger.log("running household npc off interaction...")

            super()._run_interaction_gen(timeline)

            sim_info = self.target.sim_info

            if self.context.target_sim_id is not None:
                sim_info = services.sim_info_manager().get(self.context.target_sim_id)

            Logger.log(
                f"got sim info {sim_info.first_name} {sim_info.last_name}",
            )

            selection_group = SelectionGroupService.get(services.active_household_id())
            selection_group.remove_household_npc(sim_info)

            Logger.log("sim is now a normal household member!")

            return True

        except BaseException:
            Logger.log(traceback.format_exc())
            return False
