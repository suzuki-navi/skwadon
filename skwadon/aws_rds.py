
import skwadon.lib as sic_lib
import skwadon.common_action as common_action


class InstanceListHandler(common_action.ListHandler):
    def __init__(self, session):
        self.session = session
        self.rds_client = None
        self.instances = None

    def init_client(self):
        if self.rds_client is None:
            self.rds_client = self.session.client("rds")
            self.instances = {}
            res = self.rds_client.describe_db_instances()
            while True:
                for elem in res['DBInstances']:
                    name = elem["DBInstanceIdentifier"]
                    self.instances[name] = elem
                if "Marker" not in res:
                    break
                res = self.rds_client.describe_db_instances(Marker=res["Marker"])

    def list(self):
        self.init_client()
        result = []
        for name in self.instances:
            result.append(name)
        return result

    def child_handler(self, name):
        self.init_client()
        if name in self.instances:
            info = self.instances[name]
        else:
            info = None
        info = self._create_instance_info(info)
        return common_action.NamespaceHandler(
            "conf", ["conf"],
            {
                "conf":   common_action.ResourceInfoHandler(info["conf"]),
                "status": common_action.ResourceInfoHandler(info["status"]),
                "all":    common_action.ResourceInfoHandler(info["all"]),
            },
        )

    def _create_instance_info(self, info):
        return {
            "conf": sic_lib.pickup(info, [
                "DBInstanceClass",
                "Engine",
                "MasterUsername",
                "DBName",
            ]),
            "status": sic_lib.pickup(info, [
                "DBInstanceStatus",
                "AutomaticRestartTime",
            ]),
            "all": info,
        }

