# tracks debug info about direct go home interaction for NPCs
@inject_to(sims.self_interactions.GoHomeTravelInteraction, '__init__')
def tn_go_home_travel_interaction__init__(original, self, aop, context, to_zone_id=DEFAULT, **kwargs):
    Logger.log('intercepted GoHomeTravelInteraction')
    Logger.log('expected to_zone_id: {}'.format(to_zone_id))

    result = original(self, aop, context, to_zone_id=DEFAULT, **kwargs)

    Logger.log('selected to_zone_id: {}'.format(self.to_zone_id))
    Logger.log('selected from_zone_id: {}'.format(self.from_zone_id))

    return result

@inject_to(sims.sim_info.SimInfo, 'send_travel_switch_to_zone_op')
def tn_sim_info_send_travel_switch_to_zone_op(original, self, zone_id=DEFAULT):
    Logger.log('intercepted SimInfo.send_travel_switch_to_zone_op')
    Logger.log('name: {} {}'.format(self.first_name, self.last_name))
    Logger.log('zone_id: {}'.format(zone_id))
    Logger.log('self.zone_id: {}'.format(self.zone_id))
    Logger.log('self.world_id: {}'.format(self.world_id))
    Logger.log('self.household_id: {}'.format(self.household_id))
    Logger.log('active_household_id: {}'.format(services.active_household_id()))

    return original(self, zone_id)

@inject_to(sims.self_interactions.TravelInteraction, '__init__')
def tn_travel_interaction__init__(original, self, aop, context, **kwargs):

    result = original(self, aop, context, **kwargs)

    Logger.log('intercepted TravelInteraction')
    Logger.log('interaction: {}'.format(self))
    Logger.log('kwargs: {}'.format(kwargs))
    Logger.log('aop: {}'.format(aop))

    return result


@staticmethod
@inject_to(interactions.choices.ChoiceMenu, 'is_valid_aop')
def tn_choice_menu_is_valid_aop(original, aop, context, user_pick_target=None, result_override=DEFAULT, do_test=True):

    result = original(aop, context, user_pick_target, result_override, do_test)

    # Logger.log('intercepted ChoiceMenu.is_valid_aop')
    # Logger.log('result: {}'.format(repr(result)))
    # Logger.log('aop: {}'.format(aop))

    return result


@inject_to(TravelSwitchToZone, 'write')
def tn_travel_swtich_to_zone_write(original, self, msg):
    op = DistributorOps_pb2.TravelSwitchToZone()
    op.sim_to_visit_id = self.travel_info[0]
    op.household_to_control_id = self.travel_info[1]
    op.zone_id = self.travel_info[2]
    op.world_id = self.travel_info[3]

    Logger.log('intercepted TravelSwitchToZone.write')
    Logger.log('op.sim_to_visit_id: {}'.format(op.sim_to_visit_id))
    Logger.log('op.household_to_control_id {}'.format(op.household_to_control_id))
    Logger.log('op.zone_id {}'.format(op.zone_id))
    Logger.log('op.world_id {}'.format(op.world_id))
    Logger.log('msg: {}'.format(msg))

    self.serialize_op(msg, op, protocol_constants.TRAVEL_SWITCH_TO_ZONE)


@inject_to(ClientManager, 'create_client')
def tn_client_manager_create_client(original, self, client_id, account, household_id):
    Logger.log('intercepted ClientManager.create_client')
    Logger.log('client_id: {}'.format(client_id))
    Logger.log('account {}'.format(account))
    Logger.log('household_id {}'.format(household_id))

    return original(self, client_id, account, household_id)
