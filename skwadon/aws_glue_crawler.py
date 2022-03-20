import copy
import json

import botocore

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class CrawlerListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.glue_client = None

    def init_client(self):
        if self.glue_client == None:
            self.glue_client = self.session.client("glue")

    def list(self):
        self.init_client()
        result = []
        res = self.glue_client.get_crawlers()
        while True:
            for elem in res['Crawlers']:
                name = elem["Name"]
                result.append(name)
            if not "NextToken" in res:
                break
            res = self.glue_client.get_crawlers(NextToken = res["NextToken"])
        return result

    def child_handler(self, name):
        self.init_client()
        return common_action.NamespaceHandler(
            "conf", ["conf"], {
            "conf": CrawlerConfHandler(self.glue_client, name),
            "status": CrawlerStatusHandler(self.glue_client, name),
        })

class CrawlerConfHandler(common_action.ResourceHandler):

    properties = [
        "Role",
        "Targets",
        "DatabaseName",
        "Description",
        "Classifiers",
        "RecrawlPolicy",
        "SchemaChangePolicy",
        "LineageConfiguration",
        "TablePrefix",
        "Schedule",
        "Configuration",
        "CrawlerSecurityConfiguration",
        "LakeFormationConfiguration",
    ]

    def __init__(self, glue_client, crawler_name):
        self.glue_client = glue_client
        self.crawler_name = crawler_name

    def describe(self):
        try:
            res = self.glue_client.get_crawler(Name = self.crawler_name)
            curr_data = sic_lib.pickup(res["Crawler"], self.properties)
            return curr_data
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "EntityNotFoundException":
                return None
            else:
                raise

    def create(self, confirmation_flag, src_data):
        update_data = sic_lib.pickup(src_data, self.properties)
        update_data["Name"] = self.crawler_name
        sic_main.exec_put(confirmation_flag,
            f"glue_client.create_crawler(Name = {self.crawler_name}, ...)",
            lambda:
                self.glue_client.create_crawler(**update_data)
        )

    def update(self, confirmation_flag, src_data, curr_data):
        update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, self.properties)
        if update_data != None:
            update_data["Name"] = self.crawler_name
            sic_main.exec_put(confirmation_flag,
                f"glue_client.update_crawler(Name = {self.crawler_name}, ...)",
                lambda:
                    self.glue_client.update_crawler(**update_data)
            )

    def delete(self, confirmation_flag, curr_data):
        sic_main.add_update_message(f"glue_client.delete_crawler(Name = {self.crawler_name})")
        if confirmation_flag and sic_main.global_confirmation_flag:
            self.glue_client.delete_crawler(Name = self.crawler_name)

class CrawlerStatusHandler(common_action.ResourceHandler):

    properties = [
        "State",
        "CrawlElapsedTime",
        "CreationTime",
        "LastUpdated",
        "LastCrawl",
        "Version",
    ]

    def __init__(self, glue_client, crawler_name):
        self.glue_client = glue_client
        self.crawler_name = crawler_name

    def describe(self):
        res = self.glue_client.get_crawler(Name = self.crawler_name)
        curr_data = sic_lib.pickup(res["Crawler"], self.properties)
        return curr_data

    def delete(self, confirmation_flag, curr_data):
        pass
