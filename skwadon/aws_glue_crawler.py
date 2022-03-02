import copy
import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "glue.crawlers",
        lister = lambda names: list_crawlers(session),
    )
    common_action.set_handler(handler_map, "glue.crawlers.*crawler_name.conf",
        describer = lambda names: describe_crawler(session, **names),
        creator = lambda src_data, confirmation_flag, names: create_crawler(session, src_data, confirmation_flag, **names),
        updator = lambda src_data, curr_data, confirmation_flag, names: update_crawler(session, src_data, curr_data, confirmation_flag, **names),
        deleter = lambda confirmation_flag, names: delete_crawler(session, confirmation_flag, **names)
    )
    common_action.set_handler(handler_map, "glue.crawlers.*crawler_name.status",
        describer = lambda names: describe_crawler_status(session, **names),
    )

####################################################################################################

def list_crawlers(session):
    glue_client = session.client("glue")
    result = []
    res = glue_client.get_crawlers()
    while True:
        for elem in res['Crawlers']:
            name = elem["Name"]
            result.append(name)
        if not "NextToken" in res:
            break
        res = glue_client.get_crawlers(NextToken = res["NextToken"])
    return result

####################################################################################################

crawler_conf_properties = [
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
    "Version",
    "Configuration",
    "CrawlerSecurityConfiguration",
    "LakeFormationConfiguration",
]

crawler_status_properties = [
    "State",
    "CrawlElapsedTime",
    "CreationTime",
    "LastUpdated",
    "LastCrawl",
]

def describe_crawler(session, crawler_name):
    glue_client = session.client("glue")
    res = glue_client.get_crawler(Name = crawler_name)
    curr_data = sic_lib.pickup(res["Crawler"], crawler_conf_properties)
    return curr_data

def describe_crawler_status(session, crawler_name):
    glue_client = session.client("glue")
    res = glue_client.get_crawler(Name = crawler_name)
    curr_data = sic_lib.pickup(res["Crawler"], crawler_status_properties)
    return curr_data

def create_crawler(session, src_data, confirmation_flag, crawler_name):
    glue_client = session.client("glue")
    update_data = sic_lib.pickup(src_data, crawler_conf_properties)
    update_data["Name"] = crawler_name
    sic_lib.removeKey(update_data, "Version")
    sic_main.add_update_message(f"glue_client.create_crawler(Name = {crawler_name}, ...)")
    if confirmation_flag and sic_main.global_confirmation_flag:
        glue_client.create_crawler(**update_data)

def update_crawler(session, src_data, curr_data, confirmation_flag, crawler_name):
    glue_client = session.client("glue")
    update_data = sic_lib.pickupAndCompareForUpdate(src_data, curr_data, crawler_conf_properties)
    if update_data != None:
        update_data["Name"] = crawler_name
        sic_lib.removeKey(update_data, "Version")
        sic_main.add_update_message(f"glue_client.update_crawler(Name = {crawler_name}, ...)")
        if confirmation_flag and sic_main.global_confirmation_flag:
            glue_client.update_crawler(**update_data)

def delete_crawler(session, confirmation_flag, crawler_name):
    glue_client = session.client("glue")
    sic_main.add_update_message(f"glue_client.delete_crawler(Name = {crawler_name})")
    if confirmation_flag and sic_main.global_confirmation_flag:
        glue_client.delete_crawler(Name = crawler_name)

####################################################################################################
