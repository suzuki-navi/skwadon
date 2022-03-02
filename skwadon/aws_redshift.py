import copy
import json

import botocore.exceptions

import skwadon.main as sic_main
import skwadon.lib as sic_lib
import skwadon.common_action as common_action
import skwadon.aws as sic_aws

####################################################################################################

def set_handler(handler_map, session):
    common_action.set_handler(handler_map, "redshift.clusters",
        lister = lambda names: list_clusters(session),
    )
    common_action.set_handler(handler_map, "redshift.clusters.*cluster_name.conf",
        describer = lambda names: describe_cluster(session, **names),
    )
    common_action.set_handler(handler_map, "redshift.clusters.*cluster_name.status",
        describer = lambda names: describe_cluster_status(session, **names),
    )

####################################################################################################

def list_clusters(session):
    redshift_client = session.client("redshift")
    result = []
    res = redshift_client.describe_clusters()
    while True:
        for elem in res['Clusters']:
            name = elem["ClusterIdentifier"]
            result.append(name)
        if not "Marker" in res:
            break
        res = redshift_client.describe_clusters(Marker = res["Marker"])
    return result

####################################################################################################

cluster_conf_properties = [
    "NodeType",
    "NumberOfNodes",
    "MasterUsername",
    "DBName",
    "AutomatedSnapshotRetentionPeriod",
    "ManualSnapshotRetentionPeriod",
    "ClusterSubnetGroupName",
    "VpcId",
    "AvailabilityZone",
    "PreferredMaintenanceWindow",
    "PubliclyAccessible",
    "Encrypted",
    "EnhancedVpcRouting",
    "MaintenanceTrackName",
]

def describe_cluster(session, cluster_name):
    redshift_client = session.client("redshift")
    res = redshift_client.describe_clusters(ClusterIdentifier = cluster_name)
    curr_data = sic_lib.pickup(res["Clusters"][0], cluster_conf_properties)
    return curr_data

def describe_cluster_status(session, cluster_name):
    redshift_client = session.client("redshift")
    res = redshift_client.describe_clusters(ClusterIdentifier = cluster_name)
    curr_data = copy.deepcopy(res["Clusters"][0])
    return curr_data

####################################################################################################
