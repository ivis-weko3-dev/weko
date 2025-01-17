from bs4 import BeautifulSoup
from box import Box
from datetime import datetime
import json
from urllib.parse import urlparse

def response_save_next_path(response):
    """Save data from "{host}/workflow/activity/init"'s response
    
    Args:
        response (requests.models.Response): response from {host}/workflow/activity/init
    
    Returns:
        Box: next_path and activity_id
            next_path (str): next path
            activity_id (str): activity id
    """
    json = response.json()
    return Box({
        'next_path': json['data']['redirect'],
        'activity_id': json['data']['redirect'].split('/')[-1]
    })

def response_save_recid(response):
    """Save data from "{host}/api/deposits/items"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/deposits/items
        
    Returns:
        Box: recid
            recid (str): recid
    """
    json = response.json()
    return Box({'recid': json['id']})

def response_save_register_data(response, file_name):
    """Save data from target file
    
    Args:
        response (requests.models.Response): response from {host}{next_path}
        file_name (str): name of the file containing the data to be registered
    
    Returns:
        Box: register_data
            register_data (str): register data
    """
    with open('request_params/' + file_name, 'r') as f:
        return Box({'register_data': f.read()})

def response_save_tree_data(response):
    """Save data from "{host}/api/tree/{recid}"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/tree/{recid}
    
    Returns:
        Box: tree_data
            tree_data (list): index id list
    """
    json = response.json()
    return Box({'tree_data': [t['id'] for t in json]})

def response_save_identifier_grant(response):
    """Save data from "{host}/workflow/activity/detail/{activity_id}?page=1&size=20"'s response
    
    Args:
        response (requests.models.Response): response from {host}/workflow/activity/detail/{activity_id}?page=1&size=20
    
    Returns:
        Box: identifier_grant
            identifier_grant (str): identifier grant written in json string
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    jalc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_1'})
    jalc_doi_suffix = jalc_doi_suffix_input['value'] if jalc_doi_suffix_input else ''
    try:
        jalc_doi_link = soup.find('span', {'name': 'idf_grant_link_1'}).text
    except:
        jalc_doi_link = ''
    jalc_cr_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_2'})
    jalc_cr_doi_suffix = jalc_cr_doi_suffix_input['value'] if jalc_cr_doi_suffix_input else ''
    try:
        jalc_cr_doi_link = soup.find('span', {'name': 'idf_grant_link_2'}).text
    except:
        jalc_cr_doi_link = ''
    jalc_dc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_3'})
    jalc_dc_doi_suffix = jalc_dc_doi_suffix_input['value'] if jalc_dc_doi_suffix_input else ''
    try:
        jalc_dc_doi_link = soup.find('span', {'name': 'idf_grant_link_3'}).text
    except:
        jalc_dc_doi_link = ''
    ndl_jalc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_4'})
    ndl_jalc_doi_suffix = ndl_jalc_doi_suffix_input['value'] if ndl_jalc_doi_suffix_input else ''
    try:
        ndl_jalc_doi_link = soup.find('span', {'name': 'idf_grant_link_4'}).text
    except:
        ndl_jalc_doi_link = ''
    crni_link_span = soup.find('span', {'name': 'idf_grant_link_5'})
    crni_link = crni_link_span.text if crni_link_span else ''
    return Box({
        'identifier_grant': json.dumps({
            'jalc_doi_suffix': jalc_doi_suffix,
            'jalc_doi_link': jalc_doi_link,
            'jalc_cr_doi_suffix': jalc_cr_doi_suffix,
            'jalc_cr_doi_link': jalc_cr_doi_link,
            'jalc_dc_doi_suffix': jalc_dc_doi_suffix,
            'jalc_dc_doi_link': jalc_dc_doi_link,
            'ndl_jalc_doi_suffix': ndl_jalc_doi_suffix,
            'ndl_jalc_doi_link': ndl_jalc_doi_link,
            'crni_link': crni_link
        })
    })

def response_save_author_prefix_settings(response):
    """Save data from "{host}/api/items/author_prefix_settings"'s response

    Args:
        response (requests.models.Response): response from {host}/api/items/author_prefix_settings

    Returns:
        Box: settings
            settings (list): author prefix settings
    """
    settings = [j['scheme'] for j in response.json()]
    settings.insert(0, None)
    return Box({'settings': settings})

def response_save_group_list(response):
    """Save data from "{host}/accounts/settings/groups/grouplist"'s response

    Args:
        response (requests.models.Response): response from {host}/accounts/settings/groups/grouplist
    
    Returns:
        Box: group_list
            group_list (list): group list
    """
    return Box({'group_list': list(response.json().keys())})

def response_save_url(response):
    """Save data from "{host}/api/deposits/items"'s response

    Args:
        response (requests.models.Response): response from {host}/api/deposits/items
    
    Returns:
        Box: url
            url (dict): url lists
    """
    url = response.json()['links']
    recid = url['r'].split('/')[-1]
    return Box({'url': url, 'recid': recid})

def response_save_file_upload_info(response, file_key, item_id):
    """Save data from "{url.bucket}"/[file_name]"'s response
    
    Args:
        response (requests.models.Response): response from {url.bucket}/[file_name]
        file_key (str): key of file
        item_id (str): item id
    
    Returns:
        Box:
            file_upload_info (dict): file upload info
            file_metadata (dict): file metadata
    """
    file_upload_info = response.json()
    with open('request_params/item_type_template/schema/item_type_' + str(item_id) + '.json', 'r') as f:
        schema = json.load(f)
    file_schema = schema['schema'][file_key]
    file_metadata = {}
    for key in file_schema['items']['properties'].keys():
        if key == 'url':
            parse = urlparse(file_upload_info['links']['self'])
            url = parse.scheme + '://' + parse.netloc + '/record/2000001/files/' + file_upload_info['key']
            file_metadata[key] = {'url': url} 
        elif key == 'date':
            created_str = file_upload_info['created']
            created = datetime.strptime(created_str, '%Y-%m-%dT%H:%M:%S.%f%z').date()
            file_metadata[key] = [{'dateType': 'Available', 'dateValue': created.strftime('%Y-%m-%d')}]
        elif key == 'format':
            file_metadata[key] = file_upload_info['mimetype']
        elif key == 'filename':
            file_metadata[key] = file_upload_info['key']
        elif key == 'filesize':
            size = file_upload_info['size']
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            count = 0
            while size > 1024:
                size /= 1024
                count += 1
            int_size = int(size)
            if size > int_size:
                int_size += 1
            file_metadata[key] = [{'value': str(int_size) + ' ' + units[count]}]
        elif key == 'accessrole':
            file_metadata[key] = 'open_access'
    file_metadata['version_id'] = file_upload_info['version_id']

    return Box({'file_upload_info': json.dumps(file_upload_info), 'file_metadata': json.dumps({file_key: [file_metadata]})})
