import json

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class BucketListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session

    def list(self):
        self.s3_client = self.session.client("s3")
        result = []
        res = self.s3_client.list_buckets()
        for elem in res['Buckets']:
            name = elem["Name"]
            result.append(name)
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "location": LocationHandler(self.s3_client, name),
            "bucketPolicy": BucketPolicyHandler(self.s3_client, name),
            "publicAccessBlock": PublicAccessBlockHandler(self.s3_client, name),
        })

class LocationHandler(common_action.ResourceHandler):
    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        res = self.s3_client.get_bucket_location(Bucket = self.bucket_name)
        curr_data = res["LocationConstraint"]
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

class PublicAccessBlockHandler(common_action.ResourceHandler):
    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        try:
            res = self.s3_client.get_bucket_policy_status(Bucket = self.bucket_name)
            curr_data = not res["PolicyStatus"]["IsPublic"]
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                return False

