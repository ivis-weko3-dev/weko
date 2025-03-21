from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urlunparse

from helper.config import INVENIO_WEB_HOST_NAME
from helper.verify_database_helper import connect_db, compare_db_data

def response_verify_validate_response(response, file_name):
    """Verify "{host}/api/items/validate"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/items/validate
        file_name (str): name of the file containing the data to be compared
        
    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read())
    assert response.json() == expect

def response_verify_records(response, folder_path, activity_id):
    """Verify records
    
    Args:
        response (requests.models.Response): response from {host}/records/{recid}
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
    
    Returns:
        None
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        # Connect to database
        conn = connect_db()
        cur = conn.cursor()

        cur.execute('SELECT item_id FROM workflow_activity WHERE activity_id = %s', (activity_id,))
        item_id = cur.fetchone()[0]

        cur.execute('SELECT * FROM records_buckets WHERE record_id IN (%s, %s)', (soup.find(id='record_id').text, item_id))
        records_buckets = cur.fetchall()

        # prepare data to replace
        replace_params = {
            'pidstore_pid': {
                'activity_id': activity_id,
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id
            },
            'records_metadata': {
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id,
                'bucket_uuid_2000001': records_buckets[0][1] if records_buckets[0][0] == soup.find(id='record_id').text else records_buckets[1][1],
                'bucket_uuid_2000001.1': records_buckets[0][1] if records_buckets[0][0] == item_id else records_buckets[1][1],
            }
        }

        # prepare column's type conversion params
        type_conversion_params = {
            'pidstore_pid': {
                'id': 'int'
            },
            'records_metadata': {
                'json': 'json',
                'version_id': 'int'
            }
        }
        
        compare_db_data(cur, folder_path, replace_params, type_conversion_params)
    except Exception as e:
        print(e)
        raise e
    finally:
        cur.close()
        conn.close()

def response_verify_records_with_file(response, folder_path, activity_id, file_metadata):
    """Verify records with file
    
    Args:
        response (requests.models.Response): response from {host}/records/{recid}
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
        file_metadata (str): file metadata
        
    Returns:
        None"""

    def create_file_metadata(file_metadata, cur=None):
        """Create file metadata
        
        Args:
            file_metadata (str): file metadata
            cur (psycopg2.extensions.cursor): cursor
        
        Returns:
            str: file metadata
        """
        file_metadata_list = list(json.loads(file_metadata).values())[0]
        url = file_metadata_list[0]['url']['url']
        parsed_url = urlparse(url)
        new_url = urlunparse(parsed_url._replace(netloc=INVENIO_WEB_HOST_NAME))
        if cur:
            cur.execute('SELECT version_id FROM files_object WHERE file_id = (SELECT file_id FROM files_object WHERE version_id = %s) AND version_id != %s',
                        (file_metadata_list[0]['version_id'],file_metadata_list[0]['version_id']))
            version_id = cur.fetchone()[0]
            new_url = new_url.replace('2000001', '2000001.1')
            file_metadata_list[0]['version_id'] = version_id
        file_metadata_list[0]['mimetype'] = file_metadata_list[0]['format']
        file_metadata_list[0]['url']['url'] = new_url
        return json.dumps(file_metadata_list)

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        # Connect to database
        conn = connect_db()
        cur = conn.cursor()

        cur.execute('SELECT item_id FROM workflow_activity WHERE activity_id = %s', (activity_id,))
        item_id = cur.fetchone()[0]

        cur.execute('SELECT * FROM records_buckets WHERE record_id IN (%s, %s)', (soup.find(id='record_id').text, item_id))
        records_buckets = cur.fetchall()

        # prepare data to replace
        replace_params = {
            'pidstore_pid': {
                'activity_id': activity_id,
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id
            },
            'records_metadata': {
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id,
                'bucket_uuid_2000001': records_buckets[0][1] if records_buckets[0][0] == soup.find(id='record_id').text else records_buckets[1][1],
                'bucket_uuid_2000001.1': records_buckets[0][1] if records_buckets[0][0] == item_id else records_buckets[1][1],
                'file_metadata_2000001': create_file_metadata(file_metadata),
                'file_metadata_2000001.1': create_file_metadata(file_metadata, cur)
            }
        }

        # prepare column's type conversion params
        type_conversion_params = {
            'pidstore_pid': {
                'id': 'int'
            },
            'records_metadata': {
                'json': 'json',
                'version_id': 'int'
            }
        }
        
        compare_db_data(cur, folder_path, replace_params, type_conversion_params)
        
    except Exception as e:
        print(e)
        raise e
    finally:
        cur.close()
        conn.close()