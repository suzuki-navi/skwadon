import copy
import json

import botocore

import skwadon.lib as sic_lib
import skwadon.common_action as common_action

class ClusterListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.redshift_client = None
        self.clusters = None

    def init_client(self):
        if self.redshift_client == None:
            self.redshift_client = self.session.client("redshift")
            self.clusters = {}
            res = self.redshift_client.describe_clusters()
            while True:
                for elem in res['Clusters']:
                    name = elem["ClusterIdentifier"]
                    self.clusters[name] = elem
                if not "Marker" in res:
                    break
                res = self.redshift_client.describe_clusters(Marker = res["Marker"])

    def list(self):
        self.init_client()
        result = []
        for name in self.clusters:
            result.append(name)
        return result

    def child_handler(self, name):
        self.init_client()
        if name in self.clusters:
            info = self.clusters[name]
        else:
            info = None
        return common_action.NamespaceHandler(
            "conf", ["conf"], {
            "conf": ClusterConfHandler(name, info),
            "status": ClusterStatusHandler(name, info),
            "connection": ClusterConnectionHandler(self.redshift_client, name, info),
        })

class ClusterConfHandler(common_action.ResourceHandler):

    properties = [
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

    def __init__(self, cluster_name, cluster_info):
        self.cluster_name = cluster_name
        self.cluster_info = cluster_info

    def describe(self):
        if self.cluster_info == None:
            return None
        curr_data = sic_lib.pickup(self.cluster_info, self.properties)
        return curr_data

class ClusterStatusHandler(common_action.ResourceHandler):

    properties = [
        "ClusterStatus",
        "ClusterAvailabilityStatus",
        "ModifyStatus",
        "Endpoint",
        "ClusterCreateTime",
        "ClusterSecurityGroups",
        "VpcSecurityGroups",
        "ClusterParameterGroups",
        "PendingModifiedValues",
        "ClusterVersion",
        "AllowVersionUpgrade",
        "RestoreStatus",
        "DataTransferProgress",
        "HsmStatus",
        "ClusterSnapshotCopyStatus",
        "ClusterPublicKey",
        "ClusterNodes",
        "ElasticIpStatus",
        "ClusterRevisionNumber",
        "KmsKeyId",
        "IamRoles",
        "PendingActions",
        "ElasticResizeNumberOfNodeOptions",
        "DeferredMaintenanceWindows",
        "SnapshotScheduleIdentifier",
        "SnapshotScheduleState",
        "ExpectedNextSnapshotScheduleTime",
        "ExpectedNextSnapshotScheduleTimeStatus",
        "NextMaintenanceWindowStartTime",
        "ResizeInfo",
        "AvailabilityZoneRelocationStatus",
        "ClusterNamespaceArn",
        "TotalStorageCapacityInMegaBytes",
        "AquaConfiguration",
        "DefaultIamRoleArn",
        "ReservedNodeExchangeStatus",
    ]

    def __init__(self, cluster_name, cluster_info):
        self.cluster_name = cluster_name
        self.cluster_info = cluster_info

    def describe(self):
        curr_data = sic_lib.pickup(self.cluster_info, self.properties)
        return curr_data

class ClusterConnectionHandler(common_action.ResourceHandler):

    def __init__(self, redshift_client, cluster_name, cluster_info):
        self.redshift_client = redshift_client
        self.cluster_name = cluster_name
        self.cluster_info = cluster_info

    def describe(self):
        request_info = {
            "DbUser": self.cluster_info["MasterUsername"],
            "DbName": self.cluster_info["DBName"],
            "ClusterIdentifier": self.cluster_name,
            "DurationSeconds": 3600,
            "AutoCreate": False,
        }
        res = self.redshift_client.get_cluster_credentials(**request_info)
        cmd = f"PGPASSWORD='{res['DbPassword']}' psql -h {self.cluster_info['Endpoint']['Address']} -p {self.cluster_info['Endpoint']['Port']} -U {res['DbUser']} -d {self.cluster_info['DBName']}"
        result = {
            "Endpoint": {
                "Address": self.cluster_info["Endpoint"]["Address"],
                "Port": self.cluster_info["Endpoint"]["Port"],
            },
            "DbName": self.cluster_info["DBName"],
            "DbUser": res["DbUser"],
            "DbPassword": res["DbPassword"],
            "Expiration": res["Expiration"],
            "CommandLine": cmd,
        }
        return result

