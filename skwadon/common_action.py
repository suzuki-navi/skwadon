from abc import abstractmethod
import copy
import re
from termios import TIOCPKT_DOSTOP

import skwadon.main as sic_main
import skwadon.lib as sic_lib

class Handler:
    # abstract
    def do_get(self, src_data):
        return {}

    # abstract
    # 返り値は dryrunでは (入力, 変更前のクラウド)
    # 非dryrunでは (変更後のクラウド, 変更前のクラウド)
    def do_put(self, confirmation_flag, src_data):
        return ({}, {})

    # abstract
    # 返り値は dryrunでは 入力
    # 非dryrunでは 変更後のクラウド
    def do_create(self, confirmation_flag, src_data):
        return ({}, {})

    # abstract
    # 返り値は (変更後のクラウド, 変更前のクラウド)
    def do_delete(self, confirmation_flag):
        return ({}, {})

# abstract
class ListHandler(Handler):
    def do_get(self, src_data):
        items = self._list()
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
            for elem in items:
                result[elem] = {}
            result["*"] = None
        else:
            result = {}
            for name, src_data2 in src_data.items():
                if name == "*":
                    for name in items:
                        if not name in src_data:
                            result[name] = {}
                    result[name] = None
                elif name in items:
                    result[name] = self.child_handler(name).do_get(src_data2)
                else:
                    result[name] = None
        return result

    def do_put(self, confirmation_flag, src_data):
        if src_data == None:
            return self.do_delete(confirmation_flag)
        if not isinstance(src_data, dict):
            return ({}, {})
        if src_data == {}:
            return ({}, {})
        items = self._list()
        result1 = {}
        result2 = {}
        delete_flag = False
        for name in src_data:
            if name == "*":
                if src_data[name] == None:
                    delete_flag = True
                continue
            if name in items:
                d1, d2 = self.child_handler(name).do_put(confirmation_flag, src_data[name])
                result1[name] = d1
                result2[name] = d2
            elif src_data[name] == None:
                result1[name] = None
                result2[name] = None
            else:
                d1 = self.child_handler(name).do_create(confirmation_flag, src_data[name])
                result1[name] = d1
                result2[name] = None
        if delete_flag:
            for name in items:
                if not name in src_data:
                    d1, d2 = self.child_handler(name).do_delete(confirmation_flag)
                    result1[name] = d1
                    result2[name] = d2
        if confirmation_flag:
            items2 = self._list()
            for name in items:
                if name in result1:
                    if not name in items2:
                        result1[name] = None
        else:
            for name in items:
                if name in result1:
                    if delete_flag and not name in src_data:
                        result1[name] = None
                    elif name in src_data and src_data[name] == None:
                        result1[name] = None
        return (result1, result2)

    def do_create(self, confirmation_flag, src_data):
        result = {}
        for name in src_data:
            if name == "*":
                continue
            result[name] = self.child_handler(name).do_create(confirmation_flag, src_data[name])
        if confirmation_flag:
            items = self._list()
            for name in result:
                if not name in items:
                    result[name] = None
        return result

    def do_delete(self, confirmation_flag):
        items = self._list()
        result1 = {}
        result2 = {}
        for name in items:
            if name == "*":
                continue
            d1, d2 = self.child_handler(name).do_delete(confirmation_flag)
            result1[name] = d1
            result2[name] = d2
        if confirmation_flag:
            items = self._list()
            for name in result1:
                if not name in items:
                    result1[name] = None
        else:
            for name in result1:
                result1[name] = None
        return (result1, result2)

    def _list(self):
        return self.sort_items(self.list())

    @abstractmethod
    def list(self):
        raise Exception(f"list method not implemented: {self}")

    # abstract
    def child_handler(self, name):
        return Handler()

    def sort_items(self, list):
        return sorted(list)

# abstract
class ResourceHandler(Handler):
    def do_get(self, src_data):
        curr_data = sic_lib.skwadondict_encode(self.describe())
        def build_result_data(src_data, curr_data):
            if not isinstance(src_data, dict) or not isinstance(curr_data, dict):
                return curr_data
            if len(src_data) == 0:
                return sic_lib.skwadondict_encode(curr_data)
            result = {}
            for name in src_data:
                if name == "*":
                    for name in curr_data:
                        if not name in src_data:
                            result[name] = sic_lib.skwadondict_encode(curr_data[name])
                    result[name] = None
                elif name in curr_data:
                    result[name] = build_result_data(src_data[name], curr_data[name])
                else:
                    result[name] = None
            return result
        return build_result_data(src_data, curr_data)

    def do_put(self, confirmation_flag, src_data):
        if src_data == None:
            return self.do_delete(confirmation_flag)
        if src_data == {}:
            return ({}, {})
        curr_data = sic_lib.skwadondict_encode(self.describe())
        def build_update_data(src_data, curr_data):
            if not isinstance(src_data, dict) or not isinstance(curr_data, dict):
                return (src_data, curr_data)
            if len(src_data) == 0:
                return ({}, {})
            src_data2 = {}
            curr_data2 = {}
            delete_flag = False
            for name in src_data:
                if name == "*":
                    if src_data[name] == None:
                        delete_flag = True
                    continue
                if name in curr_data:
                    src_data2[name], curr_data2[name] = build_update_data(src_data[name], curr_data[name])
                else:
                    src_data2[name] = src_data[name]
            if not delete_flag:
                for name in curr_data:
                    if name == "*":
                        continue
                    if not name in src_data2:
                        src_data2[name] = curr_data[name]
            src_data2["*"] = None
            curr_data2["*"] = None
            # src_data2: 実際に self.update に渡す値
            # curr_data2: コマンドの出力結果としての現在の値
            return (src_data2, curr_data2)
        src_data2, curr_data2 = build_update_data(src_data, curr_data)
        if src_data2 == curr_data:
            return (src_data, curr_data2)
        self.update(confirmation_flag, sic_lib.skwadondict_decode(src_data2), curr_data)
        if confirmation_flag:
            _, curr_data3 = build_update_data(src_data, sic_lib.skwadondict_encode(self.describe()))
            return (curr_data3, curr_data2)
        else:
            return (src_data, curr_data2)

    def do_create(self, confirmation_flag, src_data):
        self.create(confirmation_flag, sic_lib.skwadondict_decode(src_data))
        if not confirmation_flag:
            return src_data
        new_data = sic_lib.skwadondict_encode(self.describe())
        return new_data

    def do_delete(self, confirmation_flag):
        curr_data = sic_lib.skwadondict_encode(self.describe())
        result1 = {}
        result2 = curr_data
        self.delete(confirmation_flag, curr_data)
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

class NamespaceHandler(Handler):
    def __init__(self, path_map):
        handler_map = {}
        for path, handler in path_map.items():
            p = path.find(".")
            if p < 0:
                h = path
                t = ""
            else:
                h = path[0:p]
                t = path[p+1:]
            if not h in handler_map:
                handler_map[h] = {}
            handler_map[h][t] = handler
        self.handler_map = {}
        for key, map in handler_map.items():
            if "" in map:
                self.handler_map[key] = map[""]
            else:
                self.handler_map[key] = NamespaceHandler(map)

    def do_get(self, src_data):
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
            for name in self.handler_map:
                result[name] = {}
        else:
            result = {}
            for name in src_data:
                if name == "*":
                    for name in self.handler_map:
                        if not name in src_data:
                            result[name] = {}
                elif name in self.handler_map:
                    result[name] = self.handler_map[name].do_get(src_data[name])
                else:
                    result[name] = None
        return result

    def do_put(self, confirmation_flag, src_data):
        if src_data == None:
            return self.do_delete(confirmation_flag)
        if not isinstance(src_data, dict):
            result1 = {}
            result2 = {}
        else:
            result1 = {}
            result2 = {}
            for name in src_data:
                if name == "*":
                    continue
                if name in self.handler_map:
                    d1, d2 = self.handler_map[name].do_put(confirmation_flag, src_data[name])
                    result1[name] = d1
                    result2[name] = d2
        return (result1, result2)

    def do_create(self, confirmation_flag, src_data):
        if not isinstance(src_data, dict):
            result = {}
        else:
            result = {}
            for name in src_data:
                if name == "*":
                    continue
                if name in self.handler_map:
                    result[name] = self.handler_map[name].do_create(confirmation_flag, src_data[name])
        return result

    def do_delete(self, confirmation_flag):
        result1 = {}
        result2 = {}
        for name in reversed(self.handler_map.keys()):
            d1, d2 = self.handler_map[name].do_delete(confirmation_flag)
            result1[name] = d1
            result2[name] = d2
        result1r = {}
        result2r = {}
        for name in self.handler_map.keys():
            result1r[name] = result1[name]
            result2r[name] = result2[name]
        return (result1r, result2r)
