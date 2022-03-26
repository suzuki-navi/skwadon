
import skwadon.lib as sic_lib
import skwadon.common_action as common_action


class ClusterListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.redshift_client = None
        self.clusters = None

    def init_client(self):
        if self.redshift_client is None:
            self.redshift_client = self.session.client("redshift")
            self.clusters = {}
            res = self.redshift_client.describe_clusters()
            while True:
                for elem in res['Clusters']:
                    name = elem["ClusterIdentifier"]
                    self.clusters[name] = elem
                if "Marker" not in res:
                    break
                res = self.redshift_client.describe_clusters(Marker=res["Marker"])

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
        info = self._create_instance_info(info)
        return common_action.NamespaceHandler(
            "conf", ["conf"],
            {
                "conf":       common_action.ResourceInfoHandler(info["conf"]),
                "all":        common_action.ResourceInfoHandler(info["all"]),
                "connection": ClusterConnectionHandler(self.redshift_client, name, info["all"]),
            },
        )

    def _create_instance_info(self, info):
        return {
            "conf": sic_lib.pickup(info, [
                "NodeType",
                "NumberOfNodes",
                "MasterUsername",
                "DBName",
            ]),
            "all": info,
        }


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


