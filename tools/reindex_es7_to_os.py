import sys
import argparse
import os
import requests
from requests.auth import HTTPBasicAuth
from importlib import import_module
import re
import json
from datetime import datetime, timedelta, timezone
import traceback, copy
import time

now = datetime.now(timezone.utc)
today_str = now.strftime("%Y-%m-%dT00:00:00")

def validate_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%dT00:00:00")
    except ValueError:
        raise argparse.ArgumentTypeError(f"無効な日付形式: {date_str}（YYYY-MM-DD の形式で入力してください）")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Elasticsearch es v7 から os に reindex するツール",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "http_method",
        choices=["http", "https"],
        help="Elasticsearch に接続するプロトコル（http または https）"
    )

    parser.add_argument(
        "--es7_host",
        type=str,
        default="elasticsearch7",
        help="Elasticsearch 7 のコンテナ名"
    )
    
    parser.add_argument(
        "--es7_port",
        type=str,
        default="9200",
        help="Elasticsearch 7 のポート番号（デフォルト: 9200）"
    )
    
    parser.add_argument(
        "--os_host",
        type=str,
        default="opensearch",
        help="Opensearch のコンテナ名"
    )
    
    parser.add_argument(
        "--os_port",
        type=str,
        default="9200",
        help="opensearch のポート番号（デフォルト: 9200）"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        help="Elasticsearch のユーザー名"
    )

    parser.add_argument(
        "--password",
        type=str,
        help="Elasticsearch のパスワード"
    )
    parser.add_argument(
        "--user_os",
        type=str,
        default="admin",
        help="Opensearch のユーザー名"
    )

    parser.add_argument(
        "--password_os",
        type=str,
        default="WekoOpensearch123!",
        help="Opensearch のパスワード"
    )

    parser.add_argument(
        "--date",
        type=validate_date,
        default=None,
        help="操作する日付（省略可能）\n"
             "  ・日付なしで実行すると、前日23:59:59までのデータがreindexされる\n"
             "  ・日付付きで実行すると、指定した日の23:59:59までのデータがreindexされる\n"
             "  ・形式: YYYY-MM-DD（例: 2024-02-14）"
    )

    args = parser.parse_args()
    return args

args = parse_arguments()
http_method = args.http_method
user = args.user
password = args.password
user_os = args.user_os
password_os = args.password_os
es7_host = args.es7_host
es7_port = args.es7_port
os_host = args.os_host
os_port = args.os_port
gte_date = args.date
es_auth = HTTPBasicAuth(user, password) if user and password else None
os_auth = HTTPBasicAuth(user_os, password_os) if user_os and password_os else None
version="os-v2"

es7_url = http_method + "://"+ es7_host +":"+es7_port+"/"
os_url = "https://"+os_host+":"+os_port+"/"
reindex_url = os_url + "_reindex?pretty&refresh=true&wait_for_completion=true"
template_url = os_url + "_template/{}"
verify=False
headers = {"Content-Type":"application/json"}

req_args = {"headers":headers,"verify":verify}
os_req_args = {"headers":headers,"verify":verify}


if es_auth:
    req_args["auth"] = es_auth
if os_auth:
    os_req_args["auth"] = os_auth


mapping_files = {
    "authors-author-v1.0.0": f"weko-authors/weko_authors/mappings/{version}/authors/author-v1.0.0.json",
    "weko-item-v1.0.0": f"weko-schema-ui/weko_schema_ui/mappings/{version}/weko/item-v1.0.0.json",
}
template_files = {
    "events-stats-index": f"invenio-stats/invenio_stats/contrib/events/{version}/events-v1.json",
    "stats-index": f"invenio-stats/invenio_stats/contrib/aggregations/{version}/aggregation-v1.json",
}
stats_indexes = ["events-stats-celery-task", "events-stats-file-download", "events-stats-file-preview", "events-stats-item-create", "events-stats-record-view", "events-stats-search", "events-stats-top-view", "stats-celery-task", "stats-file-download", "stats-file-preview", "stats-item-create", "stats-record-view", "stats-search", "stats-top-view"]


prefix = os.environ.get('SEARCH_INDEX_PREFIX')

def replace_prefix_index(index_name):
    index_tmp = re.sub(f"^{prefix}-", "", index_name)
    index_tmp = re.sub("-\d{6}$","",index_tmp)
    return index_tmp

# indexとalias一覧取得
print("# get indexes and aliases")
organization_aliases = prefix+"-*"
indexes = requests.get(f"{es7_url}{organization_aliases}",**req_args).json()
indexes_alias = {} # indexとaliasのリスト
es7_mappings_cache = {} # 冒頭取得済みのES7 mappingキャッシュ
for index in indexes:
    aliases = indexes[index].get("aliases",{})
    indexes_alias[index] = aliases
    es7_mappings_cache[index] = indexes[index].get("mappings", {})

modules_dir = "/code/modules/"
mappings = {}
templates = {}

def wait_for_shards_started(index_name, timeout=120):
    """cluster health API で primary shard active かつ cluster state 確定を保証する。"""
    res = requests.get(
        os_url + f"/_cluster/health/{index_name}"
        f"?wait_for_status=yellow&wait_for_active_shards=1&timeout={timeout}s",
        **os_req_args
    )
    if res.status_code != 200 or res.json().get("timed_out"):
        raise Exception(f"Timeout waiting for index to be ready: {index_name}")

def _deep_merge_props(dst, src):
    """ES7 properties を dst へ再帰的にマージする（dst に無いキーのみ追加）。"""
    for field, field_def in src.items():
        if field not in dst:
            dst[field] = field_def
        elif isinstance(field_def, dict) and "properties" in field_def:
            dst[field].setdefault("properties", {})
            _deep_merge_props(dst[field]["properties"], field_def["properties"])

def merge_es7_mapping(index_name, base_definition):
    """冒頭取得済みの ES7 mapping から不足フィールドを全階層でマージする。"""
    es7_mappings = es7_mappings_cache.get(index_name, {})
    if not es7_mappings:
        print(f"## warn: no ES7 mapping cached for {index_name}, skipping merge")
        return base_definition

    if "properties" in es7_mappings:
        es7_props = es7_mappings["properties"]
    else:
        first_type = next(iter(es7_mappings), None)
        es7_props = es7_mappings[first_type].get("properties", {}) if first_type else {}

    base_props = base_definition.setdefault("mappings", {}).setdefault("properties", {})
    before_keys = set(base_props.keys())
    _deep_merge_props(base_props, es7_props)
    added = [k for k in base_props if k not in before_keys]
    print(f"## merged ES7 mapping (top-level added: {len(added)}): {added}")
    return base_definition

had_errors = False

# ファイルからマッピングデータを取得
print("# get mapping from json file")
for index in indexes_alias:
    index_tmp = replace_prefix_index(index)
    if index_tmp in stats_indexes:
        continue
    if index_tmp not in list(mapping_files.keys()):
        print("## not exists: {}, {}".format(index, index_tmp))
        continue
    path_data = mapping_files[index_tmp]
    file_path = os.path.join(modules_dir, path_data)

    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue

    with open(file_path, "r") as json_file:
        mappings[index] = json.loads(json_file.read())

print("# get template from json files")
for index, path in template_files.items():
    file_path = os.path.join(modules_dir, path)
    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue
    with open(file_path, "r") as json_file:
        templates[index] = json.loads(
            json_file.read().\
                replace("__SEARCH_INDEX_PREFIX__",prefix+"-")
        )


percolator_body = {"properties": {"query": {"type": "percolator"}}}
# for index in indexes_alias:
for index, mapping in mappings.items():
    print("# start reindex: {}".format(index))

    # target index mapping
    base_index_definition = mappings[index]

    # create speed up setting body
    defalut_number_of_replicas = base_index_definition.get("settings",{}).get("index",{}).get("number_of_replicas",1)
    default_refresh_interval = base_index_definition.get("settings",{}).get("index",{}).get("refresh_interval","1s")
    performance_setting_body = {"index": {"number_of_replicas": 0, "refresh_interval": "-1"}}
    restore_setting_body = {"index": {"number_of_replicas": defalut_number_of_replicas, "refresh_interval": default_refresh_interval}}

    remote = {"host": es7_url}
    if user and password:
        remote["username"] = user
        remote["password"] = password

    json_data_to_os = {
        "source": {
            "remote": remote,
            "index": index,
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                }
            }
        },
        "dest": {
            "index": index
        }
    }

    query_after_specific_date  = {
        "range": {
            "_updated": {
                "gte": gte_date
            }
        }
    }


    # body for setting alias
    json_data_set_aliases = {
        "actions":[]
    }
    for alias in indexes_alias[index]:
        alias_info = {"index": index, "alias": alias}
        if "is_write_index" in indexes_alias[index][alias]:
            alias_info["is_write_index"] = indexes_alias[index][alias]["is_write_index"]
        json_data_set_aliases["actions"].append({"add":alias_info})

    try:
        # インデックスがなかったら作る
        res = requests.get(os_url + index, **os_req_args)
        if res.status_code == 200:
            print(f"## Index {index} already exists, skipping creation.")
        else:
            print(f"## Creating index: {index}")
            base_index_definition = merge_es7_mapping(index, base_index_definition)
            res = requests.put(os_url + index + "?pretty", json=base_index_definition, **os_req_args)
            if res.status_code != 200:
                raise Exception(res.text)
            print(f"## Created index: {index}")


            if json_data_set_aliases["actions"]:
                res = requests.post(os_url + "_aliases", json=json_data_set_aliases, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
            print("## setting alias for new index")


        index_percolator = index + "-percolator"

        # percolatorがなかったら作る
        res = requests.get(os_url + index_percolator, **os_req_args)
        if res.status_code == 200:
            print(f"## Index {index_percolator} already exists, skipping creation.")
        else:
            print(f"## Creating index: {index_percolator}")
            percolator_definition = copy.deepcopy(base_index_definition)
            percolator_definition["mappings"]["properties"].update(percolator_body["properties"])
            res = requests.put(os_url + index_percolator + "?pretty", json=percolator_definition, **os_req_args)
            if res.status_code != 200:
                raise Exception(res.text)
            print(f"## Created index: {index_percolator}")

        res = requests.put(os_url + index + "/_settings?pretty", json=performance_setting_body, **os_req_args)
        if res.status_code != 200:
            raise Exception(res.text)
        print("## speed-up setting for reindex")
        wait_for_shards_started(index)
        print("## shard ready")


        if "author" not in index:
            if gte_date:
                json_data_to_os["source"]["query"]["bool"]["must"] = [query_after_specific_date]
                print(f"## start reindex {index} (>= today 00:00:00)")
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                print(f"## end reindex {index} (>= today 00:00:00)")
                json_data_to_os["source"]["query"]["bool"]["must"] = []
                json_data_to_os["dest"]["index"] = index_percolator
                json_data_to_os["source"]["index"] = index_percolator
                print(f"## start reindex {index_percolator} (>= today 00:00:00)")
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                print(f"## end reindex {index_percolator} (>= today 00:00:00)")
            else:
                print(f"## start reindex {index} (<= yesterday 23:59:59)")
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                print(f"## end reindex {index} (<= yesterday 23:59:59)")
                json_data_to_os["dest"]["index"] = index_percolator
                json_data_to_os["source"]["index"] = index_percolator
                print(f"## start reindex {index_percolator} (<= yesterday 23:59:59)")
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                print(f"## end reindex {index_percolator} (<= yesterday 23:59:59)")
        else:
            if gte_date:
                print(f"## start reindex {index} all")
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                json_data_to_os["dest"]["index"] = index_percolator
                json_data_to_os["source"]["index"] = index_percolator
                res = requests.post(url=reindex_url, json=json_data_to_os, **os_req_args)
                if res.status_code != 200:
                    raise Exception(res.text)
                print(f"## end reindex {index} all")
            else:
                print(f"## {index} Reindex next time")

        res = requests.put(os_url + index + "/_settings?pretty", json=restore_setting_body, **os_req_args)
        if res.status_code != 200:
            raise Exception(res.text)
        print(f"## reset speed-up setting")
        print("# end reindex: {}\n".format(index))
    except Exception as e:
        had_errors = True
        print("##raise error: {}".format(index))
        print(traceback.format_exc())

stats_indexes = ["events-stats-index", "stats-index"]

def stats_reindex(index_name):
    # テンプレート登録
    filename_without_ext = template_files[index_name].split("/")[-1].replace(".json","")
    template_name = f"{prefix}-{filename_without_ext}"
    template_url_event_stats = template_url.format(template_name)
    res = requests.put(template_url_event_stats,json=templates[index_name],**os_req_args)
    if res.status_code!=200:
        print("### raise error: put template")
        raise Exception(res.text)
    # 対象のインデックスのリストを取得
    index_perttern = f"{prefix}-{index_name}-*"

    indexes = requests.get(f"{es7_url}{index_perttern}",**req_args).json()
    for index in indexes:
        # ないなら作成。
        res = requests.get(os_url + index, **os_req_args)
        if res.status_code == 200:
            print(f"## Index {index} already exists, skipping creation.")
        else:
            print(f"## craete index: {index}")
            res = requests.put(os_url+index+"?pretty",**os_req_args)
            if res.status_code!=200:
                print("## raise error: create index")
                raise Exception(res.text)
            alias = f"{prefix}-{index_name}"
            # エイリアスを設定
            alias_actions = [
                {
                    "add": {
                        "index": index,
                        "alias": alias,
                        "is_write_index": indexes[index].get("aliases",{}).get(alias,{}).get("is_write_index",False)
                    }
                }
            ]
            res = requests.post(os_url+"_aliases",json={"actions":alias_actions},**os_req_args)
            if res.status_code!=200:
                print("## raise error: put aliases")
                raise Exception(res.text)
        # リインデックス
        remote = {"host": es7_url}
        if user and password:
            remote["username"] = user
            remote["password"] = password

        if gte_date:
            source_index = {
                "remote": remote,
                "index": index,
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": gte_date
                        }
                    }
                }
            }
        else:
            source_index = {
                "remote": remote,
                "index": index,
            }

        body = {
            "source": source_index,
            "dest": {
                "index": index
            }
        }
        print(f"## start reindex {index}")
        res = requests.post(url=reindex_url, json=body, **os_req_args)
        if res.status_code != 200:
            print(f"## raise error: reindex: {index}")
            raise Exception(res.text)
        print(f"## end reindex {index}")
for stats_index in stats_indexes:
    stats_reindex(stats_index)

if had_errors:
    print("## Completed with errors")
    sys.exit(1)
