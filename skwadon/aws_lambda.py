import copy
import shutil
import tempfile
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

class FunctionSourcesHandler(common_action.ResourceHandler):

    def __init__(self, lambda_client, function_name):
        self.lambda_client = lambda_client
        self.function_name = function_name

    def describe(self):
        res = self.lambda_client.get_function(FunctionName = self.function_name)
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

