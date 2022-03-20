import json

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class BucketListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.s3_client = None

    def init_client(self):
        if self.s3_client == None:
            self.s3_client = self.session.client("s3")

    def list(self):
        self.init_client()
        result = []
        res = self.s3_client.list_buckets()
        for elem in res['Buckets']:
            name = elem["Name"]
            result.append(name)
        return result

    def child_handler(self, name):
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf", "bucketPolicy"], {
            "conf": BucketConfHandler(self.s3_client, name),
            "bucketPolicy": BucketPolicyHandler(self.s3_client, name),
        })

class BucketConfHandler(common_action.ResourceHandler):

    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        curr_data = {}

        try:
            res = self.s3_client.get_bucket_location(Bucket = self.bucket_name)
            curr_data["location"] = res["LocationConstraint"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return None
            else:
                raise

        try:
            res = self.s3_client.get_bucket_policy_status(Bucket = self.bucket_name)
            curr_data["publicAccessBlock"] = not res["PolicyStatus"]["IsPublic"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                curr_data["publicAccessBlock"] = False
            else:
                raise

        return curr_data

class BucketPolicyHandler(common_action.ResourceHandler):
    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        try:
            res = self.s3_client.get_bucket_policy(Bucket = self.bucket_name)
            curr_data = json.loads(res["Policy"])
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                return None
