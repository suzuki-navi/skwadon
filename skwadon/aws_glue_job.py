import copy
import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

class JobListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.glue_client = None

    def init_client(self):
        if self.glue_client == None:
            self.glue_client = self.session.client("glue")

    def list(self):
        self.init_client()
        result = []
        res = self.glue_client.get_jobs()
        while True:
            for elem in res['Jobs']:
                name = elem["Name"]
                result.append(name)
            if not "NextToken" in res:
                break
            res = self.glue_client.get_jobs(NextToken = res["NextToken"])
        return result

    def child_handler(self, name):
        self.init_client()
        conf_handler = JobConfHandler(self.glue_client, name)
        return common_action.NamespaceHandler(
            "conf", ["conf", "source"], {
            "conf": conf_handler,
            "source": JobSourceHandler(self.session, conf_handler),
            "bookmark": JobBookmarkHandler(self.glue_client, name),
        })

class JobConfHandler(common_action.ResourceHandler):

    properties = [
        "Description",
        "Role",
        "ExecutionProperty",
        "Command",
        "DefaultArguments",
        "NonOverridableArguments",
        "Connections",
        "MaxRetries",
        "Timeout",
        "AllocatedCapacity",
        "MaxCapacity",
        "WorkerType",
        "NumberOfWorkers",
        "SecurityConfiguration",
        "NotificationProperty",
        "GlueVersion",
    ]

    def __init__(self, glue_client, job_name):
        self.glue_client = glue_client
        self.job_name = job_name

    def describe(self):
        try:
            res = self.glue_client.get_job(JobName = self.job_name)
            curr_data = sic_lib.pickup(res["Job"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise

    def create(self, confirmation_flag, src_data):
        update_data = sic_lib.pickup(src_data, self.properties)
        update_data["Name"] = self.job_name
        update_data = self._modify_data_for_put(update_data)
        sic_main.exec_put(confirmation_flag,
            f"glue_client.create_job(Name = {self.job_name}, ...)",
            lambda:
                self.glue_client.create_job(**update_data)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, self.properties)
        if update_data != None:
            update_data = self._modify_data_for_put(update_data)
            sic_main.exec_put(confirmation_flag,
                f"glue_client.update_job(JobName = {self.job_name}, ...)",
                lambda:
                    self.glue_client.update_job(JobName = self.job_name, JobUpdate = update_data)
            )

    def _modify_data_for_put(self, update_data):
        update_data = copy.copy(update_data)
        if "WorkerType" in update_data and update_data["WorkerType"] == "Standard":
            # MaxCapacity が必須で AllocatedCapacity の指定は不可
            sic_lib.removeKey(update_data, "AllocatedCapacity")
        elif "NumberOfWorkers" in update_data:
            sic_lib.removeKey(update_data, "AllocatedCapacity")
            sic_lib.removeKey(update_data, "MaxCapacity")
        else:
            sic_lib.removeKey(update_data, "AllocatedCapacity")
        return update_data

class JobSourceHandler(common_action.ResourceHandler):

    def __init__(self, session, conf_handler):
        self.session = session
        self.conf_handler = conf_handler

    def describe(self):
        conf = self.conf_handler.describe()
        if conf == None:
            return None
        script_s3_path = conf["Command"]["ScriptLocation"]
        script_source = self._fetch_script_source(script_s3_path)
        return script_source

    def create(self, confirmation_flag, src_data):
        if not confirmation_flag:
            # 新規作成時の --dry-run ではアップロード先が不明のため処理をスキップ
            return
        conf = self.conf_handler.describe()
        script_s3_path = conf["Command"]["ScriptLocation"]
        script_source = src_data
        self._put_script_source(confirmation_flag, script_s3_path, script_source)

    def update(self, confirmation_flag, src_data, curr_data):
        conf = self.conf_handler.describe()
        script_s3_path = conf["Command"]["ScriptLocation"]
        script_source = src_data
        self._put_script_source(confirmation_flag, script_s3_path, script_source)

    def _fetch_script_source(self, script_s3_path):
        script_source = sic_aws.fetch_s3_object(self.session, script_s3_path)
        if script_source == None:
            return ""
        script_source = sic_lib.normalize_script_source(script_source)
        return script_source

    def _put_script_source(self, confirmation_flag, script_s3_path, script_source):
        sic_aws.put_s3_object(confirmation_flag, self.session, script_s3_path, script_source)

class JobBookmarkHandler(common_action.ResourceHandler):

    properties = [
        "Version",
        "Run",
        "Attempt",
        "PreviousRunId",
        "RunId",
        "JobBookmark",
    ]

    def __init__(self, glue_client, job_name):
        self.glue_client = glue_client
        self.job_name = job_name

    def describe(self):
        try:
            res = self.glue_client.get_job_bookmark(JobName = self.job_name)
            curr_data = sic_lib.pickup(res["JobBookmarkEntry"], self.properties)
            if "JobBookmark" in curr_data:
                curr_data["JobBookmark"] = json.loads(curr_data["JobBookmark"])
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise
        return curr_data

