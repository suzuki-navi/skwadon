import copy
import re
import sys

import boto3
import botocore.exceptions

import skwadon.main as sic_main
import skwadon.common_action as common_action
import skwadon.aws_iam_group        as aws_iam_group
import skwadon.aws_iam_role         as aws_iam_role
import skwadon.aws_iam_policy       as aws_iam_policy
import skwadon.aws_s3_bucket        as aws_s3_bucket
import skwadon.aws_stepfunctions    as aws_stepfunctions
import skwadon.aws_lambda           as aws_lambda
import skwadon.aws_glue_datacatalog as aws_glue_datacatalog
import skwadon.aws_glue_crawler     as aws_glue_crawler
import skwadon.aws_glue_job         as aws_glue_job
import skwadon.aws_glue_connection  as aws_glue_connection
import skwadon.aws_rds              as aws_rds
import skwadon.aws_redshift         as aws_redshift

def get_message_prefix(data):
    if "profile" in data:
        profile = data["profile"]
    else:
        profile = "default"
    ret = f"aws(proifle={profile}"
    if "region" in data:
        region = data["region"]
        ret = ret + f", region={region}"
    ret = ret + ")"
    return ret

def get_handler(src_data):
    session = create_aws_session(src_data)
    return common_action.NamespaceHandler(
        None, [], {
        "iam.groups": aws_iam_group.GroupListHandler(session),
        "iam.roles": aws_iam_role.RoleListHandler(session),
        "iam.policies": aws_iam_policy.PolicyListHandler(session),
        "s3.buckets": aws_s3_bucket.BucketListHandler(session),
        "lambda.functions": aws_lambda.FunctionListHandler(session),
        "stepFunctions.stateMachines": aws_stepfunctions.StateMachineListHandler(session),
        "glue.crawlers": aws_glue_crawler.CrawlerListHandler(session),
        "glue.databases": aws_glue_datacatalog.DatabaseListHandler(session),
        "glue.jobs": aws_glue_job.JobListHandler(session),
        "glue.connections": aws_glue_connection.ConnectionListHandler(session),
        "rds.instances": aws_rds.InstanceListHandler(session),
        "redshift.clusters": aws_redshift.ClusterListHandler(session),
    })

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

def fetch_account_id(session):
    account_id = session.client("sts").get_caller_identity()["Account"]
    return account_id

def fetch_region_name(session):
    region_name = session.region_name
    if region_name == None:
        raise Exception()
    return region_name

def fetch_s3_object(session, s3_path: str):
    if s3_path == None:
        return None
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

def put_s3_object(confirmation_flag, session, s3_path: str, body: str):
    if s3_path == None:
        return
    s3_client = session.client("s3")
    m = re.compile("\As3://([^/]+)/(.*)\Z").search(s3_path)
    if not m:
        return
    s3_bucket = m.group(1)
    s3_key = m.group(2)
    sic_main.exec_put(confirmation_flag,
        f"s3_client.put_object(Bucket = {s3_bucket}, Key = {s3_key}, ...)",
        lambda:
            s3_client.put_object(Bucket = s3_bucket, Key = s3_key, Body = body.encode('utf-8'))
    )
