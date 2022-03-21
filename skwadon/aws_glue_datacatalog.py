import copy
import json

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class DatabaseListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.glue_client = None

    def init_client(self):
        if self.glue_client == None:
            self.glue_client = self.session.client("glue")

    def list(self):
        self.init_client()
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
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf"], {
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
        try:
            res = self.glue_client.get_database(Name = self.database_name)
            curr_data = sic_lib.pickup(res["Database"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise

    def create(self, confirmation_flag, src_data):
        update_data = copy.copy(src_data)
        update_data["Name"] = self.database_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.create_database(DatabaseInput = {{Name: {self.database_name}, ...}})",
            lambda:
                self.glue_client.create_database(DatabaseInput = update_data)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = copy.copy(src_data)
        update_data["Name"] = self.database_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.update_database(Name = {self.database_name}, TableInput = {{Name: {self.database_name}, ...}})",
            lambda:
                self.glue_client.update_database(Name = self.database_name,
                DatabaseInput = update_data)
        )

    def delete(self, confirmation_flag, curr_data):
        sic_main.exec_put(confirmation_flag,
            f"glue_client.delete_database(Name = {self.database_name})",
            lambda:
                self.glue_client.delete_database(Name = self.database_name)
        )
        self.described = False

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
        info = TableInfo(self.glue_client, self.database_name, name)
        return common_action.NamespaceHandler(
            "conf", ["conf", "columns"], {
            "conf": TableConfHandler(info),
            "columns": TableColumnsHandler(info),
        })

class TableInfo:

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
    ]

    def __init__(self, glue_client, database_name, table_name):
        self.glue_client = glue_client
        self.database_name = database_name
        self.table_name = table_name
        self.info = None
        self.described = False

    def describe(self):
        if not self.described:
            try:
                res = self.glue_client.get_table(DatabaseName = self.database_name, Name = self.table_name)
                self.info = sic_lib.pickup(res["Table"], self.properties)
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "EntityNotFoundException":
                    self.info = None
                else:
                    raise
            self.described = True
        return self.info

    def create(self, confirmation_flag, src_data):
        update_data = copy.copy(src_data)
        update_data["Name"] = self.table_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.create_table(DatabaseName = {self.database_name}, TableInput = {{Name: {self.table_name}, ...}})",
            lambda:
                self.glue_client.create_table(DatabaseName = self.database_name,
                TableInput = update_data)
        )
        self.described = False

    def update(self, confirmation_flag, src_data):
        if src_data == self.describe():
            return
        update_data = copy.copy(src_data)
        update_data["Name"] = self.table_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.update_table(DatabaseName = {self.database_name}, TableInput = {{Name: {self.table_name}, ...}})",
            lambda:
                self.glue_client.update_table(DatabaseName = self.database_name,
                TableInput = update_data)
        )
        self.described = False

    def delete(self, confirmation_flag):
        sic_main.exec_put(confirmation_flag,
            f"glue_client.delete_table(DatabaseName = {self.database_name}, Name = {self.table_name})",
            lambda:
                self.glue_client.delete_table(
                    DatabaseName = self.database_name,
                    Name = self.table_name)
        )
        self.described = False

class TableConfHandler(common_action.ResourceHandler):

    def __init__(self, info: TableInfo):
        self.info = info

    def describe(self):
        info = self.info.describe()
        if info == None:
            return None
        curr_data = copy.copy(info)
        curr_data["StorageDescriptor"] = copy.copy(curr_data["StorageDescriptor"])
        sic_lib.removeKey(curr_data["StorageDescriptor"], "Columns")
        return curr_data

    def create(self, confirmation_flag, src_data):
        update_data = copy.copy(src_data)
        update_data["StorageDescriptor"]["Columns"] = []
        self.info.create(confirmation_flag, update_data)

    def update(self, confirmation_flag, src_data, curr_data):
        info = self.info.describe()
        update_data = copy.copy(src_data)
        update_data["StorageDescriptor"] = copy.copy(src_data["StorageDescriptor"])
        update_data["StorageDescriptor"]["Columns"] = info["StorageDescriptor"]["Columns"]
        self.info.update(confirmation_flag, update_data)

    def delete(self, confirmation_flag, curr_data):
        self.info.delete(confirmation_flag)

class TableColumnsHandler(common_action.ResourceHandler):

    def __init__(self, info: TableInfo):
        self.info = info

    def describe(self):
        info = self.info.describe()
        if info == None:
            return None
        curr_data = self._decode_columns(info["StorageDescriptor"]["Columns"])
        return curr_data

    def create(self, confirmation_flag, src_data):
        if not confirmation_flag:
            # 新規作成時の --dry-run ではdescribeでエラーになるため処理をスキップ
            return
        self.update(confirmation_flag, src_data, None)

    def update(self, confirmation_flag, src_data, curr_data):
        info = self.info.describe()
        info = copy.copy(info)
        info["StorageDescriptor"] = copy.copy(info["StorageDescriptor"])
        info["StorageDescriptor"]["Columns"] = self._encode_columns(src_data)
        self.info.update(confirmation_flag, info)

    def delete(self, confirmation_flag, curr_data):
        pass

    def _decode_columns(self, info):
        data = {}
        for elem in info:
            name = elem["Name"]
            if len(elem) == 2 and "Type" in elem:
                value = elem["Type"]
            else:
                value = copy.copy(elem)
                del value["Name"]
            data[name] = value
        return data

    def _encode_columns(self, data):
        info = []
        for name, value in data.items():
            if isinstance(value, str):
                elem = {
                    "Name": name,
                    "Type": value,
                }
            else:
                elem = copy.copy(value)
                elem["Name"] = name
            info.append(elem)
        return info
