import copy
import datetime
import sys
import yaml

import skwadon.lib as sic_lib
import skwadon.testcloud as testcloud
import skwadon.aws as sic_aws

####################################################################################################

def main():
    # interprete parameters
    (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm) = parse_args()

    # check parameters
    (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm) = check_args \
        (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm)

    # execution
    exec_main \
        (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm)

####################################################################################################
# interprete parameters
# パラメータ解釈
####################################################################################################

def parse_args():
    help_flag = False
    action = None # get, put, delete exec
    is_simple = None
    is_full = None
    is_diff = None
    is_completion = None
    thats_all_flag = False
    type = None # testcloud, aws
    profile = None
    path = []
    src_file = None
    is_inplace = False
    is_dryrun = False
    confirm = None
    i = 1
    argCount = len(sys.argv)
    while i < argCount:
        a = sys.argv[i]
        i = i + 1
        if a == "--help":
            # ヘルプはまだ実装していない
            help_flag = True
        elif a == "-r":
            is_simple = True
        elif a == "--full":
            is_full = True
        elif a == "--diff":
            is_diff = True
        elif a == "--thats-all":
            thats_all_flag = True
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
            path.append(sys.argv[i])
            i = i + 1
        elif a == "-s":
            if i >= argCount:
                raise Exception(f"Option parameter not found: {a}")
            src_file = sys.argv[i]
            i = i + 1
        elif a == "-i":
            is_inplace = True
        elif a == "--force":
            confirm = True
        elif a == "--dry-run":
            is_dryrun = True
        elif a == "--confirm":
            if i >= argCount:
                # エラーだけど
                # check_confirm で親切なエラーを出すためここではエラー扱いにしない
                confirm = ""
            else:
                confirm = sys.argv[i]
                i = i + 1
        elif a.startswith("-"):
            raise Exception(f"Unknown option: {a}")

        # actionはこの4種類
        elif action is None and a == "get":
            action = "get"
        elif action is None and a == "put":
            action = "put"
        elif action is None and a == "delete":
            action = "delete"
        elif action is None and a == "exec":
            action = "exec"

        # クラウド種類はいまのところこの2種類
        elif a == "testcloud":
            # skwadonテストコードのためのクラウド種類
            type = "testcloud"
        elif a == "aws":
            # AWS
            type = "aws"

        elif type and src_file is None:
            path.append(a)
        elif type is None and path is None and src_file is None:
            src_file = a

        else:
            raise Exception(f"Unknown parameter: {a}")

    return (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm)

####################################################################################################
# check parameters
# パラメータの組み合わせチェック
####################################################################################################

def check_args(help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm):
    if len(path) > 0 and type is None:
        raise Exception("-p option needs aws parameter")

    # pathが . で終わっている場合はその次に続く文字列候補を出力する
    if len(path) > 0 and path[len(path) - 1].endswith("."):
        last_path = path[len(path) - 1]
        path = [last_path[0:len(last_path) - 1]]
        action = "get"
        is_simple = False
        is_full = False
        is_diff = False
        is_completion = True
        thats_all_flag = False
        src_file = None
        is_inplace = False

    # pathが複数ある場合は --full とする
    if len(path) > 1:
        is_simple = False
        is_full = True

    if action == "put" and len(path) > 1:
        raise Exception("put action must have only one path")

    if action == "exec" and len(path) > 1:
        raise Exception("exec action must have only one path")
    if action == "exec" and len(path) == 0:
        raise Exception("exec action must have one path")

    # actionの指定がない場合は get とみなす
    if action is None:
        action = "get"
        if type is None and src_file is None:
            action = "cat"

    # is_diffの指定がない場合のデフォルト値設定
    if action == "get" or action == "cat":
        if is_diff is None:
            is_diff = False
    elif action == "put" or action == "delete":
        if is_diff and not is_dryrun and not confirm:
            # --diff が指定されていて --dry-run も --confirm もない場合は --dry-run とみなす
            is_dryrun = True
        if is_dryrun:
            if is_diff is None:
                is_diff = True
        else:
            # put実行では差分表示もフル表示もしない
            pass

    if action == "delete":
        if type is None:
            raise Exception(f"delete action needs aws parameter")
        if src_file is not None:
            raise Exception(f"delete action must not have -s option")
        if len(path) == 0:
            raise Exception(f"delete action needs -p option")

    # 入力がない場合はエラー
    if type is None and src_file is None and sys.stdin.isatty():
        raise Exception(f"either aws parameter or -s must be expected")

    # ファイルでの入力の場合の出力は is_full のみ
    if type is None:
        is_simple = False
        is_full = True

    if is_inplace:
        if src_file is None:
            raise Exception("-i option needs -s option")
        if action != "get" and action != "cat":
            raise Exception(f"{action} must not have -i option")
        if is_diff:
            raise Exception(f"only one of --diff and -i can be specified")

    if type is not None:
        path2 = []
        for p in path:
            if p == "":
                path2.append([])
            else:
                if p.endswith("."):
                    p = p[0:len(p)-1]
                path2.append(p.split("."))
        if len(path) == 0 and src_file is None:
            path2.append([])
        path = path2

    return (help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm)

####################################################################################################
# execution
# 実行
####################################################################################################

def exec_main(help_flag, action, is_simple, is_full, is_diff, is_completion, thats_all_flag, type, profile, path, src_file, is_dryrun, is_inplace, confirm):
    global global_confirmation_flag
    confirmation_flag = False

    if action == "put" or action == "delete":
        if not is_dryrun:
            # putコマンドでは --confirm オプションをチェック
            if confirm is None:
                hm = get_correct_confirm_parameter()
                raise Exception(f"put action needs --dry-run or --confirm {hm}")
            if confirm != True:
                check_confirm(confirm)
            confirmation_flag = True
            global_confirmation_flag = True

    if type is not None:
        # get aws -p ... < data.yml
        # put aws -p ... < data.yml
        # のパターン
        if action == "delete":
            data_put = None # 削除の意味
        elif action == "exec":
            data_put = None
        elif action == "put":
            data_put = load_simple(src_file, {})
            # 標準入力がない場合は {} になる
        else:
            data_put = load_simple(src_file, None)
            # 標準入力がない場合は null になる
        data0 = build_path_data_full(type, profile, path, data_put)
    else:
        data0 = load_yaml(src_file)

    if action == "delete":
        action = "put"

    if action == "cat":
        data1 = data0
        r1 = data0
        r2 = data1
        action = "get"
    elif action == "get":
        data1 = do_get_n(data0, thats_all_flag)
        r1 = data0 # src
        r2 = data1 # クラウド側
    elif action == "put":
        data0, data1 = do_put_n(confirmation_flag, data0)
        r1 = data1 # 更新前のクラウド側
        r2 = data0 # srcまたは更新後
        if confirmation_flag:
            add_update_completion_message()
    elif action == "exec":
        do_exec(data0)

    if action == "exec":
        pass # ここでは出力制御しない
    elif is_completion:
        output_completion(get_by_path(data1, path))
    elif action == "get":
        if is_full:
            if is_diff:
                diff_yaml(r1, r2)
            elif is_inplace:
                save_yaml(data1, src_file)
            else:
                save_yaml(data1, None)
        elif is_simple:
            if is_diff:
                output_simple_diff(get_by_path(r1, path), get_by_path(r2, path))
            else:
                output_simple(get_by_path(data1, path))
        else:
            if is_diff:
                diff_yaml(get_by_path(r1, path), get_by_path(r2, path))
            else:
                save_yaml(get_by_path(data1, path), None)
    elif action == "put":
        if is_full:
            if is_diff:
                diff_yaml(r1, r2)
            else:
                pass
        elif is_simple:
            if is_diff:
                output_simple_diff(get_by_path(r1, path), get_by_path(r2, path))
            else:
                pass
        else:
            if is_diff:
                diff_yaml(get_by_path(r1, path), get_by_path(r2, path))
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
    hm = get_correct_confirm_parameter()
    raise Exception(f"put action needs --confirm {hm}")

def get_correct_confirm_parameter():
    now = datetime.datetime.now(datetime.timezone.utc)
    time_str = now.isoformat()
    return time_str[11:13] + time_str[14:16]

####################################################################################################

# -p オプションからデータ作成
def build_path_data_full(type, profile, path, data_put):
    data0 = {}
    data0["type"] = type
    if profile:
        data0["profile"] = profile
    data0["resources"] = build_path_data(path, data_put)
    return data0

def build_path_data(path, data_put):
    def merge(d1, d2):
        if not isinstance(d1, dict) or not isinstance(d2, dict):
            return d2
        result = {}
        for k in d1:
            if k in d2:
                result[k] = merge(d1[k], d2[k])
            else:
                result[k] = d1[k]
        for k in d2:
            if not k in d1:
                result[k] = d2[k]
        return result
    data = {}
    for p in path:
        d = build_path_data_one(p, copy.copy(data_put))
        data = merge(data, d)
    return data

def build_path_data_one(path, data_put):
    data = data_put
    for elem in reversed(path):
        data1 = {}
        data1[elem] = data
        data = data1
    return data

# データから -p で指定された場所を抜き出す
def get_by_path(data, path):
    if len(path) != 1:
        return data
    path = path[0]
    if "*" in path:
        return data
    def sub(data):
        if path is None:
            result = data
        else:
            result = data["resources"]
            for elem in path:
                if result is None:
                    return None
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
        #raise Exception(f"-s not specified")
        data = {}
    else:
        data = yaml.safe_load(sys.stdin)
    return data

def load_simple(src_file, default):
    if src_file:
        with open(src_file) as f:
            data_str = f.read()
    elif sys.stdin.isatty():
        return default
    else:
        data_str = sys.stdin.read()
    data = yaml.safe_load(data_str)
    return data

####################################################################################################

def output_completion(result):
    if result is None:
        pass
    elif isinstance(result, dict):
        max_len = 0
        names = []
        for name, value in result.items():
            if name == "*":
                continue
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
    if result is None:
        pass
    elif isinstance(result, dict):
        is_simple = True
        for name, value in result.items():
            if value != {}:
                is_simple = False
        if is_simple:
            for name, value in result.items():
                print(name)
        else:
            save_yaml(result, None)
    elif isinstance(result, list):
        is_str_list = True
        for elem in result:
            if not isinstance(elem, str):
                is_str_list = False
                break
        if is_str_list:
            for name in result:
                print(name)
        else:
            save_yaml(result, None)
    elif isinstance(result, str):
        print(result)
    elif isinstance(result, int):
        print(result)
    else:
        save_yaml(result, None)

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

####################################################################################################

def do_get_n(data0, thats_all_flag):
    data1 = data0
    if isinstance(data1, list):
        data2 = []
        for elem in data1:
            r = do_get(elem, thats_all_flag)
            data2.append(r)
    else:
        data2 = do_get(data1, thats_all_flag)
    return data2

def do_get(src_data, thats_all_flag):
    global update_message_prefix
    result = src_data
    if src_data["type"] == "testcloud":
        handler = testcloud.get_handler(src_data)
        result = copy.copy(src_data)
        if "resources" in src_data:
            result["resources"] = handler.do_get(src_data["resources"], thats_all_flag)
    elif src_data["type"] == "aws":
        handler = sic_aws.get_handler(src_data)
        result = copy.copy(src_data)
        if "resources" in src_data:
            result["resources"] = handler.do_get(src_data["resources"], thats_all_flag)
    return result

def do_put_n(confirmation_flag, data0):
    if isinstance(data0, list):
        data1 = []
        data2 = []
        for elem in data0:
            d1, d2 = do_put(confirmation_flag, elem)
            data1.append(d1)
            data2.append(d2)
    else:
        data1, data2 = do_put(confirmation_flag, data0)
    return (data1, data2)

def do_put(confirmation_flag, src_data):
    global update_message_prefix
    mod = None
    if src_data["type"] == "testcloud":
        mod = testcloud
    elif src_data["type"] == "aws":
        mod = sic_aws
    if mod:
        update_message_prefix = mod.get_message_prefix(src_data)
        handler = mod.get_handler(src_data)
        data1 = copy.copy(src_data)
        data2 = copy.copy(src_data)
        if "resources" in src_data:
            d1, d2 = handler.do_put(confirmation_flag, src_data["resources"])
            data1["resources"] = d1
            data2["resources"] = d2
        update_message_prefix = None
        return (data1, data2)
    else:
        return (src_data, src_data)

def do_exec(src_data):
    mod = None
    if src_data["type"] == "testcloud":
        mod = testcloud
    elif src_data["type"] == "aws":
        mod = sic_aws
    if mod:
        handler = mod.get_handler(src_data)
        if "resources" in src_data:
            raise Exception("TODO")
            #handler.do_exec(src_data["resources"])

####################################################################################################

# boto3で変更のAPIリクエストを実行する際には必ずこのメソッドを通すこと
# dryrunでも通す
# dryrunかどうかはconfirmation_flagで判定
def exec_put(confirmation_flag, message, executor):
    add_update_message(message)
    if confirmation_flag and global_confirmation_flag:
        executor()

# putアクションで --dry-run が指定されていなく、更新処理を実行することを示すフラグ
# バグにより意図せず更新処理してしまうのが怖いので、引き回しせずにグローバルで持つことにする
global_confirmation_flag = False

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

####################################################################################################
