"""Shared helpers for user-files HTTP tests (UserFiles, UserFileContent, UserFileFolder)."""
import os
import shutil

import api as basil_api

USER_FILES_URL = "/user/files"
USER_FILE_CONTENT_URL = "/user/files/content"
USER_FILE_FOLDER_URL = "/user/files/folder"
UT_PREFIX = "ut_user_files_"


def auth_query(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def auth_json_body(auth_json):
    return {"user-id": auth_json["id"], "token": auth_json["token"]}


def user_files_dir(user_id):
    return os.path.join(basil_api.USER_FILES_BASE_DIR, str(user_id))


def get_files(client, auth_json, extra_query=None):
    qs = auth_query(auth_json)
    if extra_query:
        qs = {**qs, **extra_query}
    return client.get(USER_FILES_URL, query_string=qs)


def post_file(client, auth_json, filename, filecontent):
    body = {
        **auth_json_body(auth_json),
        "filename": filename,
        "filecontent": filecontent,
    }
    return client.post(USER_FILES_URL, json=body)


def delete_file(client, auth_json, filename):
    body = {**auth_json_body(auth_json), "filename": filename}
    return client.delete(USER_FILES_URL, json=body)


def move_file(client, auth_json, source, destination):
    body = {**auth_json_body(auth_json), "source": source, "destination": destination}
    return client.put(USER_FILES_URL, json=body)


def create_folder(client, auth_json, foldername):
    body = {**auth_json_body(auth_json), "foldername": foldername}
    return client.post(USER_FILE_FOLDER_URL, json=body)


def get_content(client, auth_json, filename):
    qs = {**auth_query(auth_json), "filename": filename}
    return client.get(USER_FILE_CONTENT_URL, query_string=qs)


def put_content(client, auth_json, filename, filecontent):
    body = {
        **auth_json_body(auth_json),
        "filename": filename,
        "filecontent": filecontent,
    }
    return client.put(USER_FILE_CONTENT_URL, json=body)


def remove_if_exists(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def remove_user_files_dir_if_exists(user_id):
    """Remove the whole user-files directory if present (tests that need no prior folder)."""
    path = user_files_dir(user_id)
    if os.path.isdir(path):
        shutil.rmtree(path)
