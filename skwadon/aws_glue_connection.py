import copy
import json
import re

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class ConnectionListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session

    def list(self):
        self.glue_client = self.session.client("glue")
        result = []
        res = self.glue_client.get_connections()
        while True:
            for elem in res['ConnectionList']:
                name = elem["Name"]
                result.append(name)
            if not "NextToken" in res:
                break
            res = self.glue_client.get_connections(NextToken = res["NextToken"])
        return result

    def child_handler(self, name):
        return common_action.NamespaceHandler({
            "conf": ConnectionConfHandler(self.glue_client, name),
            "connection": ConnectionConnectionHandler(self.glue_client, name),
        })

class ConnectionConfHandler(common_action.ResourceHandler):

    properties = [
        "Description",
        "ConnectionType",
        "MatchCriteria",
        "ConnectionProperties",
        "PhysicalConnectionRequirements",
    ]

    def __init__(self, glue_client, connection_name):
        self.glue_client = glue_client
        self.connection_name = connection_name

    def describe(self):
        res = self.glue_client.get_connection(Name = self.connection_name)
        curr_data = sic_lib.pickup(res["Connection"], self.properties)
        return curr_data

    def create(self, confirmation_flag, src_data):
        update_data = sic_lib.pickup(src_data, self.properties)
        update_data["Name"] = self.connection_name
        sic_main.add_update_message(f"glue_client.create_connection(ConnectionInput = {{Name = {self.connection_name}, ...}})")
        if confirmation_flag and sic_main.global_confirmation_flag:
            self.glue_client.create_connection(ConnectionInput = update_data)

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, self.properties)
        if update_data != None:
            update_data["Name"] = self.connection_name
            sic_main.add_update_message(f"glue_client.update_connection(Name = {self.connection_name}, ...)")
            if confirmation_flag and sic_main.global_confirmation_flag:
                self.glue_client.update_connection(Name = self.connection_name, ConnectionInput = update_data)

class ConnectionConnectionHandler(common_action.ResourceHandler):

    properties = [
        "Description",
        "ConnectionType",
        "MatchCriteria",
        "ConnectionProperties",
        "PhysicalConnectionRequirements",
    ]

    def __init__(self, glue_client, connection_name):
        self.glue_client = glue_client
        self.connection_name = connection_name

    def describe(self):
        res = self.glue_client.get_connection(Name = self.connection_name)
        jdbc_url = sic_lib.dictlib_get(res, "Connection.ConnectionProperties.JDBC_CONNECTION_URL")
        curr_data = {
        }
        if jdbc_url != None:
            curr_data["JBCDUrl"] = jdbc_url
            m = re.compile("\Ajdbc:([^:]+)://([^:]+):([0-9]+)/(.+)\Z").search(jdbc_url)
            if m:
                driver = m.group(1)
                if driver == "postgresql" or driver == "redshift":
                    host = m.group(2)
                    port = m.group(3)
                    db_name = m.group(4)
                    user_name = sic_lib.dictlib_get(res, "Connection.ConnectionProperties.USERNAME")
                    password = sic_lib.dictlib_get(res, "Connection.ConnectionProperties.PASSWORD")
                    cmd = f"PGPASSWORD='{password}' psql -h {host} -p {port} -U {user_name} -d {db_name}"
                    curr_data["CommandLine"] = cmd
        return curr_data

    def create(self, confirmation_flag, src_data):
        pass

    def update(self, confirmation_flag, src_data, curr_data):
        pass
