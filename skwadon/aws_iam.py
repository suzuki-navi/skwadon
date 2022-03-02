import json

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "iam.roles",
        lister = lambda names: list_roles(session),
    )
    common_action.set_handler(handler_map, "iam.roles.*role_name.conf",
        describer = lambda names: describe_role(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_role(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_role(session, src_data, curr_data, confirmation_flag, **names),
        deleter = lambda confirmation_flag, names: delete_role(session, confirmation_flag, **names)
    )
    common_action.set_handler(handler_map, "iam.roles.*role_name.inlinePolicies",
        lister = lambda names: list_inline_role_policies(session, **names),
    )
    common_action.set_handler(handler_map, "iam.roles.*role_name.inlinePolicies.*policy_name",
        describer = lambda names: describe_inline_role_policy(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_inline_role_policy(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_inline_role_policy(session, src_data, curr_data, confirmation_flag, **names),
        deleter = lambda confirmation_flag, names: delete_inline_role_policy(session, confirmation_flag, **names)
    )
    common_action.set_handler(handler_map, "iam.roles.*role_name.attachedPolicies",
        lister = lambda names: list_attached_role_policies(session, **names),
    )
    common_action.set_handler(handler_map, "iam.roles.*role_name.assumeRolePolicy",
        describer = lambda names: describe_assume_role_policy(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_assume_role_policy(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_assume_role_policy(session, src_data, curr_data, confirmation_flag, **names),
    )

####################################################################################################

def list_roles(session):
    iam_client = session.client("iam")
    result = []
    res = iam_client.list_roles()
    while True:
        for elem in res["Roles"]:
            name = elem["RoleName"]
            result.append(name)
        if not "Marker" in res:
            break
        res = iam_client.list_roles(Marker = res["Marker"])
    return result

####################################################################################################

def describe_role(session, role_name):
    iam_client = session.client("iam")
    res = iam_client.get_role(RoleName = role_name)
    curr_data = sic_lib.pickup(res["Role"], ["Description", "MaxSessionDuration"])
    return curr_data

def create_role(session, src_data, confirmation_flag, role_name):
    iam_client = session.client("iam")
    update_data = {}
    update_data["RoleName"] = role_name
    update_data["AssumeRolePolicyDocument"] = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ],
    })
    update_data["Description"] = src_data["Description"]
    update_data["MaxSessionDuration"] = src_data["MaxSessionDuration"]
    sic_main.add_update_message(f"iam_client.create_role(RoleName = {role_name}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        iam_client.create_role(**update_data)

def update_role(session, src_data, curr_data, confirmation_flag, role_name):
    iam_client = session.client("iam")
    update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, ["Description", "MaxSessionDuration"])
    if update_data != None:
        sic_main.add_update_message(f"iam_client.update_role(RoleName = {role_name}, ...)")
        if confirmation_flag and sic_main.global_confirmation_flag:
            update_data["RoleName"] = role_name
            iam_client.update_role(**update_data)

def delete_role(session, confirmation_flag, role_name):
    iam_client = session.client("iam")
    sic_main.add_update_message(f"iam_client.delete_role(RoleName = {role_name})")
    if confirmation_flag and sic_main.global_confirmation_flag:
        iam_client.delete_role(RoleName = role_name)

####################################################################################################

def list_inline_role_policies(session, role_name):
    iam_client = session.client("iam")
    result = []
    res = iam_client.list_role_policies(RoleName = role_name)
    while True:
        for elem in res["PolicyNames"]:
            name = elem
            result.append(name)
        if not "Marker" in res:
            break
        res = iam_client.list_role_policies(RoleName = role_name, Marker = res["Marker"])
    return result

####################################################################################################

def describe_inline_role_policy(session, role_name, policy_name):
    iam_client = session.client("iam")
    res = iam_client.get_role_policy(RoleName = role_name, PolicyName = policy_name)
    return res["PolicyDocument"]

def create_inline_role_policy(session, src_data, confirmation_flag, role_name, policy_name):
    put_inline_role_policy(session, src_data, confirmation_flag, role_name, policy_name)

def update_inline_role_policy(session, src_data, curr_data, confirmation_flag, role_name, policy_name):
    put_inline_role_policy(session, src_data, confirmation_flag, role_name, policy_name)

def put_inline_role_policy(session, src_data, confirmation_flag, role_name, policy_name):
    iam_client = session.client("iam")
    sic_main.add_update_message(f"iam_client.put_role_policy(RoleName = {role_name}, PolicyName = {policy_name}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        policy_document_json = json.dumps(src_data)
        iam_client.put_role_policy(RoleName = role_name, PolicyName = policy_name, PolicyDocument = policy_document_json)

def delete_inline_role_policy(session, confirmation_flag, role_name, policy_name):
    iam_client = session.client("iam")
    sic_main.add_update_message(f"iam_client.delete_role_policy(RoleName = {role_name}, PolicyName = {policy_name})")
    if confirmation_flag and sic_main.global_confirmation_flag:
        iam_client.delete_role_policy(RoleName = role_name, PolicyName = policy_name)

####################################################################################################

def list_attached_role_policies(session, role_name):
    iam_client = session.client("iam")
    result = []
    res = iam_client.list_attached_role_policies(RoleName = role_name)
    while True:
        for elem in res["AttachedPolicies"]:
            name = elem["PolicyName"]
            result.append(name)
        if not "Marker" in res:
            break
        res = iam_client.list_role_policies(RoleName = role_name, Marker = res["Marker"])
    return result

####################################################################################################

def describe_assume_role_policy(session, role_name):
    iam_client = session.client("iam")
    res = iam_client.get_role(RoleName = role_name)
    curr_data = sic_lib.dictlib_get(res, "Role.AssumeRolePolicyDocument")
    return curr_data

def create_assume_role_policy(session, src_data, confirmation_flag, role_name):
    put_assume_role_policy(session, src_data, confirmation_flag, role_name)

def update_assume_role_policy(session, src_data, curr_data, confirmation_flag, role_name):
    put_assume_role_policy(session, src_data, confirmation_flag, role_name)

def put_assume_role_policy(session, src_data, confirmation_flag, role_name):
    iam_client = session.client("iam")
    sic_main.add_update_message(f"iam_client.update_assume_role_policy(RoleName = {role_name}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        policy_document_json = json.dumps(src_data)
        iam_client.update_assume_role_policy(RoleName = role_name, PolicyDocument = policy_document_json)

####################################################################################################
