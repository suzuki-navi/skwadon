import copy
import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "glue.jobs",
        lister = lambda names: list_jobs(session),
    )
    common_action.set_handler(handler_map, "glue.jobs.*job_name.conf",
        describer = lambda names: describe_job(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_job(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_job(session, src_data, curr_data, confirmation_flag, **names),
    )
    common_action.set_handler(handler_map, "glue.jobs.*job_name.source",
        describer = lambda names: describe_source(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_source(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_source(session, src_data, curr_data, confirmation_flag, **names),
    )
    common_action.set_handler(handler_map, "glue.jobs.*job_name.bookmark",
        describer = lambda names: describe_bookmark(session, **names),
    )

####################################################################################################

def list_jobs(session):
    glue_client = session.client("glue")
    result = []
    res = glue_client.get_jobs()
    while True:
        for elem in res['Jobs']:
            name = elem["Name"]
            result.append(name)
        if not "NextToken" in res:
            break
        res = glue_client.get_jobs(NextToken = res["NextToken"])
    return result

####################################################################################################

job_conf_properties = [
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

def describe_job(session, job_name):
    glue_client = session.client("glue")
    res = glue_client.get_job(JobName = job_name)
    curr_data = sic_lib.pickup(res["Job"], job_conf_properties)
    return curr_data

def create_job(session, src_data, confirmation_flag, job_name):
    glue_client = session.client("glue")
    update_data = sic_lib.pickup(src_data, job_conf_properties)
    update_data["Name"] = job_name
    update_data = modify_data_for_put(update_data)
    sic_main.add_update_message(f"glue_client.create_job(Name = {job_name}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        glue_client.create_job(**update_data)

def update_job(session, src_data, curr_data, confirmation_flag, job_name):
    glue_client = session.client("glue")
    update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, job_conf_properties)
    if update_data != None:
        update_data = modify_data_for_put(update_data)
        sic_main.add_update_message(f"glue_client.update_job(JobName = {job_name}, ...)")
        if confirmation_flag and sic_main.global_confirmation_flag:
            glue_client.update_job(JobName = job_name, JobUpdate = update_data)

def modify_data_for_put(update_data):
    update_data = copy.copy(update_data)
    if update_data["WorkerType"] == "Standard":
        # MaxCapacity が必須で AllocatedCapacity の指定は不可
        sic_lib.removeKey(update_data, "AllocatedCapacity")
    elif "NumberOfWorkers" in update_data:
        sic_lib.removeKey(update_data, "AllocatedCapacity")
        sic_lib.removeKey(update_data, "MaxCapacity")
    else:
        sic_lib.removeKey(update_data, "AllocatedCapacity")
    return update_data

####################################################################################################

def describe_source(session, job_name):
    conf = describe_job(session, job_name)
    script_s3_path = conf["Command"]["ScriptLocation"]
    script_source = fetch_script_source(session, script_s3_path)
    return script_source

def create_source(session, src_data, confirmation_flag, job_name):
    if not confirmation_flag:
        # 新規作成時の --dry-run ではアップロード先が不明のため処理をスキップ
        return
    conf = describe_job(session, job_name)
    script_s3_path = conf["Command"]["ScriptLocation"]
    script_source = src_data
    put_script_source(session, script_s3_path, script_source, confirmation_flag)

def update_source(session, src_data, curr_data, confirmation_flag, job_name):
    conf = describe_job(session, job_name)
    script_s3_path = conf["Command"]["ScriptLocation"]
    script_source = src_data
    put_script_source(session, script_s3_path, script_source, confirmation_flag)

def fetch_script_source(session, script_s3_path):
    script_source = sic_aws.fetch_s3_object(session, script_s3_path)
    if script_source == None:
        return ""
    script_source = sic_lib.normalize_script_source(script_source)
    return script_source

def put_script_source(session, script_s3_path, script_source, confirmation_flag):
    sic_aws.put_s3_object(session, script_s3_path, script_source, confirmation_flag)

####################################################################################################

job_bookmark_properties = [
    "Version",
    "Run",
    "Attempt",
    "PreviousRunId",
    "RunId",
    "JobBookmark",
]

def describe_bookmark(session, job_name):
    glue_client = session.client("glue")
    try:
        res = glue_client.get_job_bookmark(JobName = job_name)
        curr_data = sic_lib.pickup(res["JobBookmarkEntry"], job_bookmark_properties)
        if "JobBookmark" in curr_data:
            curr_data["JobBookmark"] = json.loads(curr_data["JobBookmark"])
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "EntityNotFoundException":
            return None
    return curr_data

####################################################################################################
