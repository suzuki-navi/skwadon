import copy
import json

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class DatabaseListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session

    def list(self):
        self.glue_client = self.session.client("glue")
        result = []
        res = self.glue_client.get_databases()
        while True:
            for elem in res['DatabaseList']:
                name = elem["Name"]
                result.append(name)
            if not "NextToken" in res:
                break
            res = self.glue_client.get_databases(NextToken = res["NextToken"])
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "conf": DatabaseConfHandler(self.glue_client, name),
            "tables": TableListHandler(self.glue_client, name),
        })

class DatabaseConfHandler(common_action.ResourceHandler):

    properties = [
        "Description",
        "LocationUri",
        "Parameters",
        "CreateTableDefaultPermissions",
        "TargetDatabase",
    ]

    def __init__(self, glue_client, database_name):
        self.glue_client = glue_client
        self.database_name = database_name

    def describe(self):
        res = self.glue_client.get_database(Name = self.database_name)
        curr_data = sic_lib.pickup(res["Database"], self.properties)
        return curr_data

class TableListHandler(common_action.ListHandler):
    def __init__(self, glue_client, database_name):
        self.glue_client = glue_client
        self.database_name = database_name

    def list(self):
        result = []
        res = self.glue_client.get_tables(DatabaseName = self.database_name)
        while True:
            for elem in res['TableList']:
                name = elem["Name"]
                result.append(name)
            if not "NextToken" in res:
                break
            res = self.glue_client.get_tables(DatabaseName = self.database_name, NextToken = res["NextToken"])
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "conf": TableConfHandler(self.glue_client, self.database_name, name),
            "columns": TableColumnsHandler(self.glue_client, self.database_name, name),
        })

class TableConfHandler(common_action.ResourceHandler):

    properties = [
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

    def __init__(self, glue_client, database_name, table_name):
        self.glue_client = glue_client
        self.database_name = database_name
        self.table_name = table_name

    def describe(self):
        res = self.glue_client.get_table(DatabaseName = self.database_name, Name = self.table_name)
        curr_data = sic_lib.pickup(res["Table"], self.properties)
        curr_data["StorageDescriptor"] = copy.copy(curr_data["StorageDescriptor"])
        sic_lib.removeKey(curr_data["StorageDescriptor"], "Columns")
        return curr_data

class TableColumnsHandler(common_action.ResourceHandler):
    def __init__(self, glue_client, database_name, table_name):
        self.glue_client = glue_client
        self.database_name = database_name
        self.table_name = table_name

    def describe(self):
        result = []
        res = self.glue_client.get_table(DatabaseName = self.database_name, Name = self.table_name)
        curr_data = {}
        for elem in res["Table"]["StorageDescriptor"]["Columns"]:
            name = elem["Name"]
            value = copy.copy(elem)
            del value["Name"]
            curr_data[name] = value
        return curr_data

