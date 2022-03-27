import copy
import shutil
import tempfile
import time
import urllib.request

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

class FunctionListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.lambda_client = None

    def init_client(self):
        if self.lambda_client == None:
            self.lambda_client = self.session.client("lambda")

    def list(self):
        self.init_client()
        result = []
        res = self.lambda_client.list_functions()
        while True:
            for elem in res['Functions']:
                name = elem["FunctionName"]
                result.append(name)
            if not "NextMarker" in res:
                break
            res = self.lambda_client.list_functions(NextMarker = res["NextMarker"])
        return result

    def child_handler(self, name):
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf", "sources"], {
            "conf": FunctionConfHandler(self.lambda_client, name),
            "sources": FunctionSourcesHandler(self.lambda_client, name),
        })

class FunctionConfHandler(common_action.ResourceHandler):

    properties = [
        'Runtime',
        'Role',
        'Handler',
        'Description',
        'Timeout',
        'MemorySize',
        'VpcConfig',
        'DeadLetterConfig',
        'Environment',
        'KMSKeyArn',
        'TracingConfig',
        'MasterArn',
        'Layers',
        'FileSystemConfigs',
        'PackageType',
        'ImageConfigResponse',
        'Architectures',
    ]

    def __init__(self, lambda_client, function_name):
        self.lambda_client = lambda_client
        self.function_name = function_name

    def describe(self):
        try:
            res = self.lambda_client.get_function(FunctionName = self.function_name)
            curr_data = sic_lib.pickup(res["Configuration"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return None
            else:
                raise

    def create(self, confirmation_flag, src_data):
        update_data = src_data.copy()
        update_data["FunctionName"] = self.function_name
        update_data["Code"] = {"ZipFile": create_zip({"__skwadon_dummy.txt": "dummy"})}
        sic_main.exec_put(confirmation_flag,
            f"lambda_client.create_function(FunctionName = {self.function_name}, ...)",
            lambda: self.lambda_client.create_function(**update_data)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = src_data.copy()
        update_data["FunctionName"] = self.function_name
        sic_lib.removeKey(update_data, "PackageType")
        sic_lib.removeKey(update_data, "Architectures")
        sic_main.exec_put(confirmation_flag,
            f"lambda_client.update_function_configuration(FunctionName = {self.function_name}, ...)",
            lambda: self.lambda_client.update_function_configuration(**update_data)
        )


class FunctionSourcesHandler(common_action.ResourceHandler):

    def __init__(self, lambda_client, function_name):
        self.lambda_client = lambda_client
        self.function_name = function_name

    def describe(self):
        try:
            res = self.lambda_client.get_function(FunctionName = self.function_name)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return None
            else:
                raise
        result = {}
        if res["Configuration"]["PackageType"] == "Zip" and res["Code"]["RepositoryType"] == "S3":
            url = res["Code"]["Location"]
            with tempfile.TemporaryDirectory() as tmp_dir:
                with tempfile.NamedTemporaryFile() as tmp_file:
                    with urllib.request.urlopen(url) as response:
                        shutil.copyfileobj(response, tmp_file)
                    tmp_file.flush()
                    shutil.unpack_archive(tmp_file.name, tmp_dir, "zip")
                result = sic_lib.script_sources_to_yaml(tmp_dir)
        return result

    def put(self, confirmation_flag, src_data):
        if confirmation_flag:
            self.waitPending()
        src_data2 = src_data.copy()
        if "__skwadon_dummy.txt" in src_data2:
            del src_data2["__skwadon_dummy.txt"]
        zipbin = create_zip(src_data2)
        update_data = {}
        update_data["FunctionName"] = self.function_name
        update_data["ZipFile"] = zipbin
        sic_main.exec_put(confirmation_flag,
            f"lambda_client.update_function_code(FunctionName = {self.function_name}, ...)",
            lambda: self.lambda_client.update_function_code(**update_data)
        )

    def waitPending(self):
        while True:
            res = self.lambda_client.get_function(FunctionName = self.function_name)
            if res["Configuration"]["State"] == "Pending":
                time.sleep(1)
            else:
                break

def create_zip(sources):
    with tempfile.TemporaryDirectory() as tmp_dir:
        sic_lib.script_sources_from_yaml(tmp_dir, sources)
        with tempfile.TemporaryDirectory() as tmp_dir2:
            shutil.make_archive(tmp_dir2 + "/sources", "zip", tmp_dir)
            with open(tmp_dir2 + "/sources.zip", "rb") as fh:
                zipbin = fh.read()
    return zipbin

