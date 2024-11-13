#!/bin/bash

# 各コマンドを8時間（28800秒）のタイムアウトを設定して順番に実行する
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_api.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_api-10-28-v2sh.log
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_permissions.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_permissins-10-28-v2sh.log
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_rest-10-28-v2sh.log
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_utils-10-28-v2sh.log
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_views-10-28-v2sh.log
timeout 28800 .tox/c1/bin/pytest --cov=weko_items_ui tests/test_weko_items_ui.py -v -vv -s --cov-append --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace >> test_weko_items_ui-10-28-v2sh.log
