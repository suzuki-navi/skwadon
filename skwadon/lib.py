import os
import random
import sys
import tempfile
import urllib

def removeKey(info: dict, key: str):
    if key in info:
        del info[key]

def exec_diff(content1, content2, dst_file, name1 = "1", name2 = "2"):
    sys.stdout.flush()
    sys.stderr.flush()
    tmpdir = tempfile.mkdtemp()
    fifo1 = tmpdir + "/" + name1
    fifo2 = tmpdir + "/" + name2
    os.mkfifo(fifo1)
    os.mkfifo(fifo2)
    pid = os.fork()
    if pid == 0:
        if dst_file != None:
            sys.stdout = open(dst_file, "w")
        os.execvp("diff", ["diff", "-u", fifo1, fifo2])
    pid1 = os.fork()
    if pid1 == 0:
        writer1 = open(fifo1, "w")
        writer1.write(content1)
        writer1.close()
        sys.exit()
    pid2 = os.fork()
    if pid2 == 0:
        writer2 = open(fifo2, "w")
        writer2.write(content2)
        writer2.close()
        sys.exit()
    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)
    os.waitpid(pid, 0)
    os.remove(fifo1)
    os.remove(fifo2)
    os.rmdir(tmpdir)

def normalize_script_source(script_source):
    lines = []
    for line in script_source.split("\n"):
        lines.append(line.rstrip(" \t\r"))
    while len(lines) > 0 and lines[0] == "":
        lines = lines[1:]
    while len(lines) > 0 and lines[len(lines) - 1] == "":
        lines = lines[0 : len(lines) - 1]
    return "\n".join(lines) + "\n"

def script_sources_to_yaml(script_dir):
    result = {}
    for file_name in os.listdir(script_dir):
        if os.path.isdir(file_name):
            result[file_name] = script_sources_to_yaml(script_dir + "/" + file_name)
        else:
            with open(script_dir + "/" + file_name) as fh:
                result[file_name] = normalize_script_source(fh.read())
    return result

def script_sources_from_yaml(script_dir, sources):
    for name, data in sources.items():
        path = script_dir + "/" + name
        if isinstance(data, dict):
            if not os.path.exists(path):
                os.makedirs(path)
            script_sources_from_yaml(path, data)
        else:
            with open(path, "w") as fh:
                fh.write(data)

def random_string(length):
    chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    return ''.join([random.choice(chars) for i in range(length)])

def pickup(src_data, keys):
    if src_data is None:
        return None
    src_data2 = {}
    for key in keys:
        if dictlib_in(src_data, key):
            dictlib_put(src_data2, key, dictlib_get(src_data, key))
    return src_data2

def pickupAndCompareForUpdate(src_data, curr_data, keys):
    src_data2 = {}
    curr_data2 = {}
    for key in keys:
        if dictlib_in(src_data, key):
            dictlib_put(src_data2, key, dictlib_get(src_data, key))
        if dictlib_in(curr_data, key):
            dictlib_put(curr_data2, key, dictlib_get(curr_data, key))
    if src_data2 == curr_data2:
        return None
    return src_data2

def dictlib_in(data, key):
    idx = key.find(".")
    if idx < 0:
        if key in data:
            return True
        else:
            return False
    key2 = key[0:idx]
    if not key2 in data:
        return False
    return dictlib_in(data[key2], key[idx+1:])

def dictlib_get(data, key):
    idx = key.find(".")
    if idx < 0:
        if key in data:
            return data[key]
        else:
            return None
    key2 = key[0:idx]
    if not key2 in data:
        return None
    return dictlib_get(data[key2], key[idx+1:])

def dictlib_put(data, key, value):
    idx = key.find(".")
    if idx < 0:
        data[key] = value
        return
    key2 = key[0:idx]
    if not key2 in data:
        data[key2] = {}
    dictlib_put(data[key2], key[idx+1:], value)

def dict_key_to_lower(info):
    ret = {}
    for key, value in info.items():
        key2 = key[0:1].lower() + key[1:]
        ret[key2] = value
    return ret

def dict_key_capitalize(info):
    ret = {}
    for key, value in info.items():
        key2 = key[0:1].title() + key[1:]
        ret[key2] = value
    return ret

def encode_key(key):
    s = key
    s = urllib.parse.quote(s)
    s = s.replace(".", "%2E")
    s = s.replace("/", "%2F")
    s = s.replace("~", "%7E")
    return s

def decode_key(key):
    s = key
    s = s.replace("%2E", ".")
    s = s.replace("%2F", "/")
    s = s.replace("%7E", "~")
    s = urllib.parse.unquote(s)
    return s

def encode_tags(tags):
    ret = []
    for key, value in tags.items():
        ret.append({"Key": key, "Value": value})
    return ret

def decode_tags(tags):
    ret = {}
    for elem in tags:
        ret[elem["Key"]] = elem["Value"]
    return ret

