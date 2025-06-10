import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

import api
import api_utils


def test__add_html_link_to_email_body():
    settings = None
    initial_body = None
    body = api_utils.add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert api_utils.LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings = None
    initial_body = ""
    body = api_utils.add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body == ""
    assert api_utils.LINK_BASIL_INSTANCE_HTML_MESSAGE not in body

    settings = api.load_settings()
    initial_body = ""
    body = api_utils.add_html_link_to_email_body(settings=settings, body=initial_body)
    assert body != ""
    assert api_utils.LINK_BASIL_INSTANCE_HTML_MESSAGE in body
