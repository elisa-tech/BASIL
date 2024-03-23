import json
import os
import sys
import traceback
import urllib.request

API_URL = 'http://localhost:5000'

def api_get_sw_components(filter) -> list:
    """
    Return list of Sw Components from BASIL Api
    """
    ret = []
    try:
        response = urllib.request.urlopen(f'{API_URL}/apis?search={filter}')
        content = json.loads(response.read().decode('utf-8'))
        if isinstance(content, list):
            print(f'Sw Components count: {len(content)}')
            ret = content
        else:
            print('Error: The return value is not a list')
    except Exception as exp:
        print(traceback.format_exc())
    return ret

def write_sw_components_to_file(content) -> int:
    """
    Write content as JSON to a file
    """
    ret = 0
    JSON_FILE = 'api.json'
    try:
        f = open(JSON_FILE, 'w')
        json.dump(content, f, indent=2)
        f.close()
        if os.path.exists(JSON_FILE):
            print(f'File {JSON_FILE} exists')
            ret = 1
    except Exception as exp:
        print(traceback.format_exc())
    return ret

if __name__ == '__main__':
    filter = ''
    if len(sys.argv) > 1:
        filter = sys.argv[1]
    write_sw_components_to_file(api_get_sw_components(filter))
