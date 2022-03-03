import json

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "stepfunctions.stateMachines",
        lister = lambda names: list_statemachines(session),
    )
    common_action.set_handler(handler_map, "stepfunctions.stateMachines.*machine_name.conf",
        describer = lambda names: describe_statemachine(session, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_statemachine(session, src_data, curr_data, confirmation_flag, **names),
    )
    common_action.set_handler(handler_map, "stepfunctions.stateMachines.*machine_name.definition",
        describer = lambda names: describe_statemachine_definition(session, **names),
    )

####################################################################################################

def list_statemachines(session):
    stepfunctions_client = session.client("stepfunctions")
    account_id = sic_aws.fetch_account_id(session)
    region_name = sic_aws.fetch_region_name(session)
    result = []
    res = stepfunctions_client.list_state_machines()
    while True:
        for elem in res['stateMachines']:
            name = elem["name"]
            arn = calc_statemachine_arn(account_id, region_name, name)
            if elem["stateMachineArn"] == arn:
                result.append(name)
        if not "nextToken" in res:
            break
        res = stepfunctions_client.list_state_machines(nextToken = res["nextToken"])
    return result

####################################################################################################

statemachine_conf_properties = [
    "RoleArn",
    "Type",
    "LoggingConfiguration",
    "TracingConfiguration",
]
statemachine_conf_properties_for_update = [
    "RoleArn",
    "LoggingConfiguration",
    "TracingConfiguration",
]

def describe_statemachine(session, machine_name):
    stepfunctions_client = session.client("stepfunctions")
    account_id = sic_aws.fetch_account_id(session)
    region_name = sic_aws.fetch_region_name(session)
    arn = calc_statemachine_arn(account_id, region_name, machine_name)
    res = stepfunctions_client.describe_state_machine(stateMachineArn = arn)
    curr_data = sic_lib.dict_key_capitalize(res)
    curr_data = sic_lib.pickup(curr_data, statemachine_conf_properties)
    return curr_data

def update_statemachine(session, src_data, curr_data, confirmation_flag, machine_name):
    stepfunctions_client = session.client("stepfunctions")
    account_id = sic_aws.fetch_account_id(session)
    region_name = sic_aws.fetch_region_name(session)
    arn = calc_statemachine_arn(account_id, region_name, machine_name)

    update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, statemachine_conf_properties_for_update)
    if update_data != None:
        update_data = sic_lib.dict_key_to_lower(update_data)
        sic_main.add_update_message(f"stepfunctions_client.update_state_machine(stateMachineArn = {arn}, ...)")
        if confirmation_flag and sic_main.global_confirmation_flag:
            stepfunctions_client.update_state_machine(stateMachineArn = arn, **update_data)

def calc_statemachine_arn(account_id, region_name, machine_name):
    return f"arn:aws:states:{region_name}:{account_id}:stateMachine:{machine_name}"

####################################################################################################

def describe_statemachine_definition(session, machine_name):
    stepfunctions_client = session.client("stepfunctions")
    account_id = sic_aws.fetch_account_id(session)
    region_name = sic_aws.fetch_region_name(session)
    arn = calc_statemachine_arn(account_id, region_name, machine_name)
    res = stepfunctions_client.describe_state_machine(stateMachineArn = arn)
    return definition_str_to_dict(res["definition"])

def definition_str_to_dict(definition: str):
    return json.loads(definition)

def definition_dict_to_str(definition: dict):
    return json.dumps(definition)

####################################################################################################
