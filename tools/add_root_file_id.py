
import os

from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_search.engine import search

open_search = search.OpenSearch(
        "http://" + os.environ.get("INVENIO_ELASTICSEARCH_HOST", "localhost") + ":9200"
    )

    
def add_root_file_id(index):
    errors = []
    updated = []
    # root_file_id が null または "" となっている文書を探す
    _query = '{"query":{"bool":{"should":[{"bool":{"must_not":{"exists":{"field":"root_file_id"}}}},{"bool":{"must":[{"exists":{"field":"root_file_id"}}],"must_not":[{"wildcard":{"root_file_id":"*"}}]}}]}}}'
    results = search.helpers.scan(
            open_search,
            index=index,
            preserve_order=True,
            query=_query,
        )
    _bulk = []
    for r in results:
        id = r['_id']
        source = r.get('_source')
        _index = r.get('_index')
        _type = r.get('_type')
        _body = {"root_file_id": source['file_id']}
        with db.session.begin_nested():
            file = None
            # file_idが存在する場合はそこからroot_file_idの取得を試みる
            if "file_id" in source and source['file_id'] is not None and source['file_id'] is not "":
                file = ObjectVersion.query.filter_by(file_id=source["file_id"]).order_by(ObjectVersion.updated.desc()).first() 
            # file_idがなく、file_keyが存在する場合はそこからroot_file_idの取得を試みる
            elif "file_key" in source and source['file_key'] is not None and source['file_key'] is not "":
                file = ObjectVersion.query.filter_by(key=source["file_key"],bucket_id=source["bucket_id"]).order_by(ObjectVersion.updated.desc()).first() 
            # file_idもfile_keyも存在ない場合はbucket_idからroot_file_idの取得を試みる
            else:
                file = ObjectVersion.query.filter_by(bucket_id=source["bucket_id"]).order_by(ObjectVersion.updated.desc()).first() 
            
            # fileオブジェクトが取得でき、root_file_idが取得できた場合
            if file and file.root_file_id is not None:
                _body = {"file_keys":file.key,"root_file_id":file.root_file_id,"file_id":file.file_id}
                _bulk.append({'_op_type': 'update',"_index":_index,"_type":_type,"_id":id,"doc":_body,"doc_as_upsert" : True})
                updated.append(id)
            elif file and file.file_id is not None:
                _body = {"file_keys":file.key,"root_file_id":file.file_id,"file_id":file.file_id}
                _bulk.append({'_op_type': 'update',"_index":_index,"_type":_type,"_id":id,"doc":_body,"doc_as_upsert" : True})
                updated.append(id)
            elif _body is not None and _body['root_file_id'] is not None:
                _bulk.append({'_op_type': 'update',"_index":_index,"_type":_type,"_id":id,"doc":_body,"doc_as_upsert" : True})
                updated.append(id)
            else:
                errors.append(id)
    if len(_bulk)>0:
        try:
            res = search.helpers.bulk(open_search, _bulk)
            print("update: {}".format(updated))
            print("result: {}".format(res))
        except Exception as e:
            errors.append(e)
    return errors

    
if __name__ == "__main__":
    index = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-stats-file-download"
    print("# {}".format(index))
    errors = add_root_file_id(index)
    print("raise error item: {}".format(len(errors)))
    print("{}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-download"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(len(errors)))
    print("{}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-preview"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(len(errors)))
    print("{}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-preview"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(len(errors)))
    print("{}".format(errors))
