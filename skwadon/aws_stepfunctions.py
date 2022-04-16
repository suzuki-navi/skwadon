import json

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

class StateMachineListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.stepfunctions_client = None

    def init_client(self):
        if self.stepfunctions_client == None:
            self.stepfunctions_client = self.session.client("stepfunctions")

    def list(self):
        self.init_client()
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
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf", "definition"], {
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
        if self.arn != None:
            return self.info
        if self.arn == None:
            arn = self._calc_statemachine_arn()
        try:
            res = self.stepfunctions_client.describe_state_machine(stateMachineArn = arn)
            curr_data = sic_lib.dict_key_capitalize(res)
            curr_data = sic_lib.pickup(curr_data, self._properties)
            self.info = curr_data
            return self.info
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "StateMachineDoesNotExist":
                return None
            else:
                raise

    def _create(self, confirmation_flag, src_data):
        update_data = {}
        update_data["Name"] = self.machine_name
        update_data["Definition"] = self._defaultDefinition()
        for key in self._properties_for_create:
            if key in src_data:
                update_data[key] = src_data[key]
        update_data = sic_lib.dict_key_to_lower(update_data)
        sic_main.exec_put(confirmation_flag,
            f"stepfunctions_client.create_state_machine(name = {self.machine_name}, ...)",
            lambda:
                self.stepfunctions_client.create_state_machine(**update_data)
        )
        if confirmation_flag:
            self.info = None

    def _update(self, confirmation_flag, src_data):
        curr_data = self._describe()
        if curr_data is None:
            curr_data = {}
        update_data = {}
        dirty = False
        for key in self._properties_for_update:
            if key in src_data:
                update_data[key] = src_data[key]
                if key not in curr_data or update_data[key] != curr_data[key]:
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
            if confirmation_flag:
                self.info = None

    def _calc_statemachine_arn(self):
        return calc_statemachine_arn(self.session, self.machine_name)

    def _defaultDefinition(self):
        return json.dumps({
            "StartAt": "__skwadon_dummy",
            "States": {
                "__skwadon_dummy": {
                    "Type": "Pass",
                    "End": True,
                },
            },
        })

    _properties = [
        "RoleArn",
        "Type",
        "LoggingConfiguration",
        "TracingConfiguration",
        "Definition"
    ]
    _properties_for_create = [
        "RoleArn",
        "Type",
        "LoggingConfiguration",
        "TracingConfiguration",
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
        info = self._describe()
        if info == None:
            return None
        curr_data = sic_lib.pickup(info, self.properties)
        return curr_data

    def create(self, confirmation_flag, src_data):
        self._create(confirmation_flag, src_data)

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
        if info == None:
            return None
        result = self._definition_str_to_dict(info["Definition"])
        if "__skwadon_dummy" in result["States"]:
            del result["States"]["__skwadon_dummy"]
        return result

    def put(self, confirmation_flag, src_data):
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
