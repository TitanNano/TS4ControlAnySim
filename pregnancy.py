import operator
import services

from sims4.math import Threshold
from sims4 import commands
from sims.pregnancy.pregnancy_tracker import PregnancyTracker


def is_pregnant_sim(sim_info):
    return sim_info.is_pregnant


def get_pregnancy_state(sim_info):
    pregnancy_commodity_type = PregnancyTracker.PREGNANCY_COMMODITY_MAP.get(sim_info.species)
    tracker = sim_info.get_tracker(pregnancy_commodity_type)
    pregnancy_commodity = tracker.get_statistic(pregnancy_commodity_type, add=True)
    pregnancy_commodity.add_statistic_modifier(PregnancyTracker.PREGNANCY_RATE)
    current_pregnancy = pregnancy_commodity.get_value()
    max_pregnancy = pregnancy_commodity.max_value

    return current_pregnancy, max_pregnancy


def is_pregnancy_complete(sim_info):
    current, max = get_pregnancy_state(sim_info)
    threshold = Threshold(max, operator.ge)

    return threshold.compare(current)


def get_currently_pregnant_sims():
    info_manager = services.sim_info_manager()

    all_sims = info_manager.get_all()
    pregnant_sims = []

    for sim_info in all_sims:
        if not sim_info.is_pregnant:
            continue

        pregnant_sims.append(sim_info)

    return pregnant_sims


@commands.Command('tn_force_deliver', command_type=commands.CommandType.Live)
def force_deliver(_connection=None):
    output = commands.CheatOutput(_connection)

    try:
        pregnant_sims = get_currently_pregnant_sims()
        output('currently pregnant sims {}'.format(len(pregnant_sims)))

        for sim_info in pregnant_sims:
            is_ready = is_pregnancy_complete(sim_info)

            if not is_ready:
                continue

            sim_info.pregnancy_tracker._create_and_name_offspring()
            sim_info.pregnancy_tracker._show_npc_dialog()
            sim_info.pregnancy_tracker.clear_pregnancy()

            output("sim {} {} has force delivered".format(sim_info.first_name, sim_info.last_name))

    except BaseException as e:
        output('Error: {}'.format(e))


@commands.Command('tn_get_info', command_type=commands.CommandType.Live)
def get_info(_connection=None):
    output = commands.CheatOutput(_connection)

    try:
        pregnant_sims = get_currently_pregnant_sims()
        output('currently pregnant sims {}'.format(len(pregnant_sims)))

        for sim_info in pregnant_sims:
            current, max = get_pregnancy_state(sim_info)

            output("sim {} {} is pregnant: {} / {}".format(sim_info.first_name, sim_info.last_name, current, max))

    except BaseException as e:
        output('Error: {}'.format(e))
