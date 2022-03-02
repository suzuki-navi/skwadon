import copy
import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "glue.databases",
        lister = lambda names: list_databases(session),
    )
    common_action.set_handler(handler_map, "glue.databases.*database_name.conf",
        describer = lambda names: describe_database(session, **names),
    )
    common_action.set_handler(handler_map, "glue.databases.*database_name.tables",
        lister = lambda names: list_tables(session, **names),
    )
    common_action.set_handler(handler_map, "glue.databases.*database_name.tables.*table_name.conf",
        describer = lambda names: describe_table(session, **names),
    )
    common_action.set_handler(handler_map, "glue.databases.*database_name.tables.*table_name.columns",
        describer = lambda names: describe_table_columns(session, **names),
    )

####################################################################################################

def list_databases(session):
    glue_client = session.client("glue")
    result = []
    res = glue_client.get_databases()
    while True:
        for elem in res['DatabaseList']:
            name = elem["Name"]
            result.append(name)
        if not "NextToken" in res:
            break
        res = glue_client.get_databases(NextToken = res["NextToken"])
    return result

####################################################################################################

database_conf_properties = [
    "Description",
    "LocationUri",
    "Parameters",
    "CreateTableDefaultPermissions",
    "TargetDatabase",
]

def describe_database(session, database_name):
    glue_client = session.client("glue")
    res = glue_client.get_database(Name = database_name)
    curr_data = sic_lib.pickup(res["Database"], database_conf_properties)
    return curr_data

####################################################################################################

def list_tables(session, database_name):
    glue_client = session.client("glue")
    result = []
    res = glue_client.get_tables(DatabaseName = database_name)
    while True:
        for elem in res['TableList']:
            name = elem["Name"]
            result.append(name)
        if not "NextToken" in res:
            break
        res = glue_client.get_tables(DatabaseName = database_name, NextToken = res["NextToken"])
    return result

####################################################################################################

table_conf_properties = [
    "Description",
    "Owner",
    "Retention",
    "StorageDescriptor",
    "PartitionKeys",
    "ViewOriginalText",
    "ViewExpandedText",
    "TableType",
    "Parameters",
    "TargetTable",
    "VersionId",
]

def describe_table(session, database_name, table_name):
    glue_client = session.client("glue")
    res = glue_client.get_table(DatabaseName = database_name, Name = table_name)
    curr_data = sic_lib.pickup(res["Table"], table_conf_properties)
    curr_data["StorageDescriptor"] = copy.copy(curr_data["StorageDescriptor"])
    sic_lib.removeKey(curr_data["StorageDescriptor"], "Columns")
    return curr_data

def describe_table_columns(session, database_name, table_name):
    glue_client = session.client("glue")
    res = glue_client.get_table(DatabaseName = database_name, Name = table_name)
    curr_data = {}
    for elem in res["Table"]["StorageDescriptor"]["Columns"]:
        name = elem["Name"]
        value = copy.copy(elem)
        del value["Name"]
        curr_data[name] = value
    return curr_data

####################################################################################################
