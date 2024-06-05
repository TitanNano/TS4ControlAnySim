"""New cheat commands introduced by this mod."""

import traceback

import services  # pylint: disable=import-error
from sims4 import commands  # pylint: disable=import-error

import control_any_sim
from control_any_sim.services.selection_group import SelectionGroupService
from control_any_sim.util.logger import Logger


@commands.Command("canys.make_selectable", command_type=(commands.CommandType.Live))
def set_active_sim(
    first_name: str = "",
    last_name: str = "",
    _connection: commands.Output = None,
) -> bool:
    """Add a sim to the selection group."""
    output = commands.CheatOutput(_connection)

    try:
        if _connection is None:
            output("SetActiveSim; Status:ParamError")
            return False

        tgt_client = services.client_manager().get(_connection)

        if tgt_client is None:
            output("SetActiveSim; Status:ClientError no client")
            return False

        sim_info = services.sim_info_manager().get_sim_info_by_name(
            first_name,
            last_name,
        )

        if sim_info is None:
            output("SetActiveSim; Status:SimError no sim with this name found")
            return False

        SelectionGroupService.get(services.active_household_id()).make_sim_selectable(
            sim_info,
        )

        if tgt_client.set_active_sim_by_id(sim_info.id):
            output("SetActiveSim; Status:Success")
            return True

        output("SetActiveSim; Status:NoChange")
        return True
    except BaseException as exception:
        output(f"Error: {exception}")
        Logger.log(traceback.format_exc())
        return False


@commands.Command("canys.selectable_sims", command_type=(commands.CommandType.Live))
def get_selectable_sims(_connection: commands.Output = None) -> bool:
    """List all selectable sims."""
    output = commands.CheatOutput(_connection)
    tgt_client = services.client_manager().get(_connection)

    for sim_info in tgt_client.selectable_sims:
        output(
            f"sim {sim_info.first_name} {sim_info.last_name} is selectable",
        )
    return True


@commands.Command("canys.sim_info", command_type=(commands.CommandType.Live))
def log_sim_info(_connection: commands.Output = None) -> bool:
    """Print detailed sim info."""
    output = commands.CheatOutput(_connection)
    tgt_client = services.client_manager().get(_connection)
    sim_info = tgt_client.active_sim_info

    sim_info.log_sim_info(output)
    output(f"commodity_tracker: {sim_info.commodity_tracker}")
    output(
        f"commodity_tracker_lod: {sim_info.commodity_tracker.simulation_level}",
    )
    output(f"is npc: {sim_info.is_npc}")
    output(f"is_selected: {sim_info.is_selected}")
    output(f"is_selectable: {sim_info.is_selectable}")
    output(
        f"can away actions: {sim_info.away_action_tracker.is_sim_info_valid_to_run_away_actions()}",
    )
    return True


@commands.Command("canys.version", command_type=(commands.CommandType.Live))
def canys_get_version_command(_connection: commands.Output = None) -> bool:
    """Print the loaded version of ControlAnySim."""
    output = commands.CheatOutput(_connection)
    version = control_any_sim.__version__

    output(f"you are currently running version {version} of Control Any Sim")
    return True
