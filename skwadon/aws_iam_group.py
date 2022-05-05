import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as aws
import skwadon.aws_iam_policy as iam_policy

class GroupListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.iam_client = None

    def init_client(self):
        if self.iam_client == None:
            self.iam_client = self.session.client("iam")
            self.account_id = aws.fetch_account_id(self.session)

    def list(self):
        self.init_client()
        result = []
        res = self.iam_client.list_groups()
        while True:
            for elem in res["Groups"]:
                name = elem["GroupName"]
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_groups(Marker = res["Marker"])
        return result

    def child_handler(self, name):
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf", "inlinePolicies", "attachedPolicies"], {
                "conf": GroupConfHandler(self.iam_client, name),
                "inlinePolicies": GroupInlinePolicyListHandler(self.iam_client, name),
                "attachedPolicies": AttachedPolicyListHandler(self.iam_client, name, self.account_id),
            },
        )

class GroupConfHandler(common_action.ResourceHandler):
    properties = [
        "Path",
        "GroupId",
    ]

    def __init__(self, iam_client, name):
        self.iam_client = iam_client
        self.name = name

    def describe(self):
        try:
            res = self.iam_client.get_group(GroupName=self.name)
            curr_data = sic_lib.pickup(res["Group"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            else:
                raise

class GroupInlinePolicyListHandler(common_action.ListHandler):
    def __init__(self, iam_client, group_name):
        self.is_default_all = True
        self.iam_client = iam_client
        self.group_name = group_name

    def list(self):
        result = []
        res = self.iam_client.list_group_policies(GroupName = self.group_name)
        while True:
            for elem in res["PolicyNames"]:
                name = elem
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_group_policies(GroupName = self.role_name, Marker = res["Marker"])
        return result

    def child_handler(self, name):
        return GroupInlinePolicyHandler(self.iam_client, self.group_name, name)

class GroupInlinePolicyHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, group_name, policy_name):
        self.iam_client = iam_client
        self.group_name = group_name
        self.policy_name = policy_name

    def describe(self):
        try:
            res = self.iam_client.get_group_policy(GroupName = self.group_name, PolicyName = self.policy_name)
            return res["PolicyDocument"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            else:
                raise

class AttachedPolicyListHandler(common_action.ListHandler):
    def __init__(self, iam_client, group_name, account_id):
        self.iam_client = iam_client
        self.group_name = group_name
        self.account_id = account_id

    def list(self):
        result = []
        res = self.iam_client.list_attached_group_policies(GroupName=self.group_name)
        while True:
            for elem in res["AttachedPolicies"]:
                name = iam_policy.policy_arn_to_name(elem["PolicyArn"], self.account_id)
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_attached_group_policies(GroupName=self.group_name, Marker=res["Marker"])
        return result

