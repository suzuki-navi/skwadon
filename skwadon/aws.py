import copy
import re
import sys

import boto3
import botocore.exceptions

import skwadon.main as sic_main
import skwadon.common_action as common_action
import skwadon.aws_iam              as aws_iam
import skwadon.aws_glue_datacatalog as aws_glue_datacatalog
import skwadon.aws_glue_crawler     as aws_glue_crawler
import skwadon.aws_glue_job         as aws_glue_job
import skwadon.aws_redshift         as aws_redshift

def get_message_prefix(data):
    if "profile" in data:
        profile = data["profile"]
    else:
        profile = "default"
    ret = f"aws(proifle={profile}"
    if "region" in data:
        region = data["region"]
        ret = ret + ", region={region}"
    ret = ret + ")"
    return ret

def do_action(action, is_dryrun, path, src_data):
    session = create_aws_session(src_data)

    handler_map = {}
    modules = [
        aws_iam,
        aws_glue_datacatalog,
        aws_glue_crawler,
        aws_glue_job,
        aws_redshift,
    ]
    for m in modules:
        m.set_handler(handler_map, session)

    result = copy.copy(src_data)
    if "resources" in src_data:
        result["resources"] = common_action.do_action(handler_map, action, is_dryrun, path, src_data["resources"])

    return result

def create_aws_session(data):
    if "profile" in data:
        profile = data["profile"]
    else:
        profile = "default"
    if "region" in data:
        region = data["region"]
    else:
        region = None
    session = boto3.session.Session(profile_name = profile, region_name = region)
    return session

def fetch_s3_object(session, s3_path: str):
    if s3_path == None:
        return ""
    s3_client = session.client("s3")
    m = re.compile("\As3://([^/]+)/(.*)\Z").search(s3_path)
    if not m:
        return None
    s3_bucket = m.group(1)
    s3_key = m.group(2)
    try:
        res = s3_client.get_object(Bucket = s3_bucket, Key = s3_key)
        body = res['Body'].read()
        body_str = body.decode('utf-8')
        return body_str
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        else:
            raise

def put_s3_object(session, s3_path: str, body: str, confirmation_flag):
    if s3_path == None:
        return
    s3_client = session.client("s3")
    m = re.compile("\As3://([^/]+)/(.*)\Z").search(s3_path)
    if not m:
        return
    s3_bucket = m.group(1)
    s3_key = m.group(2)
    sic_main.add_update_message(f"s3_client.put_object(Bucket = {s3_bucket}, Key = {s3_key}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        res = s3_client.put_object(Bucket = s3_bucket, Key = s3_key, Body = body.encode('utf-8'))
