import json

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class RoleListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session

    def list(self):
        self.iam_client = self.session.client("iam")
        result = []
        res = self.iam_client.list_roles()
        while True:
            for elem in res["Roles"]:
                name = elem["RoleName"]
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_roles(Marker = res["Marker"])
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "conf": RoleConfHandler(self.iam_client, name),
            "inlinePolicies": RoleInlinePolicyListHandler(self.iam_client, name),
            "attachedPolicies": AttachedPolicyListHandler(self.iam_client, name),
            "assumeRolePolicy": AssumeRolePolicyHandler(self.iam_client, name),
        })

class RoleConfHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, role_name):
        self.iam_client = iam_client
        self.role_name = role_name

    def describe(self):
        res = self.iam_client.get_role(RoleName = self.role_name)
        curr_data = sic_lib.pickup(res["Role"], ["Description", "MaxSessionDuration"])
        return curr_data

    def create(self, confirmation_flag, src_data):
        update_data = {}
        update_data["RoleName"] = self.role_name
        update_data["AssumeRolePolicyDocument"] = json.dumps(self._defaultAssumeRole())
        update_data["Description"] = src_data["Description"]
        update_data["MaxSessionDuration"] = src_data["MaxSessionDuration"]
        sic_main.exec_put(confirmation_flag,
            f"iam_client.create_role(RoleName = {self.role_name}, ...)",
            lambda: self.iam_client.create_role(**update_data)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, ["Description", "MaxSessionDuration"])
        if update_data != None:
            update_data["RoleName"] = self.role_name
            sic_main.exec_put(confirmation_flag,
                f"iam_client.update_role(RoleName = {self.role_name}, ...)",
                lambda:
                    self.iam_client.update_role(**update_data)
            )

    def delete(self, confirmation_flag, curr_data):
        sic_main.exec_put(confirmation_flag,
            f"iam_client.delete_role(RoleName = {self.role_name})",
            lambda:
                self.iam_client.delete_role(RoleName = self.role_name)
        )

    def _defaultAssumeRole(self):
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ],
        }

class RoleInlinePolicyListHandler(common_action.ListHandler):
    def __init__(self, iam_client, role_name):
        self.iam_client = iam_client
        self.role_name = role_name

    def list(self):
        result = []
        res = self.iam_client.list_role_policies(RoleName = self.role_name)
        while True:
            for elem in res["PolicyNames"]:
                name = elem
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_role_policies(RoleName = self.role_name, Marker = res["Marker"])
        return result

    def child_handler(self, name):
        return RoleInlinePolicyHandler(self.iam_client, self.role_name, name)

class RoleInlinePolicyHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, role_name, policy_name):
        self.iam_client = iam_client
        self.role_name = role_name
        self.policy_name = policy_name

    def describe(self):
        res = self.iam_client.get_role_policy(RoleName = self.role_name, PolicyName = self.policy_name)
        return res["PolicyDocument"]

    def put(self, confirmation_flag, src_data):
        policy_document_json = json.dumps(src_data)
        sic_main.exec_put(confirmation_flag,
            f"iam_client.put_role_policy(RoleName = {self.role_name}, PolicyName = {self.policy_name}, ...)",
            lambda:
                self.iam_client.put_role_policy(RoleName = self.role_name, PolicyName = self.policy_name, PolicyDocument = policy_document_json)
        )

    def delete(self, confirmation_flag, curr_data):
        sic_main.exec_put(confirmation_flag,
            f"iam_client.delete_role_policy(RoleName = {self.role_name}, PolicyName = {self.policy_name})",
            lambda:
                self.iam_client.delete_role_policy(RoleName = self.role_name, PolicyName = self.policy_name)
        )

class AttachedPolicyListHandler(common_action.ListHandler):
    def __init__(self, iam_client, role_name):
        self.iam_client = iam_client
        self.role_name = role_name

    def list(self):
        result = []
        res = self.iam_client.list_attached_role_policies(RoleName = self.role_name)
        while True:
            for elem in res["AttachedPolicies"]:
                name = elem["PolicyName"]
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_role_policies(RoleName = self.role_name, Marker = res["Marker"])
        return result

class AssumeRolePolicyHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, role_name):
        self.iam_client = iam_client
        self.role_name = role_name

    def describe(self):
        res = self.iam_client.get_role(RoleName = self.role_name)
        curr_data = sic_lib.dictlib_get(res, "Role.AssumeRolePolicyDocument")
        return curr_data

    def put(self, confirmation_flag, src_data):
        policy_document_json = json.dumps(src_data)
        sic_main.exec_put(confirmation_flag,
            f"iam_client.update_assume_role_policy(RoleName = {self.role_name}, ...)",
            lambda:
                self.iam_client.update_assume_role_policy(RoleName = self.role_name, PolicyDocument = policy_document_json)
        )

    def delete(self, confirmation_flag, curr_data):
        pass
