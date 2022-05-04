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
                m = re.compile("\Aarn:aws:iam::([^:]*):policy/([^:]+)\Z").search(arn)
                if not m:
                    print(f"DEBUG {arn}")
                    continue
                if m.group(1) == self.account_id:
                    name = sic_lib.encode_key(m.group(2))
                elif m.group(1) == "aws":
                    name = sic_lib.encode_key("aws//" + m.group(2))
                else:
                    continue
                result.append(name)
            if not "Marker" in res:
                break
            res = self.iam_client.list_policies(Marker = res["Marker"])
        return result

    def child_handler(self, name):
        self.init_client()
        name = sic_lib.decode_key(name)
        if name.startswith("aws//"):
            arn = f"arn:aws:iam::aws:policy/{name[5:]}"
        else:
            arn = f"arn:aws:iam::{self.account_id}:policy/{name}"
        return common_action.NamespaceHandler(
            "conf", ["conf", "policy", "tag"], {
                "conf": PolicyConfHandler(self.iam_client, arn),
                "policy": PolicyDocumentHandler(self.iam_client, arn),
                "tags": PolicyTagsHandler(self.iam_client, arn),
            },
        )

class PolicyConfHandler(common_action.ResourceHandler):
    properties = [
        "Description",
        "PolicyId",
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

