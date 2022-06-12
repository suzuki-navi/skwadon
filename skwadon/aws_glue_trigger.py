import copy

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class TriggerListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.glue_client = None

    def init_client(self):
        if self.glue_client is None:
            self.glue_client = self.session.client("glue")

    def list(self):
        self.init_client()
        result = []
        res = self.glue_client.get_triggers()
        while True:
            for elem in res['Triggers']:
                name = elem["Name"]
                result.append(name)
            if "NextToken" not in res:
                break
            res = self.glue_client.get_databases(NextToken=res["NextToken"])
        return result

    def child_handler(self, name):
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf", "status"], {
            "conf": TriggerConfHandler(self.glue_client, name),
            "status": TriggerStatusHandler(self.glue_client, name),
        })

class TriggerConfHandler(common_action.ResourceHandler):

    properties = [
        "Type",
        "Description",
        "Schedule",
        "Actions",
    ]
    properties_for_update = [
        "Description",
        "Schedule",
        "Actions",
    ]

    def __init__(self, glue_client, trigger_name):
        self.glue_client = glue_client
        self.trigger_name = trigger_name

    def describe(self):
        try:
            res = self.glue_client.get_trigger(Name = self.trigger_name)
            curr_data = sic_lib.pickup(res["Trigger"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise

    def create(self, confirmation_flag, src_data):
        update_data = copy.copy(src_data)
        update_data["Name"] = self.trigger_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.create_trigger({{Name: {self.trigger_name}, ...}})",
            lambda:
                self.glue_client.create_trigger(**update_data)
        )
        sic_main.exec_put(confirmation_flag,
            f"glue_client.start_trigger(Name={self.trigger_name})",
            lambda:
                self.glue_client.start_trigger(Name=self.trigger_name)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickup(src_data, self.properties_for_update)
        sic_main.exec_put(confirmation_flag,
            f"glue_client.update_trigger(Name={self.trigger_name}, TriggerUpdate={{...}})",
            lambda:
                self.glue_client.update_trigger(Name=self.trigger_name,
                TriggerUpdate=update_data)
        )

    def delete(self, confirmation_flag, curr_data):
        sic_main.exec_put(confirmation_flag,
            f"glue_client.delete_trigger(Name={self.trigger_name})",
            lambda:
                self.glue_client.delete_trigger(Name=self.trigger_name)
        )

class TriggerStatusHandler(common_action.ResourceHandler):

    properties = [
        "State",
    ]

    def __init__(self, glue_client, trigger_name):
        self.glue_client = glue_client
        self.trigger_name = trigger_name

    def describe(self):
        try:
            res = self.glue_client.get_trigger(Name = self.trigger_name)
            curr_data = sic_lib.pickup(res["Trigger"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise

    def delete(self, confirmation_flag, curr_data):
        pass

