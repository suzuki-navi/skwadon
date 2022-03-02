import copy
import re

import skwadon.lib as sic_lib

####################################################################################################

#def null_lister(names):
#    return []
#
#def null_describer(names):
#    return {}
#
#def null_creator(src_data, confirmation_flag, names):
#    return None
#
#def null_updator(src_data, curr_data, confirmation_flag, names):
#    return curr_data
#
#def null_deleter(confirmation_flag, names):
#    return curr_data

def set_handler(handler_map, path, *,
    lister = None,
    describer = None,
    creator = None,
    updator = None,
    deleter = None):
    def sub(handler_map, path):
        head = path[0]
        if head.startswith("*"):
            if not "lister" in handler_map:
                raise Exception()
            if not "wildcard" in handler_map:
                handler_map["wildcard"] = head[1:]
                handler_map["children"] = {}
            children = handler_map["children"]
        else:
            if "lister" in handler_map:
                raise Exception()
            key = "#" + head
            if not key in handler_map:
                handler_map[key] = {}
            children = handler_map[key]
        if len(path) == 1:
            if lister != None:
                children["lister"] = lister
            else:
                if describer != None:
                    children["describer"] = describer
                if creator != None:
                    children["creator"] = creator
                if updator != None:
                    children["updator"] = updator
                if deleter != None:
                    children["deleter"] = deleter
        else:
            sub(children, path[1:])
    path = path.split(".")
    sub(handler_map, path)

####################################################################################################

def do_action(handler_map, action, confirmation_flag, path, src_data):
    if path == None:
        path2 = []
    else:
        path2 = path
    if action == "get":
        return do_get(handler_map, {}, src_data)
    elif action == "put":
        return do_put(confirmation_flag, handler_map, {}, path2, src_data)

####################################################################################################

def do_get(handler_map, names, src_data):
    if "lister" in handler_map:
        items = handler_map["lister"](names)
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
            for elem in items:
                result[elem] = {}
        else:
            result = {}
            if "wildcard" in handler_map:
                key = handler_map["wildcard"]
                for name, src_data2 in src_data.items():
                    if name in items:
                        names2 = copy.copy(names)
                        names2[key] = name
                        result[name] = do_get(handler_map["children"], names2, src_data2)
                    else:
                        result[name] = None
            else:
                for name, src_data2 in src_data.items():
                    if name in items:
                        result[name] = {}
                    else:
                        result[name] = None
    elif "describer" in handler_map:
        result = handler_map["describer"](names)
    else:
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
            for key in handler_map:
                if key.startswith("#"):
                    name = key[1:]
                    result[name] = {}
        else:
            result = {}
            for name, src_data2 in src_data.items():
                key = "#" + name
                if key in handler_map:
                    result[name] = do_get(handler_map[key], names, src_data2)
    return result

# path は大きさ0以上の配列
def do_put(confirmation_flag, handler_map, names, path, src_data):
    if "lister" in handler_map:
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
        else:
            result = {}
            items = handler_map["lister"](names)
            if "wildcard" in handler_map:
                key = handler_map["wildcard"]
                for name, src_data2 in src_data.items():
                    names2 = copy.copy(names)
                    names2[key] = name
                    path2 = []
                    if len(path) > 1 and path[0] == name:
                        path2 = path[1:]
                    if name in items:
                        if src_data2 == None:
                            result[name] = do_delete(confirmation_flag, handler_map["children"], names2)
                        else:
                            result[name] = do_put(confirmation_flag, handler_map["children"], names2, path2, src_data2)
                    else:
                        if src_data2 == None:
                            result[name] = None
                        elif len(path2) == 0:
                            do_create(confirmation_flag, handler_map["children"], names2, src_data2)
                            result[name] = None
                        else:
                            # この場合は情報が足りなくて作成できない
                            result[name] = None
            else:
                for name in items:
                    result[name] = {}
    elif "describer" in handler_map:
        result = handler_map["describer"](names)
        if "updator" in handler_map:
            if len(path) == 0:
                if src_data != result:
                    handler_map["updator"](src_data, result, confirmation_flag, names)
            else:
                result2 = sic_lib.intersect_dict(result, src_data)
                src_data2 = sic_lib.update_dict(result, src_data)
                if src_data2 != result2:
                    handler_map["updator"](src_data2, result2, confirmation_flag, names)
                result = result2
    else:
        if not isinstance(src_data, dict) or len(src_data) == 0:
            result = {}
        else:
            result = {}
            for name, src_data2 in src_data.items():
                key = "#" + name
                path2 = []
                if len(path) > 1 and path[0] == name:
                    path2 = path[1:]
                if key in handler_map:
                    result[name] = do_put(confirmation_flag, handler_map[key], names, path2, src_data2)
    return result

def do_create(confirmation_flag, handler_map, names, src_data):
    if "lister" in handler_map:
        if "wildcard" in handler_map:
            key = handler_map["wildcard"]
            for name, src_data2 in src_data.items():
                names2 = copy.copy(names)
                names2[key] = name
                do_create(confirmation_flag, handler_map["children"], names2, src_data2)
    elif "describer" in handler_map:
        if "creator" in handler_map:
            handler_map["creator"](src_data, confirmation_flag, names)
    else:
        for key in handler_map:
            if key.startswith("#"):
                name = key[1:]
                if name in src_data:
                    do_create(confirmation_flag, handler_map[key], names, src_data[name])

def do_delete(confirmation_flag, handler_map, names):
    if "lister" in handler_map:
        result = {}
        items = handler_map["lister"](names)
        if "wildcard" in handler_map:
            key = handler_map["wildcard"]
            for name in items:
                names2 = copy.copy(names)
                names2[key] = name
                result[name] = do_delete(confirmation_flag, handler_map["children"], names2)
        else:
            for name in items:
                result[name] = {}
    elif "describer" in handler_map:
        result = handler_map["describer"](names)
        if "deleter" in handler_map:
            handler_map["deleter"](confirmation_flag, names)
    else:
        result = {}
        for key, h in reversed(handler_map.items()):
            if key.startswith("#"):
                name = key[1:]
                result[name] = do_delete(confirmation_flag, handler_map[key], names)
        result2 = {}
        for k, v in reversed(result.items()):
            result2[k] = v
        result = result2
    return result

####################################################################################################
