
def encode_for_get_list(src_data, thats_all_flag, default_keys, items_fetcher, item_detail_fetcher):
    if not isinstance(src_data, dict):
        src_data = {"*": None}
    result = {}
    unknown_flag = False
    for name, value in src_data.items():
        if name == "*":
            for name2 in items_fetcher():
                if not name2 in src_data:
                    if value != None and value != {}:
                        result[name2] = item_detail_fetcher(name2, value)
                    elif value == None and (default_keys is None or name2 in default_keys):
                        result[name2] = item_detail_fetcher(name2, None)
                    else:
                        result[name2] = {}
            unknown_flag = True
        else:
            d = item_detail_fetcher(name, value)
            if d != None:
                result[name] = d
    if unknown_flag and thats_all_flag:
        result["*"] = None
    return result

def encode_for_get_resource(data):
    return encode_for_get_resource2(None, data, False)

def encode_for_get_resource2(src_data, curr_data, thats_all_flag):
    if not isinstance(curr_data, dict):
        return curr_data
    if not isinstance(src_data, dict):
        src_data = {"*": None}
    result = {}
    unknown_flag = False
    for name, value in src_data.items():
        if name == "*":
            if value == None:
                for name2, value2 in curr_data.items():
                    if not name2 in src_data:
                        result[name2] = encode_for_get_resource2(value, value2, thats_all_flag)
                unknown_flag = True
        elif name in curr_data:
            result[name] = encode_for_get_resource2(value, curr_data[name], thats_all_flag)
        else:
            pass
    # AccessDeniedの場合は curr_data に {"*": "AccessDenied"} が来る
    # その場合は thats_all_flag があっても {"*": null} にしない
    if unknown_flag and thats_all_flag and "*" not in curr_data:
        result["*"] = None
    return result

def decode_for_put(src_data):
    if isinstance(src_data, str):
        return src_data
    if not isinstance(src_data, dict):
        return src_data
    src_data2 = {}
    for name, value in src_data.items():
        if name == "*":
            continue
        src_data2[name] = decode_for_put(value)
    return src_data2


