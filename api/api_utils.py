import os
import urllib
from urllib.error import HTTPError, URLError


def get_api_specification(_url_or_path):
    if _url_or_path is None:
        return None
    else:
        _url_or_path = _url_or_path.strip()
        if len(_url_or_path) == 0:
            return None

        if _url_or_path.startswith("http"):
            try:
                resource = urllib.request.urlopen(_url_or_path)
                if resource.headers.get_content_charset():
                    content = resource.read().decode(resource.headers.get_content_charset())
                else:
                    content = resource.read().decode("utf-8")
                return content
            except HTTPError as excp:
                print(f"HTTPError: {excp.reason} reading {_url_or_path}")
                return None
            except URLError as excp:
                print(f"URLError: {excp.reason} reading {_url_or_path}")
                return None
            except ValueError as excp:
                print(f"ValueError reading {_url_or_path}: {excp}")
                return None
        else:
            if not os.path.exists(_url_or_path):
                return None

            try:
                f = open(_url_or_path, "r")
                fc = f.read()
                f.close()
                return fc
            except OSError as excp:
                print(f"OSError for {_url_or_path}: {excp}")
                return None


def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except PermissionError:
        print(f"Error: Permission denied when reading '{filepath}'.")
    except IOError as e:
        print(f"Error: I/O error while reading '{filepath}': {e}")
    return None
