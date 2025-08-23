import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from api_utils import (
    LINK_BASIL_INSTANCE_HTML_MESSAGE,
    add_html_link_to_email_body,
    load_settings
)


def test__add_html_link_to_email_body():
    settings = None
    initial_body = None
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings = None
    initial_body = ""
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings, settings_last_modified = load_settings(None, None)
    initial_body = ""
    body = add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body != ""
    assert LINK_BASIL_INSTANCE_HTML_MESSAGE in body
