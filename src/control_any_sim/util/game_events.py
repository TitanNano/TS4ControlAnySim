"""Provides a global event bus with game events."""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Callable, ClassVar, TypeVar

import services
from server.client import Client
from sims.self_interactions import TravelInteraction
from sims.sim import Sim
from sims.sim_info import SimInfo
from zone import Zone
from zone_types import ZoneState

from control_any_sim import ts4_services
from control_any_sim.util.inject import inject_method_to
from control_any_sim.util.logger import Logger

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


class GameEvents:
    """Game event bus to listen to events in the game."""

    OnZoneTeardown: TypeAlias = Callable[[Zone, Client], None]
    OnZoneSpinUp: TypeAlias = Callable[[Zone, int, int], None]
    OnAddSim: TypeAlias = Callable[[Sim], None]
    OnLoadingScreenAnimationFinished: TypeAlias = Callable[[Zone], None]
    OnActiveSimChanged: TypeAlias = Callable[[Sim, Sim], None]
    OnTravelSimOut: TypeAlias = Callable[[SimInfo], None]
    OnPostSpawnSim: TypeAlias = Callable[[Sim], None]

    C = TypeVar("C", bound="GameEvents")

    zone_teardown_handlers: ClassVar[list[OnZoneTeardown]] = []
    zone_spin_up_handlers: ClassVar[list[OnZoneSpinUp]] = []
    add_sim_handlers: ClassVar[list[OnAddSim]] = []
    loading_screen_animation_finished_handlers: ClassVar[
        list[OnLoadingScreenAnimationFinished]
    ] = []
    travel_sim_out_handlers: ClassVar[list[OnTravelSimOut]] = []

    @classmethod
    def on_zone_teardown(cls: type[C], handler: OnZoneTeardown) -> None:
        """Add a listener for the zone_teardown event."""
        cls.zone_teardown_handlers.append(handler)

    @classmethod
    def remove_zone_teardown(cls: type[C], handler: OnZoneTeardown) -> None:
        """Remove a listener for the zone_teardown event."""
        if handler not in cls.zone_teardown_handlers:
            return

        cls.zone_teardown_handlers.remove(handler)

    @classmethod
    def emit_zone_teardown(cls: type[C], current_zone: Zone, client: Client) -> None:
        """Emit a zone teardown event."""
        Logger.log(
            f"registered zone teardown handlers: {len(cls.zone_teardown_handlers)}",
        )

        for handler in cls.zone_teardown_handlers:
            handler(current_zone, client)

    @classmethod
    def on_zone_spin_up(cls: type[C], handler: OnZoneSpinUp) -> None:
        """Add a listener for the zone_spin_up event."""
        cls.zone_spin_up_handlers.append(handler)

    @classmethod
    def emit_zone_spin_up(
        cls: type[C],
        current_zone: Zone,
        household_id: int,
        active_sim_id: int,
    ) -> None:
        """Emit a zone spin up event."""
        for handler in cls.zone_spin_up_handlers:
            handler(current_zone, household_id, active_sim_id)

    @classmethod
    def on_add_sim(cls: type[C], handler: OnAddSim) -> None:
        """Add a listener for the add_sim event."""
        cls.add_sim_handlers.append(handler)

    @classmethod
    def emit_add_sim(cls: type[C], sim: Sim) -> None:
        """Emit the add sim event."""
        for handler in cls.add_sim_handlers:
            handler(sim)

    @staticmethod
    def on_active_sim_changed(handler: OnActiveSimChanged) -> None:
        """Add a listener for the active_sim_changed event."""
        services.get_first_client().register_active_sim_changed(handler)

    @classmethod
    def on_loading_screen_animation_finished(
        cls: type[C],
        handler: OnLoadingScreenAnimationFinished,
    ) -> None:
        """Add a listener for the loading_screen_animation_finished event."""
        cls.loading_screen_animation_finished_handlers.append(handler)

    @classmethod
    def emit_loading_screen_animation_finished(
        cls: type[C],
        current_zone: Zone,
    ) -> None:
        """Emit the loading screen finished event."""
        for handler in cls.loading_screen_animation_finished_handlers:
            handler(current_zone)

    @classmethod
    def on_travel_sim_out(cls: type[C], handler: OnTravelSimOut) -> None:
        """Add a listener for the travel_sim_out event."""
        cls.travel_sim_out_handlers.append(handler)

    @classmethod
    def emit_travel_sim_out(cls: type[C], sim_info: SimInfo) -> None:
        """Emit the travel sim out event."""
        for handler in cls.travel_sim_out_handlers:
            handler(sim_info)

    @staticmethod
    def on_post_spawn_sim(handler: OnPostSpawnSim) -> None:
        """Adda listener for the post spawn sim event."""
        ts4_services.sim_spawner_service().register_sim_spawned_callback(handler)


@inject_method_to(Zone, "on_teardown")
def canys_zone_on_teardown(
    original: Callable[[Zone, Client], Any],
    self: Zone,
    client: Client,
) -> Any:  # noqa: ANN401
    """Wrap around the Zone::on_teardown method to emit the coresponding event."""
    try:
        Logger.log("Zone.on_teardown event occurred")
        GameEvents.emit_zone_teardown(self, client)
    except BaseException:
        Logger.error(traceback.format_exc())

    return original(self, client)


@inject_method_to(Zone, "do_zone_spin_up")
def canys_zone_do_zone_spin_up(
    original: Callable[[Zone, int, int], None],
    self: Zone,
    household_id: int,
    active_sim_id: int,
) -> None:
    """Wrap the Zone::do_zone_spin_up method to emit the corresponding event."""
    try:
        result = original(self, household_id, active_sim_id)

        def callback() -> None:
            try:
                Logger.log("zone_spin_up event occurred")
                GameEvents.emit_zone_spin_up(self, household_id, active_sim_id)
            except BaseException:
                Logger.error(traceback.format_exc())

        self.register_callback(ZoneState.RUNNING, callback)

        return result
    except BaseException:
        Logger.error(traceback.format_exc())


@inject_method_to(Sim, "on_add")
def canys_sim_on_add(original: Callable[[Sim], None], self: Sim) -> None:
    """Wrap the Sim::on_add method to emit the corresponding event."""
    try:
        Logger.log("Sim.on_add event occurred")
        result = original(self)

        GameEvents.emit_add_sim(self)

        return result
    except BaseException:
        Logger.error(traceback.format_exc())


@inject_method_to(Zone, "on_loading_screen_animation_finished")
def canys_zone_on_loading_screen_animation_finished(
    original: Callable[[Zone], None],
    self: Zone,
) -> None:
    """Wrap around Zone::on_loading_screen_animation_finished to emit corresponding event."""
    try:
        Logger.log("Zone.on_loading_screen_animation_finished event occurred")
        GameEvents.emit_loading_screen_animation_finished(self)
    except BaseException:
        Logger.error(traceback.format_exc())

    return original(self)


@inject_method_to(TravelInteraction, "save_and_destroy_sim")
def canys_travel_internaction_save_and_destroy_sim(
    original: Callable[[TravelInteraction, bool, SimInfo], None],
    self: TravelInteraction,
    on_reset: bool,  # noqa: FBT001
    sim_info: SimInfo,
) -> None:
    """Wrap the TravelInteraction::save_and_destroy_sim method to emit the corresponding event."""
    try:
        result = original(self, on_reset, sim_info)

        GameEvents.emit_travel_sim_out(sim_info)
    except Exception as err:
        Logger.error(f"{err}")
        Logger.error(traceback.format_exc())

    return result
