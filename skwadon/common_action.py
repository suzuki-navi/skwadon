from abc import abstractmethod

import skwadon.action_lib as action_lib

# Handlerは各階層でのdo_get, do_putを実装するクラス。
# 各階層ごとに再帰的に処理していく。
#
# 階層とは
#   $ skwadon aws iam.roles.AWSServiceRoleForAPIGateway
# と実行した場合
#   - iam
#   - iam.roles
#   - iam.roles.AWSServiceRoleForAPIGateway
#  の3階層。
#
# このファイルではHandlerのほかにHandlerのサブクラスを定義している。
#
# ListHandler
#   リソースの一覧を表現する階層
#   AWSの各サービスでのリソース一覧はこのクラスのサブクラスを実装する
# NamespaceHandler
#   名前を区切っているだけの階層
#   サブクラスを実装することなくAWSの各サービスで直接インスタンスを生成する
# ResourceHandler
#   リソースの実際の属性値などを表現する階層
#   AWSの各サービスでこのクラスのサブクラスを実装する
# ResourceInfoHandler
#   describeのみを実装しているResourceHandlerのサブクラス


class Handler:

    # getアクションを実装
    @abstractmethod
    def do_get(self, src_data, thats_all_flag):
        return {}

    # putアクションを実装 (deleteアクションを含む)
    # 返り値
    #   dryrun(confirmation_flag=False): (入力, 変更前のクラウド)
    #   更新実行(confirmation_flag=True): (変更後のクラウド, 変更前のクラウド)
    @abstractmethod
    def do_put(self, confirmation_flag, src_data):
        return ({}, {})


# abstract
class ListHandler(Handler):

    def do_get(self, src_data, thats_all_flag):
        if hasattr(self, "is_default_all") and self.is_default_all:
            default_keys = None
        else:
            default_keys = []
        return action_lib.encode_for_get_list(
            src_data, thats_all_flag, default_keys,
            lambda: self._list(),
            lambda name, src_data: self.child_handler(name).do_get(src_data, thats_all_flag),
        )

    def do_put(self, confirmation_flag, src_data):
        if src_data is None:
            src_data = {"*": None}
        elif not isinstance(src_data, dict):
            src_data = {}
        result1 = {}  # 入力または変更後のクラウド
        result2 = {}  # 変更前のクラウド
        for name, value in src_data.items():
            if name == "*":
                for name2 in self._list():
                    if name2 not in src_data:
                        d1, d2 = self.child_handler(name2).do_put(confirmation_flag, None)
                        result1[name2] = None
                        result2[name2] = d2
            elif value is None:
                curr_data = self.child_handler(name).do_get(None, False)
                if curr_data is not None:
                    d1, d2 = self.child_handler(name).do_put(confirmation_flag, None)
                    result1[name] = None
                    result2[name] = d2
            else:
                d1, d2 = self.child_handler(name).do_put(confirmation_flag, value)
                result1[name] = d1
                result2[name] = d2
        return (result1, result2)

    def _list(self):
        return self.sort_items(self.list())

    @abstractmethod
    def list(self):
        raise Exception(f"list method not implemented: {self}")

    @abstractmethod
    def child_handler(self, name):
        return Handler()

    def sort_items(self, list):
        return sorted(list)


class NamespaceHandler(Handler):
    def __init__(self, conf_key, default_keys, path_map):
        self.conf_key = conf_key
        self.default_keys = default_keys
        handler_map = {}
        for path, handler in path_map.items():
            p = path.find(".")
            if p < 0:
                h = path
                t = ""
            else:
                h = path[0:p]
                t = path[p+1:]
            if h not in handler_map:
                handler_map[h] = {}
            handler_map[h][t] = handler
        self.handler_map = {}
        for key, map in handler_map.items():
            if "" in map:
                self.handler_map[key] = map[""]
            else:
                self.handler_map[key] = NamespaceHandler(None, [], map)

    def do_get(self, src_data, thats_all_flag):
        if self.conf_key:
            conf = self.handler_map[self.conf_key].do_get(None, False)
            if conf is None:
                return None
        def sub(name, src_data):
            if name in self.handler_map:
                return self.handler_map[name].do_get(src_data, thats_all_flag)
            else:
                return None
        result = action_lib.encode_for_get_list(
            src_data, thats_all_flag, self.default_keys,
            lambda: self.handler_map.keys(),
            lambda name, src_data: sub(name, src_data),
        )
        return result

    def do_put(self, confirmation_flag, src_data):
        if self.conf_key:
            conf = self.handler_map[self.conf_key].do_get(None, False)
            if conf is None:
                if src_data is None:
                    return (None, None)
        if src_data is None:
            src_data = {"*": None}
        elif not isinstance(src_data, dict):
            src_data = {}
        result1 = {}  # 入力または変更後のクラウド
        result2 = {}  # 変更前のクラウド
        for name, value in src_data.items():
            if name == "*":
                if value is None:
                    result2r = {}
                    for name2 in reversed(self.handler_map.keys()):
                        if name2 not in src_data:
                            d1, d2 = self.handler_map[name2].do_put(confirmation_flag, None)
                            result2r[name2] = d2
                    for name2 in reversed(result2r.keys()):
                        result1[name2] = None
                        result2[name2] = result2r[name2]
                result1[name] = value
            elif value is None:
                if name in self.handler_map:
                    d1, d2 = self.handler_map[name].do_put(confirmation_flag, None)
                    result1[name] = None
                    result2[name] = d2
            else:
                if name in self.handler_map:
                    d1, d2 = self.handler_map[name].do_put(confirmation_flag, value)
                    result1[name] = d1
                    result2[name] = d2
        return (result1, result2)


# abstract
class ResourceHandler(Handler):
    def do_get(self, src_data, thats_all_flag):
        curr_data = self.describe()
        return action_lib.encode_for_get_resource2(src_data, curr_data, thats_all_flag)

    def do_put(self, confirmation_flag, src_data):
        curr_data = self.describe()

        # 1つ目の返り値: 実際に self.updateに渡す値
        # 2つ目の返り値: コマンドの出力結果としての入力
        # 3つ目の返り値: コマンドの出力結果としての変更前のクラウド
        def build_update_data(src_data, curr_data):
            if not isinstance(src_data, dict) or not isinstance(curr_data, dict):
                src_data2 = action_lib.decode_for_put(src_data)
                result2 = action_lib.encode_for_get_resource(curr_data)
                return (src_data2, src_data, result2)
            src_data2 = {}  # 実際に self.updateに渡す値
            result1 = {}
            result2 = {}
            delete_flag = False
            for name, value in src_data.items():
                if name == "*":
                    if value is None:
                        for name2 in curr_data:
                            if name2 not in src_data:
                                result2[name2] = action_lib.encode_for_get_resource(curr_data[name2])
                        delete_flag = True
                elif value is None:
                    if name in curr_data:
                        result2[name] = action_lib.encode_for_get_resource(curr_data[name])
                else:
                    if name in curr_data:
                        src_data2[name], result1[name], result2[name] = build_update_data(value, curr_data[name])
                    else:
                        src_data2[name], result1[name], _ = build_update_data(value, None)
            if not delete_flag:
                for name in curr_data:
                    if name not in src_data2:
                        src_data2[name] = action_lib.encode_for_get_resource(curr_data[name])
            return (src_data2, result1, result2)

        src_data2, result1, result2 = build_update_data(src_data, curr_data)
        if src_data2 == curr_data:
            return (result1, result2)

        if curr_data is None:
            self.create(confirmation_flag, src_data2)
        elif src_data is None:
            self.delete(confirmation_flag, curr_data)
        else:
            self.update(confirmation_flag, src_data2, curr_data)

        if confirmation_flag:
            _, _, result1 = build_update_data(src_data, self.describe())

        return (result1, result2)

    @abstractmethod
    def describe(self):
        raise Exception(f"describe method not implemented: {self}")

    @abstractmethod
    def create(self, confirmation_flag, src_data):
        self.put(confirmation_flag, src_data)

    @abstractmethod
    def update(self, confirmation_flag, src_data, curr_data):
        self.put(confirmation_flag, src_data)

    @abstractmethod
    def put(self, confirmation_flag, src_data):
        raise Exception(f"put method not implemented: {self}")

    @abstractmethod
    def delete(self, confirmation_flag, curr_data):
        raise Exception(f"delete method not implemented: {self}")


class ResourceInfoHandler(ResourceHandler):

    def __init__(self, info):
        self.info = info

    def describe(self):
        return self.info

