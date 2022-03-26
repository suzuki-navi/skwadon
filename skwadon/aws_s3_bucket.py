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
        if self.s3_client is None:
            self.s3_client = self.session.client("s3")
            self.s3_resource = self.session.resource("s3")

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
            "conf", ["conf", "bucketPolicy", "lifecycles"],
            {
                "conf": BucketConfHandler(self.s3_client, name),
                "bucketPolicy": BucketPolicyHandler(self.s3_client, name),
                "lifecycles": BucketLifecyclesHandler(self.s3_client, name),
            },
        )


class BucketConfHandler(common_action.ResourceHandler):

    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        curr_data = {}

        try:
            res = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            curr_data["location"] = res["LocationConstraint"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                return None
            elif e.response["Error"]["Code"] == "AccessDenied":
                return {"*": "AccessDenied"}
            else:
                raise

        try:
            res = self.s3_client.get_bucket_policy_status(Bucket=self.bucket_name)
            curr_data["publicAccessBlock"] = not res["PolicyStatus"]["IsPublic"]
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                curr_data["publicAccessBlock"] = False
            elif e.response["Error"]["Code"] == "AccessDenied":
                return {"*": "AccessDenied"}
            else:
                raise

        return curr_data


class BucketPolicyHandler(common_action.ResourceHandler):
    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        try:
            res = self.s3_client.get_bucket_policy(Bucket=self.bucket_name)
            curr_data = json.loads(res["Policy"])
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                return None
            raise


class BucketLifecyclesHandler(common_action.ResourceHandler):
    def __init__(self, s3_client, bucket_name):
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    def describe(self):
        try:
            res = self.s3_client.get_bucket_lifecycle_configuration(Bucket=self.bucket_name)
            result = self._encode(res["Rules"])
            return result
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                return {}
            elif e.response["Error"]["Code"] == "AccessDenied":
                return {"*": "AccessDenied"}
            raise

    def put(self, confirmation_flag, src_data):
        update_data = {"Rules": self._decode(src_data)}
        if len(update_data["Rules"]) == 0:
            sic_main.exec_put(
                confirmation_flag,
                f"s3_client.delete_bucket_lifecycle(Bucket={self.bucket_name})",
                lambda:
                    self.s3_client.delete_bucket_lifecycle(Bucket=self.bucket_name)
            )
        else:
            sic_main.exec_put(
                confirmation_flag,
                f"s3_client.put_bucket_lifecycle_configuration(Bucket={self.bucket_name}, LifecycleConfiguration=...)",
                lambda:
                    self.s3_client.put_bucket_lifecycle_configuration(Bucket=self.bucket_name, LifecycleConfiguration=update_data)
            )

    def delete(self, confirmation_flag, curr_data):
        self.put(confirmation_flag, None)

    def _encode(self, info):
        result = {}
        for elem in info:
            elem2 = elem.copy()
            name = sic_lib.encode_key(elem["ID"])
            del elem2["ID"]
            if "Prefix" not in elem2:
                elem2["Prefix"] = ""
            result[name] = elem2
        return result

    def _decode(self, info):
        if info is None:
            return []
        result = []
        for name, elem in info.items():
            elem2 = elem.copy()
            elem2["ID"] = sic_lib.decode_key(name)

            # putのときは Prefix が必須

            result.append(elem2)
        return result


