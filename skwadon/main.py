import datetime
from re import S
import sys
import yaml

import skwadon.aws as sic_aws
import skwadon.lib as sic_lib

def main():
    (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm) = parse_args()
    (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm) = check_args \
        (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm)
    exec_main \
        (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm)

# putアクションで --dry-run が指定されていなく、更新処理を実行することを示すフラグ
# バグにより意図せず更新処理してしまうのが怖いので、引き回しせずにグローバルで持つことにする
global_confirmation_flag = False

####################################################################################################
# パラメータ解釈
####################################################################################################

def parse_args():
    help_flag = False
    action = None # get, put, delete exec
    is_full = None
    is_diff = None
    is_completion = None
    type = None # aws
    profile = None
    path = None
    src_file = None
    is_inplace = False
    repeat_count = None
    is_dryrun = False
    confirm = None
    i = 1
    argCount = len(sys.argv)
    while i < argCount:
        a = sys.argv[i]
        i = i + 1
        if a == "--help":
            help_flag = True
        elif a == "--full":
            is_full = True
        elif a == "--diff":
            is_diff = True
        elif a == "--no-diff":
            is_diff = False
        elif a == "--profile":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            profile = sys.argv[i]
            i = i + 1
        elif a == "-p":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            path = sys.argv[i]
            i = i + 1
        elif a == "-s":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            src_file = sys.argv[i]
            i = i + 1
        elif a == "-i":
            is_inplace = True
        elif a == "--repeat":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            repeat_count = int(sys.argv[i])
            i = i + 1
        elif a == "--force":
            confirm = True
        elif a == "--dry-run":
            is_dryrun = True
        elif a == "--confirm":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            confirm = sys.argv[i]
            i = i + 1
        elif a.startswith("-"):
            raise Exception(f"Unknown option: {a}")
        elif action == None and a == "get":
            action = "get"
        elif action == None and a == "put":
            action = "put"
        elif action == None and a == "delete":
            action = "delete"
        elif a == "aws":
            type = "aws"
        elif type == "aws" and path == None and src_file == None:
            path = a
        elif type == None and path == None and src_file == None:
            src_file = a
        else:
            raise Exception(f"Unknown parameter: {a}")
    return (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm)

####################################################################################################
# パラメータの組み合わせチェック
####################################################################################################

def check_args(help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm):
    if path != None and type == None:
        raise Exception("-p option needs aws parameter")

    # pathが . で終わっている場合はその次に続く文字列候補を出力する
    if path != None and path.endswith("."):
        path = path[0:len(path) - 1]
        action = "get"
        is_full = False
        is_diff = False
        is_completion = True
        src_file = None
        is_inplace = False
        repeat_count = 1

    # actionの指定がない場合は get とみなす
    if action == None:
        action = "get"
        if repeat_count == None:
            if type == None and src_file == None:
                # 標準入力から取り込む場合はデフォルトは0
                repeat_count = 0
            else:
                repeat_count = 1

    # --repeat は get でのみ有効
    if action != "get":
        if repeat_count != None:
            raise Exception(f"put action must not have --repeat option")

    # --repeat は標準入力から取り込む場合を除いてデフォルト値1
    if repeat_count == None:
        repeat_count = 1

    # is_diffの指定がない場合のデフォルト値設定
    if action == "get":
        if is_diff == None:
            is_diff = False
    elif action == "put" or action == "delete":
        if is_diff and not is_dryrun and not confirm:
            # --diff が指定されていて --dry-run も --confirm もない場合は --dry-run とみなす
            is_dryrun = True
        if is_dryrun:
            if is_diff == None:
                is_diff = True
        else:
            # put実行では差分表示もフル表示もしない
            pass

    if action == "delete":
        if type == None:
            raise Exception(f"delete action needs aws parameter")
        if src_file != None:
            raise Exception(f"delete action must not have -s option")
        if path == None or path == "":
            raise Exception(f"delete action needs -p option")

    # 入力がない場合はエラー
    if type == None and src_file == None and sys.stdin.isatty():
        raise Exception(f"either aws parameter or -s must be expected")

    # ファイルでの入力の場合の出力は is_full のみ
    if type == None:
        is_full = True

    if is_inplace:
        if src_file == None:
            raise Exception("-i option needs -s option")
        if action != "get":
            raise Exception(f"{action} must not have -i option")
        if is_diff:
            raise Exception(f"only one of --diff and -i can be specified")

    if type != None:
        if path == None or path == "":
            path = []
        else:
            path = path.split(".")

    return (help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm)

####################################################################################################
# 実行
####################################################################################################

def exec_main(help_flag, action, is_full, is_diff, is_completion, type, profile, path, src_file, is_dryrun, is_inplace, repeat_count, confirm):
    global global_confirmation_flag
    confirmation_flag = False

    if action == "put" or action == "delete":
        if not is_dryrun:
            # putコマンドでは --confirm オプションをチェック
            if confirm == None:
                raise Exception("put action needs --dry-run or --confirm HHMM")
            if confirm != True:
                check_confirm(confirm)
            confirmation_flag = True
            global_confirmation_flag = True

    if path != None:
        # get aws -p ... < data.yml
        # put aws -p ... < data.yml
        # のパターン
        if action == "delete":
            data_put = None # 削除の意味
        else:
            data_put = load_simple(None)
        data0 = build_path_data_full(type, profile, path, data_put)
    else:
        data0 = load_yaml(src_file)

    if action == "delete":
        action = "put"

    data1 = do_actions(action, confirmation_flag, path, data0, repeat_count)

    if action == "put" and not is_dryrun:
        add_update_completion_message()

    if action == "get":
        r1 = data0 # src
        r2 = data1 # クラウド側
    elif action == "put":
        r1 = data1 # 更新前のクラウド側
        r2 = data0 # src

    if is_completion:
        output_completion(get_by_path(data1, path))
    elif action == "get":
        if is_full:
            if is_diff:
                diff_yaml(r1, r2)
            elif is_inplace:
                save_yaml(data1, src_file)
            else:
                save_yaml(data1, None)
        else:
            if is_diff:
                output_simple_diff(get_by_path(r1, path), get_by_path(r2, path))
            else:
                output_simple(get_by_path(data1, path))
    elif action == "put":
        if is_full:
            if is_diff:
                diff_yaml(r1, r2)
            else:
                pass
        else:
            if is_diff:
                output_simple_diff(get_by_path(r1, path), get_by_path(r2, path))
            else:
                pass

####################################################################################################

# --confirm の時間チェック
def check_confirm(confirm):
    now = datetime.datetime.now(datetime.timezone.utc)
    for i in range(3):
        time_str = (now + datetime.timedelta(minutes = i - 1)).isoformat()
        hm = time_str[11:13] + time_str[14:16]
        if hm == confirm:
            return True
    time_str = now.isoformat()
    hm = time_str[11:13] + time_str[14:16]
    raise Exception(f"put action needs --confirm {hm}")

# -p オプションからデータ作成
def build_path_data_full(type, profile, path, data_put):
    data0 = {
        "type": type,
        "profile": profile,
        "resources": build_path_data(path, data_put),
    }
    return data0

def build_path_data(path, data_put):
    data = data_put
    for elem in reversed(path):
        data1 = {}
        data1[elem] = data
        data = data1
    return data

# データから -p で指定された場所を抜き出す
def get_by_path(data, path):
    def sub(data):
        if path == None:
            result = data
        else:
            result = data["resources"]
            for elem in path:
                if not elem in result:
                    return None
                result = result[elem]
        return result
    if isinstance(data, list):
        result = []
        for elem in data:
            result.append(sub(elem))
    else:
        result = sub(data)
    return result

def load_yaml(src_file):
    if src_file:
        with open(src_file) as f:
            data = yaml.safe_load(f)
    elif sys.stdin.isatty():
        raise Exception(f"-s not specified")
    else:
        data = yaml.safe_load(sys.stdin)
    return data

def load_simple(src_file):
    if src_file:
        with open(src_file) as f:
            data_str = f.read()
    elif sys.stdin.isatty():
        return {}
    else:
        data_str = sys.stdin.read()
    data = yaml.safe_load(data_str)
    return data

def output_completion(result):
    if result == None:
        pass
    elif isinstance(result, dict):
        max_len = 0
        names = []
        for name, value in result.items():
            if len(name) > max_len:
                max_len = len(name)
            names.append(name)
        for name, msg in help_message.items():
            if name in names:
                continue
            if len(name) > max_len:
                max_len = len(name)
            names.append(name)
        for name in names:
            if name in help_message:
                msg = help_message[name]
            else:
                msg = ""
            if len(msg) > 0:
                padding = " " * (max_len - len(name))
                print(f"{name}{padding} : {msg}")
            else:
                print(f"{name}")
    elif isinstance(result, list):
        is_str_list = True
        for elem in result:
            if not isinstance(elem, str):
                is_str_list = False
                break
        if is_str_list:
            for name in result:
                print(name)

def output_simple(result):
    save_yaml(result, None)
    #if result == None:
    #    pass
    #elif isinstance(result, dict):
    #    is_simple = True
    #    for name, value in result.items():
    #        if value != {}:
    #            is_simple = False
    #    if is_simple:
    #        for name, value in result.items():
    #            print(name)
    #    else:
    #        save_yaml(result, None)
    #elif isinstance(result, list):
    #    is_str_list = True
    #    for elem in result:
    #        if not isinstance(elem, str):
    #            is_str_list = False
    #            break
    #    if is_str_list:
    #        for name in result:
    #            print(name)
    #    else:
    #        save_yaml(result, None)
    #elif isinstance(result, str):
    #    print(result)
    #elif isinstance(result, int):
    #    print(result)
    #else:
    #    save_yaml(result, None)

def output_simple_diff(result1, result2):
    if result1 == {} and (isinstance(result2, str) or isinstance(result2, int)):
        result1 = ""
    if (result1 == "" or isinstance(result1, str)) and isinstance(result2, str):
        sic_lib.exec_diff(result1, result2, None)
    elif (result1 == "" or isinstance(result1, int)) and isinstance(result2, int):
        sic_lib.exec_diff(str(result1), str(result2), None)
    else:
        diff_yaml(result1, result2)

def represent_str(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar('tag:yaml.org,2002:str', s, style='|')
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:str', s)

yaml.add_representer(str, represent_str)

def save_yaml(data, dst_file):
    yaml_str = yaml.dump(data, sort_keys = False, allow_unicode = True, width = 120, default_flow_style = False)
    if dst_file:
        with open(dst_file, "w") as f:
            f.write(yaml_str)
    else:
        sys.stdout.write(yaml_str)

def diff_yaml(src_data, dst_data):
    src_yaml_str = yaml.dump(src_data, sort_keys = False, allow_unicode = True, width = 120)
    dst_yaml_str = yaml.dump(dst_data, sort_keys = False, allow_unicode = True, width = 120)
    sic_lib.exec_diff(src_yaml_str, dst_yaml_str, None)

def do_actions(action, confirmation_flag, path, data0, repeat_count):
    data1 = data0
    for i in range(repeat_count):
        if isinstance(data1, list):
            data2 = []
            for elem in data1:
                r = do_action(action, confirmation_flag, path, elem)
                data2.append(r)
        else:
            data2 = do_action(action, confirmation_flag, path, data1)
        data1 = data2
    return data1

def do_action(action, confirmation_flag, path, src_data):
    global update_message_prefix
    if src_data["type"] == "aws":
        update_message_prefix = sic_aws.get_message_prefix(src_data)
        ret = sic_aws.do_action(action, confirmation_flag, path, src_data)
        update_message_prefix = None
        return ret
    else:
        return src_data

update_message_prefix = None
update_message = []

# 更新系APIコールの直前で呼ばれる
# --dry-run でも呼ばれる
def add_update_message(message):
    if update_message_prefix:
        message = f"{update_message_prefix}: {message}"
    else:
        message = f"{message}"
    #print(message, file = sys.stderr)
    print(message)
    update_message.append(message)

# 更新系の処理がすべて完了したら呼ばれる
# --dry-run では呼ばれない
def add_update_completion_message():
    if len(update_message) > 0:
        message = "complete put action"
        #print(message, file = sys.stderr)
        print(message)

help_message = {}

def put_help_message(key, message):
    help_message[key] = message
