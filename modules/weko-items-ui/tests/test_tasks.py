import pytest
import json
from mock import MagicMock, patch ,sentinel
from invenio_pidstore.models import PersistentIdentifier
from weko_items_ui.models import CRIS_Institutions, CRISLinkageResult, LinkageItems
from weko_items_ui.tasks import build_achievement, build_one_data, bulk_post_item_to_researchmap, get_achievement_type, get_merge_mode, parse_bulk_result, process_researchmap_queue ,get_item,is_public, register_linkage_result,get_authors, sync_item_to_researchmap, update_linkage_by_authors
from weko_records.api import Mapping
from weko_records.models import ItemMetadata, ItemTypeMapping
from weko_records.utils import json_loader

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_bulk_post_item_to_researchmap -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_bulk_post_item_to_researchmap(app):
    with patch('weko_items_ui.tasks.process_researchmap_queue' , return_value = ""):
        with patch('weko_items_ui.tasks.current_celery_app' , return_value = MagicMock()):
            with patch('weko_items_ui.tasks.current_app' , return_value = MagicMock()):
                message = MagicMock()
                with patch('weko_items_ui.tasks.Consumer.iterqueue' , return_value = [message, None]):
                        bulk_post_item_to_researchmap()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_process_researchmap_queue -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_process_researchmap_queue(app ,db, db_records_researchmap):
    # item = ItemsMetadata.create(db_records[0][0].object_uuid, id_=rec_uuid)
    db.session.commit()
    # process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
    with patch('weko_items_ui.tasks.CRISLinkageResult.register_linkage_result' , return_value = True):
        with patch('weko_items_ui.tasks.PersistentIdentifier.get_by_object' , side_effect = [Exception(),MagicMock()]):
            process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
        with patch('weko_items_ui.tasks.json_loader' , side_effect = Exception()):
            process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
        with patch('weko_items_ui.tasks.is_public' , return_value = False):
            process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
        with patch('weko_items_ui.tasks.is_public' , return_value = True):
            with patch('weko_items_ui.tasks.get_authors' , return_value = []):
                process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
            with patch('weko_items_ui.tasks.get_authors' , return_value = ["auth1","auth2"]):
                with patch('weko_items_ui.tasks.get_achievement_type' , return_value = {}):
                    process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())
                with patch('weko_items_ui.tasks.get_achievement_type' , return_value = {"hoge":"fuga"}):
                    with patch('weko_items_ui.tasks.build_achievement' , return_value = {}):
                        with patch('weko_items_ui.tasks.update_linkage_by_authors' , return_value = True):
                            with patch('weko_items_ui.tasks.sync_item_to_researchmap' , return_value = True):
                                process_researchmap_queue({"item_uuid" : db_records_researchmap[0]}  ,MagicMock())

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_update_linkage_by_authors -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_update_linkage_by_authors(app, db, db_records_researchmap, db_linkage_items):
    mock_pid = MagicMock()
    mock_pid.object_uuid = db_records_researchmap[0]
    with patch('weko_items_ui.tasks.get_record_without_version', return_value=mock_pid):
        # REGISTERED -> DELETED
        update_linkage_by_authors(db_records_researchmap[0], [])
        linkage_items = LinkageItems.get_by_item_id(db_records_researchmap[0], LinkageItems.ExternalSystem.RM)
        for linkage_item in linkage_items:
            assert linkage_item.status == LinkageItems.Status.DELETED
        
        # DELETED -> REGISTERED
        update_linkage_by_authors(db_records_researchmap[0], ["auth1"])
        linkage_item = LinkageItems.get_by_item_id(db_records_researchmap[0], LinkageItems.ExternalSystem.RM)
        for linkage_item in linkage_items:
            if linkage_item.permalink == "auth1":
                assert linkage_item.status == LinkageItems.Status.REGISTERED
            else:
                assert linkage_item.status == LinkageItems.Status.DELETED

        # permalink in authors, status already REGISTERED → inner if is False, no update
        update_linkage_by_authors(db_records_researchmap[0], ["auth1"])
        linkage_items_final = LinkageItems.get_by_item_id(db_records_researchmap[0], LinkageItems.ExternalSystem.RM)
        for item in linkage_items_final:
            if item.permalink == "auth1":
                assert item.status == LinkageItems.Status.REGISTERED

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_sync_item_to_researchmap -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_sync_item_to_researchmap(app, db, db_records_researchmap, db_linkage_items):
    mock_pid = MagicMock()
    mock_pid.object_uuid = db_records_researchmap[0]
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result' , return_value = True):
        with patch('weko_items_ui.tasks.get_record_without_version', return_value=mock_pid):
            with patch('weko_items_ui.tasks.Researchmap.post_data', return_value='{"url" : "hoge"}'):
                # No authors
                errors = []
                success = [{"code": 200, "id": "external_id_1"},]
                with patch('weko_items_ui.tasks.Researchmap.get_result',
                        side_effect=[
                            json.dumps({"errors": errors}),
                            json.dumps({"success": success}),
                        ]
                ):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=[],
                        should_create_if_not_found=False
                    )
                
                # No LinkageItems
                db_linkage_items[0].status = LinkageItems.Status.DELETED
                db_linkage_items[1].status = LinkageItems.Status.DELETED
                db.session.commit()
                with patch('weko_items_ui.tasks.Researchmap.get_result',
                        side_effect=[
                            json.dumps({"errors": [{"code": 404, "line": 1}]}),
                            json.dumps({"success": []}),
                        ]
                ):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=[],
                        should_create_if_not_found=False
                    )
                
                # No error and Success update, no recall
                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()
                errors = [{"code": 200}, {"code": 404, "line": 2},]
                success = [{"code": 200, "line": 1, "id": "external_id_1"},]
                with patch('weko_items_ui.tasks.Researchmap.get_result',
                        side_effect=[
                            json.dumps({"errors": errors}),
                            json.dumps({"success": success}),
                        ]
                ):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1', 'auth2'],
                        should_create_if_not_found=False
                    )
                
                # Error and recall(new register), no success
                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()
                errors = [{"code": 404, "line": 2},]
                success = [
                    {"code": 200, "line": 1, "id": "new_external_id"},
                ]
                with patch('weko_items_ui.tasks.Researchmap.get_result',
                        side_effect=[
                            json.dumps({"errors": errors}),
                            json.dumps({"success": []}),
                            json.dumps({"errors": []}),         # recall
                            json.dumps({"success": success}),   # recall
                        ]
                ):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1', 'auth2'],
                        should_create_if_not_found=True
                    )

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_sync_item_to_researchmap_with_concatenated_json_result -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_sync_item_to_researchmap_with_concatenated_json_result(app, db, db_records_researchmap, db_linkage_items):
    mock_pid = MagicMock()
    mock_pid.object_uuid = db_records_researchmap[0]
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result', return_value=True):
        with patch('weko_items_ui.tasks.get_record_without_version', return_value=mock_pid):
            with patch('weko_items_ui.tasks.Researchmap.post_data', return_value='{"url" : "hoge"}'):
                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()

                error_result = '\n'.join([
                    json.dumps({"errors": [{"code": 404, "line": 2}]}),
                    json.dumps({"errors": [{"code": 200}]})
                ])
                success_result = '\n'.join([
                    json.dumps({"success": [{"code": 200, "line": 1, "id": "external_id_1"}]}),
                    json.dumps({"success": []})
                ])

                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[error_result, success_result]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1', 'auth2'],
                        should_create_if_not_found=False
                    )

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_sync_item_to_researchmap_ndjson -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_sync_item_to_researchmap_ndjson(app, db, db_records_researchmap, db_linkage_items):
    mock_pid = MagicMock()
    mock_pid.object_uuid = db_records_researchmap[0]
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result', return_value=True):
        with patch('weko_items_ui.tasks.get_record_without_version', return_value=mock_pid):
            with patch('weko_items_ui.tasks.Researchmap.post_data', return_value='{"url": "hoge"}'):
                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()
                summary_line = '{"code":200,"status":"completion"}'

                # error record with no "line" field → line is None
                error_no_line = summary_line + '\n' + json.dumps({"code": 404})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[error_no_line, summary_line]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                # error record with non-404 code
                error_non_404 = summary_line + '\n' + json.dumps({"line": 1, "code": 500})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[error_non_404, summary_line]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                # success record with no "line" field → line is None
                success_no_line = summary_line + '\n' + json.dumps({"code": 200, "id": "xyz"})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[summary_line, success_no_line]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                # success line number does not match any linkage target
                success_unmatched = summary_line + '\n' + json.dumps({"line": 99, "code": 200, "id": "new_id"})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[summary_line, success_unmatched]):
                    with patch('weko_items_ui.tasks.LinkageItems.get_by_external_item_id', return_value=[MagicMock()]):
                        sync_item_to_researchmap(
                            pid_int=1,
                            item_id=db_records_researchmap[0],
                            achievements_obj={},
                            merge_mode='merge',
                            achievement_type='published_papers',
                            authors=['auth1'],
                            should_create_if_not_found=False
                        )

                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()

                # error with line and code=404, linkage target matches, should_create_if_not_found=False
                error_404_matched = summary_line + '\n' + json.dumps({"line": 1, "code": 404})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[error_404_matched, summary_line]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()

                # error with line and code=404, no matching linkage target (line mismatch)
                error_404_unmatched = summary_line + '\n' + json.dumps({"line": 99, "code": 404})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[error_404_unmatched, summary_line]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()

                # error with line and code=404, should_create_if_not_found=True → recall and recursive call
                error_404_recall = summary_line + '\n' + json.dumps({"line": 1, "code": 404})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[
                    error_404_recall, summary_line,  # first call
                    summary_line, summary_line,      # recursive call
                ]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=True
                    )

                db_linkage_items[0].status = LinkageItems.Status.REGISTERED
                db_linkage_items[1].status = LinkageItems.Status.REGISTERED
                db.session.commit()

                # success with line matching target and id matching external_item_id → exists=True
                success_id_matched = summary_line + '\n' + json.dumps({"line": 1, "code": 200, "id": "external_id_1"})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[summary_line, success_id_matched]):
                    sync_item_to_researchmap(
                        pid_int=1,
                        item_id=db_records_researchmap[0],
                        achievements_obj={},
                        merge_mode='merge',
                        achievement_type='published_papers',
                        authors=['auth1'],
                        should_create_if_not_found=False
                    )

                # success with line matching but id not matching, no existing linkage → LinkageItems.create called
                success_new_id = summary_line + '\n' + json.dumps({"line": 1, "code": 200, "id": "brand_new_id"})
                with patch('weko_items_ui.tasks.Researchmap.get_result', side_effect=[summary_line, success_new_id]):
                    with patch('weko_items_ui.tasks.LinkageItems.get_by_external_item_id', return_value=[]):
                        with patch('weko_items_ui.tasks.LinkageItems.create', return_value=MagicMock()):
                            sync_item_to_researchmap(
                                pid_int=1,
                                item_id=db_records_researchmap[0],
                                achievements_obj={},
                                merge_mode='merge',
                                achievement_type='published_papers',
                                authors=['auth1'],
                                should_create_if_not_found=False
                            )

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_parse_bulk_result -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_parse_bulk_result():
    parsed = parse_bulk_result('')
    assert parsed == []

    payload = '\n'.join([
        json.dumps({"code": 999, "status": "completion"}),
        json.dumps({"line": 2, "code": 200, "id": "x"}),
        json.dumps({"line": 3, "code": 500}),
    ])
    parsed = parse_bulk_result(payload)

    assert parsed == [
        {"line": 2, "code": 200, "id": "x"},
        {"line": 3, "code": 500},
    ]

    # The first line is ignored even if it is invalid JSON.
    payload = '\n'.join([
        'INVALID_SUMMARY_LINE',
        json.dumps({"line": 10, "code": 201, "id": "R0000123"}),
    ])
    parsed = parse_bulk_result(payload)
    assert parsed == [{"line": 10, "code": 201, "id": "R0000123"}]

    # blank line between data records is skipped
    payload_with_blank = '\n'.join([
        json.dumps({"code": 200, "status": "completion"}),
        '',
        json.dumps({"line": 2, "code": 201, "id": "y"}),
    ])
    parsed = parse_bulk_result(payload_with_blank)
    assert parsed == [{"line": 2, "code": 201, "id": "y"}]

    # invalid JSON on a data line is silently skipped
    payload_with_invalid = '\n'.join([
        json.dumps({"code": 200, "status": "completion"}),
        'INVALID_JSON_HERE',
        json.dumps({"line": 3, "code": 201, "id": "z"}),
    ])
    parsed = parse_bulk_result(payload_with_invalid)
    assert parsed == [{"line": 3, "code": 201, "id": "z"}]

    # non-dict JSON on a data line (e.g. list) is skipped
    payload_with_list = '\n'.join([
        json.dumps({"code": 200, "status": "completion"}),
        json.dumps([1, 2, 3]),
        json.dumps({"line": 4, "code": 201, "id": "w"}),
    ])
    parsed = parse_bulk_result(payload_with_list)
    assert parsed == [{"line": 4, "code": 201, "id": "w"}]


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_item -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_item(app , db_records):
    assert get_item(db_records[0][0].object_uuid)

def test_is_public():
    with patch('weko_items_ui.tasks.check_publish_status' , return_value = True):
        with patch('weko_items_ui.tasks.is_private_index' , return_value = False):
            assert is_public("hoge" , "") == True
    
        with patch('weko_items_ui.tasks.is_private_index' , return_value = True):
            assert is_public("hoge" , "") == False

    with patch('weko_items_ui.tasks.check_publish_status' , return_value = False):
        with patch('weko_items_ui.tasks.is_private_index' , return_value = True):
            assert is_public("hoge" , "") == False

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_authors -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp
def test_get_authors(db_author):
    data = [
        {"nameIdentifiers": [{"nameIdentifierScheme": "ORCID", "nameIdentifier": "0123"}]},
        {"nameIdentifiers": [{"nameIdentifierScheme": "ISNI", "nameIdentifier": "2345"}]},
        {"nameIdentifiers": [{"nameIdentifierScheme": "researchmap", "nameIdentifier": "4567"}]},
        {"nameIdentifiers": []},
        {},
        "text"
    ]
    assert get_authors(data) == ["4567"]

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_merge_mode -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_merge_mode(app ,db_admin_setting):
    assert get_merge_mode()
    with patch("weko_items_ui.tasks.AdminSettings.get" , return_value={}):
        assert get_merge_mode()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_get_achievement_type -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_get_achievement_type(app):
    assert get_achievement_type({"type" : ["article"]}) == 'published_papers'
    assert get_achievement_type({"type" : ["hoge"]}) == None

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_build_achievement -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items-ui/.tox/c1/tmp
def test_build_achievement(app, db_records_researchmap, es):
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[0]) 
    record,item = get_item(db_records_researchmap[0])
    # mapping = Mapping.get_record(item.item_type_id)
    mapping = ItemTypeMapping.query.filter(ItemTypeMapping.mapping != None).first().mapping
    #  db_itemtype_15["item_type_mapping"] 
    _ , jrc , _= json_loader(data=item.json ,pid=recid)
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[1]) 
    record,item = get_item(db_records_researchmap[1])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[2]) 
    record,item = get_item(db_records_researchmap[2])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers')
    assert build_achievement(record,item,recid,mapping,jrc, 'misc')
    assert build_achievement(record,item,recid,mapping,jrc, 'books_etc')
    assert build_achievement(record,item,recid,mapping,jrc, 'presentations')
    assert build_achievement(record,item,recid,mapping,jrc, 'works')
    assert build_achievement(record,item,recid,mapping,jrc, 'others')

    # err cases
    recid = PersistentIdentifier.get_by_object(pid_type='recid', object_type='rec', object_uuid=db_records_researchmap[3]) 
    record,item = get_item(db_records_researchmap[3])
    _ , jrc , _= json_loader(data=item.json ,pid=recid) 
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers') == {
        "ending_page": None, "languages": None, "number": None, "published_paper_type": "",
        "see_also": [{'@id': 'https://weko3.example.org/records/19', "label": "url"}],
        "starting_page": None, "total_page": None, "volume": None
    }
    
    app.config.update(WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS= [{ 'type' : 'hoge' , "rm_name" : 'paper_title', "jpcoar_name" : 'dc:title' , "weko_name" :"title"}])
    assert build_achievement(record,item,recid,mapping,jrc, 'published_papers') == {"see_also": [{"@id": "https://weko3.example.org/records/19", "label": "url"}]}



# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_build_one_data -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_build_one_data(app):
    assert build_one_data({"hoge" : "foo"} , 'merge' ,'author',"publish_papaers").get("merge") == {"hoge" : "foo"}
    assert build_one_data({"hoge" : "foo"} , 'force' ,'author',"publish_papaers").get("force") == {"hoge" : "foo"}
    assert build_one_data({} , 'similar_merge_similar_data' ,'author',"publish_papaers").get("priority") == "similar_data"
    assert build_one_data({} , 'similar_merge_input_data' ,'author',"publish_papaers").get("priority") == "input_data"
    assert {} == build_one_data({} , '' ,'author',"publish_papaers")
    assert build_one_data({"hoge" : "foo"} , 'merge' ,'author',"publish_papaers", [{},{"permalink": "author", "external_item_id": "1234"}]).get("insert") == {"type": "publish_papaers", "permalink": "author", "id": "1234"}

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_tasks.py::test_register_linkage_result -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_register_linkage_result(db,db_records):
    with patch('weko_items_ui.models.CRISLinkageResult.register_linkage_result' , return_value = True):
        assert register_linkage_result(db_records[0][0].pid_value , True , db_records[0][0].object_uuid, None )