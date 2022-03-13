import json

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

class StateMachineListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session

    def list(self):
        self.stepfunctions_client = self.session.client("stepfunctions")
        account_id = sic_aws.fetch_account_id(self.session)
        region_name = sic_aws.fetch_region_name(self.session)
        result = []
        res = self.stepfunctions_client.list_state_machines()
        while True:
            for elem in res['stateMachines']:
                name = elem["name"]
                arn = calc_statemachine_arn2(account_id, region_name, name)
                if elem["stateMachineArn"] == arn:
                    result.append(name)
            if not "nextToken" in res:
                break
            res = self.stepfunctions_client.list_state_machines(nextToken = res["nextToken"])
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "conf": StateMachineConfHandler(self.session, self.stepfunctions_client, name),
            "definition": StateMachineDefinitionHandler(self.session, self.stepfunctions_client, name),
        })

class StateMachineBasicHandler(common_action.ResourceHandler):
    def __init__(self, session, stepfunctions_client, machine_name):
        self.session = session
        self.stepfunctions_client = stepfunctions_client
        self.machine_name = machine_name
        self.arn = None
        self.info = None

    def _describe(self):
        if self.info != None:
            return self.info
        if self.arn == None:
            arn = self._calc_statemachine_arn()
        res = self.stepfunctions_client.describe_state_machine(stateMachineArn = arn)
        curr_data = sic_lib.dict_key_capitalize(res)
        curr_data = sic_lib.pickup(curr_data, self._properties)
        self.info = curr_data
        return self.info

    def _update(self, confirmation_flag, src_data):
        curr_data = self._describe()
        update_data = {}
        dirty = False
        for key in self._properties_for_update:
            if key in src_data:
                update_data[key] = src_data[key]
                if update_data[key] != curr_data[key]:
                    dirty = True
            elif key in curr_data:
                update_data[key] = curr_data[key]
        if dirty:
            arn = self._calc_statemachine_arn()
            update_data = sic_lib.dict_key_to_lower(update_data)
            sic_main.exec_put(confirmation_flag,
                f"stepfunctions_client.update_state_machine(stateMachineArn = {arn}, ...)",
                lambda:
                    self.stepfunctions_client.update_state_machine(stateMachineArn = arn, **update_data)
            )
            self.info = None

    def _calc_statemachine_arn(self):
        return calc_statemachine_arn(self.session, self.machine_name)

    _properties = [
        "RoleArn",
        "Type",
        "LoggingConfiguration",
        "TracingConfiguration",
        "Definition"
    ]
    _properties_for_update = [
        "RoleArn",
        "LoggingConfiguration",
        "TracingConfiguration",
        "Definition"
    ]


class StateMachineConfHandler(StateMachineBasicHandler):
    def __init__(self, session, stepfunctions_client, machine_name):
        StateMachineBasicHandler.__init__(self, session, stepfunctions_client, machine_name)

    def describe(self):
        curr_data = sic_lib.pickup(self._describe(), self.properties)
        return curr_data

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, self.properties_for_update)
        if update_data != None:
            self._update(confirmation_flag, update_data)

    properties = [
        "RoleArn",
        "Type",
        "LoggingConfiguration",
        "TracingConfiguration",
    ]
    properties_for_update = [
        "RoleArn",
        "LoggingConfiguration",
        "TracingConfiguration",
    ]

class StateMachineDefinitionHandler(StateMachineBasicHandler):
    def __init__(self, session, stepfunctions_client, machine_name):
        StateMachineBasicHandler.__init__(self, session, stepfunctions_client, machine_name)

    def describe(self):
        info = self._describe()
        return self._definition_str_to_dict(info["Definition"])

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = {
            "Definition": self._definition_dict_to_str(src_data),
        }
        self._update(confirmation_flag, update_data)

    def _definition_str_to_dict(self, definition: str):
        return json.loads(definition)

    def _definition_dict_to_str(self, definition: dict):
        return json.dumps(definition)

def calc_statemachine_arn(session, machine_name):
    account_id = sic_aws.fetch_account_id(session)
    region_name = sic_aws.fetch_region_name(session)
    return calc_statemachine_arn2(account_id, region_name, machine_name)

def calc_statemachine_arn2(account_id, region_name, machine_name):
    return f"arn:aws:states:{region_name}:{account_id}:stateMachine:{machine_name}"
