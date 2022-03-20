
import yaml

import skwadon.main as sic_main
import skwadon.common_action as common_action

def get_message_prefix(data):
    return "testcloud"

def get_handler(src_data):
    return common_action.NamespaceHandler(
        None, [], {
        "seeds": SeedListHandler(),
    })

class SeedListHandler(common_action.ListHandler):

    _items = [
        "himawari1",
        "himawari2",
        "himawari3",
    ]

    def list(self):
        return self._items

    def child_handler(self, name):
        exists = name in self._items
        return common_action.NamespaceHandler(
            "conf", ["conf"], {
            "conf": SeedConfHandler(name, exists),
            "status": SeedStatusHandler(name, exists),
        })

class SeedConfHandler(common_action.ResourceHandler):
    def __init__(self, name, exists):
        self.name = name
        self.exists = exists

    def describe(self):
        if not self.exists:
            return None
        return {
            "Description": f"himawari no tane '{self.name}'",
            "Count": 10,
            "Color": {
                "r": 30,
                "g": 20,
                "b": 15,
            },
        }

    def create(self, confirmation_flag, src_data):
        print(f"TESTCLOUD: create conf, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"src_data": src_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: create conf",
            lambda:
                print("TESTCLOUD: execute create conf"),
        )

    def update(self, confirmation_flag, src_data, curr_data):
        print(f"TESTCLOUD: update conf, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"src_data": src_data, "curr_data": curr_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: update conf",
            lambda:
                print("TESTCLOUD: execute update conf"),
        )

    def delete(self, confirmation_flag, curr_data):
        print(f"TESTCLOUD: delete, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"curr_data": curr_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: delete conf",
            lambda:
                print("TESTCLOUD: execute delete conf"),
        )

class SeedStatusHandler(common_action.ResourceHandler):
    def __init__(self, name, exists):
        self.name = name
        self.exists = exists

    def describe(self):
        if not self.exists:
            return None
        return {
            "status": "OK",
        }

    def create(self, confirmation_flag, src_data):
        print(f"TESTCLOUD: create status, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"src_data": src_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: create status",
            lambda:
                print("TESTCLOUD: execute create status"),
        )

    def update(self, confirmation_flag, src_data, curr_data):
        print(f"TESTCLOUD: update status, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"src_data": src_data, "curr_data": curr_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: update status",
            lambda:
                print("TESTCLOUD: execute update status"),
        )

    def delete(self, confirmation_flag, curr_data):
        print(f"TESTCLOUD: delete status, confirmation_flag = {confirmation_flag}")
        sic_main.save_yaml({"curr_data": curr_data}, None)
        sic_main.exec_put(
            confirmation_flag,
            "api: delete status",
            lambda:
                print("TESTCLOUD: execute delete status"),
        )

