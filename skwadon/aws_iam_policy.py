import json
import re

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as aws

class PolicyListHandler(common_action.ListHandler):
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
        res = self.iam_client.list_policies()
        while True:
            for elem in res["Policies"]:
                arn = elem["Arn"]
                name = policy_arn_to_name(arn, self.account_id)
                if name is None:
                    continue
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_policies(Marker = res["Marker"])
        return result

    def child_handler(self, name):
        self.init_client()
        arn = policy_name_to_arn(name, self.account_id)
        return common_action.NamespaceHandler(
            "conf", ["conf", "policy", "tag"], {
                "conf": PolicyConfHandler(self.iam_client, arn),
                "policy": PolicyDocumentHandler(self.iam_client, arn),
                "tags": PolicyTagsHandler(self.iam_client, arn),
            },
        )

def policy_arn_to_name(arn, account_id):
    m = re.compile("\Aarn:aws:iam::([^:]*):policy/([^:]+)\Z").search(arn)
    if not m:
        return None
    if m.group(1) == account_id:
        return sic_lib.encode_key(m.group(2))
    elif m.group(1) == "aws":
        return sic_lib.encode_key("aws//" + m.group(2))
    else:
        return None

def policy_name_to_arn(name, account_id):
    name = sic_lib.decode_key(name)
    if name.startswith("aws//"):
        return f"arn:aws:iam::aws:policy/{name[5:]}"
    else:
        return f"arn:aws:iam::{account_id}:policy/{name}"

class PolicyConfHandler(common_action.ResourceHandler):
    properties = [
        "Path",
        "PolicyId",
        "Description",
        "IsAttachable",
    ]

    def __init__(self, iam_client, arn):
        self.iam_client = iam_client
        self.arn = arn

    def describe(self):
        try:
            res = self.iam_client.get_policy(PolicyArn=self.arn)
            curr_data = sic_lib.pickup(res["Policy"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            else:
                raise

class PolicyDocumentHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, arn):
        self.iam_client = iam_client
        self.arn = arn

    def describe(self):
        try:
            res = self.iam_client.get_policy(PolicyArn=self.arn)
            version_id = res["Policy"]["DefaultVersionId"]
            res = self.iam_client.get_policy_version(PolicyArn=self.arn, VersionId=version_id)
            return res["PolicyVersion"]["Document"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            else:
                raise

class PolicyTagsHandler(common_action.ResourceHandler):
    def __init__(self, iam_client, arn):
        self.iam_client = iam_client
        self.arn = arn

    def describe(self):
        try:
            res = self.iam_client.get_policy(PolicyArn=self.arn)
            return sic_lib.decode_tags(res["Policy"]["Tags"])
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                return None
            else:
                raise

