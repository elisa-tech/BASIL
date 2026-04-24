import datetime
import html as html_module
import tarfile
import logging
import os
import re
import subprocess
import urllib
from pyaml_env import parse_config
from string import Template
from urllib.error import HTTPError, URLError

currentdir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)

from db.db_orm import DbInterface  # noqa: E402
from db.models.comment import CommentModel  # noqa: E402
from db.models.db_base import Base  # noqa: E402
from db.models.user import UserModel  # noqa: E402

LINK_BASIL_INSTANCE_HTML_MESSAGE = "Link to BASIL website"

CONFIGS_FOLDER = "configs"
SETTINGS_FILEPATH = os.path.join(currentdir, CONFIGS_FOLDER, "settings.yaml")

ROW_LABEL_TD_STYLE = (
    "padding:8px 10px;white-space:nowrap;width:1%;"
    "vertical-align:top;border-bottom:1px solid #e0e0e0;"
)
ROW_VALUE_TD_STYLE = (
    "padding:8px 10px;width:99%;word-break:break-all;"
    "overflow-wrap:break-word;vertical-align:top;border-bottom:1px solid #e0e0e0;"
)

BORDER_COLOR_SW_REQUIREMENT = "#0066cc"
BORDER_COLOR_TEST_SPECIFICATION = "#008060"
BORDER_COLOR_TEST_CASE = "#6a4c93"
BORDER_COLOR_DOCUMENT = "#8a6d3b"
BORDER_COLOR_JUSTIFICATION = "#c9190b"
BORDER_COLOR_TEST_RUN = "#4a90d9"
BORDER_COLOR_COMMENT = "#6c757d"

_BACKTICK_RE = re.compile(r'`([^`]+)`')
_INLINE_CODE_STYLE = (
    "background:#f0f0f0;padding:1px 4px;border-radius:3px;"
    "font-family:monospace;font-size:12px;"
)


def _render_inline_code(text: str) -> str:
    return _BACKTICK_RE.sub(
        rf'<code style="{_INLINE_CODE_STYLE}">\1</code>',
        text
    )


def _section_type_style(border_color: str) -> str:
    return (
        f"border-left:3px solid {border_color};padding-left:12px;"
        "border-bottom:1px solid #CCC;page-break-inside:avoid;"
        "margin-top:14px;"
    )


def tr(label_html: str, value_html: str) -> str:
    return (
        f"<tr><td style='{ROW_LABEL_TD_STYLE}'>{label_html}</td>"
        f"<td style='{ROW_VALUE_TD_STYLE}'>{value_html}</td></tr>"
    )


def get_safe_str(value, trim=True, encoding='utf-8') -> str:
    """
    Safely convert a value to string

    Args:
        value: The value to convert to string
        trim: Whether to strip leading/trailing whitespace
        encoding: Text encoding to use for conversion

    Returns:
        str: Safe string representation of the input
    """
    # Handle None and empty values
    if value is None:
        return ""

    # Convert to string safely
    try:
        if isinstance(value, bytes):
            result = value.decode(encoding, errors='replace')
        else:
            result = str(value)
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback for encoding issues
        result = str(value).encode(encoding, errors='replace').decode(encoding)

    # Trim whitespace if requested
    if trim:
        result = result.strip()

    return result


def get_configuration(
        setting_section=None,
        setting_key=None,
        env_key=None,
        default_value=None,
        settings=None,
        settings_last_modified=None):
    """Extract a configuration from settings or from environment file
    settings should have priority on environment file as admin can overwrite it at runtime"""

    valid_settings_config = True
    if not setting_section or not setting_key:
        valid_settings_config = False

    if valid_settings_config:
        settings, settings_last_modified = load_settings(settings, settings_last_modified)
        if setting_section in settings.keys():
            if setting_key in settings[setting_section].keys():
                return settings[setting_section][setting_key]

    if not env_key:
        return None

    ret = os.environ.get(env_key, default_value)
    if not ret:
        return None

    if not isinstance(ret, str):
        return ret

    if ret.lower() == "true":
        return True
    if ret.lower() == "false":
        return False

    return ret


def load_settings(settings_cache=None, settings_last_modified=None):
    """Load settings from yaml file if file last modified date
    is different from the last time we read it
    """

    if not os.path.exists(SETTINGS_FILEPATH):
        f = open(SETTINGS_FILEPATH, "w")
        f.write("")
        f.close()

    read_settings_file = False
    last_modified = os.path.getmtime(SETTINGS_FILEPATH)

    if settings_cache is None or settings_last_modified is None:
        read_settings_file = True
    else:
        if settings_last_modified != last_modified:
            read_settings_file = True

    if read_settings_file:
        try:
            settings_cache = parse_config(path=SETTINGS_FILEPATH)
            settings_last_modified = last_modified
        except Exception as e:
            logger.error(f"Exception on load_settings(): {e}")
    return settings_cache, settings_last_modified


def get_available_filepath(filepath):
    """
    Given a full file path, returns a new path that doesn't exist
    by appending _1, _2, etc. to the base filename if needed.

    Example:
        /home/user/report.txt →
        /home/user/report_1.txt (if report.txt exists)
    """
    if not os.path.exists(filepath):
        return filepath

    directory, filename = os.path.split(filepath)
    base, ext = os.path.splitext(filename)
    counter = 1

    while True:
        new_filename = f"{base}_{counter}{ext}"
        new_filepath = os.path.join(directory, new_filename)
        if not os.path.exists(new_filepath):
            return new_filepath
        counter += 1


def is_testing_enabled_by_env() -> bool:
    ret = False
    env_testing = os.getenv("BASIL_TESTING", "")
    if str(env_testing).lower().strip() in ["1", "true"]:
        ret = True
    return ret


def bool_from_string(value: str) -> bool:
    return str(value).lower().strip() in ["1", "true"]


def add_html_link_to_email_body(settings, body) -> str:
    """Append a link to BASIL instance if the app_url setting is populated"""
    if not settings:
        return body if body else ""

    if not body:
        return ""

    if "app_url" in settings.keys():
        if str(settings["app_url"]).strip():
            body += f"<p><a href='{settings['app_url']}'>{LINK_BASIL_INSTANCE_HTML_MESSAGE}</a></p>"
    return body


def get_html_email_body_from_template(template_path, subject, body, footer):
    """Generate the HTML email body from a template file using
    custom values for subject, body and footer
    """
    if not os.path.exists(template_path):
        return None

    with open(template_path, "r") as file:
        html_template = Template(file.read())
        body = html_template.substitute(subject=subject,
                                        body=body,
                                        footer=footer)
    return body


def normalize_whitespace(text: str) -> str:
    # Replace all types of whitespace (spaces, tabs, newlines) with a single space
    return re.sub(r'\s+', ' ', text).strip()


def async_email_notification(setting_path, template_path, recipient_list, subject, body, footer, is_html):
    """Send async email to a list of recipients
    to be used in case user don't need to know the notification status
    """
    if recipient_list:
        if is_html:
            body = get_html_email_body_from_template(template_path, subject, body, footer)
            if not body:
                return False

        for recipient in recipient_list:
            cmd = ["python3",
                   "notifier.py",
                   f"{setting_path}",
                   f"{recipient}",
                   f"{subject}",
                   f"{body}",
                   f"{is_html}",
                   "false",  # dry mode
                   "&"]

            subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        return True
    return False


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
                logger.error(f"HTTPError: {excp.reason} reading {_url_or_path}")
                return None
            except URLError as excp:
                logger.error(f"URLError: {excp.reason} reading {_url_or_path}")
                return None
            except ValueError as excp:
                logger.error(f"ValueError reading {_url_or_path}: {excp}")
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
                logger.error(f"OSError for {_url_or_path}: {excp}")
                return None


def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        logger.error(f"Error: File '{filepath}' not found.")
    except PermissionError:
        logger.error(f"Error: Permission denied when reading '{filepath}'.")
    except IOError as e:
        logger.error(f"Error: I/O error while reading '{filepath}': {e}")
    return None


def parse_int(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None  # or raise ValueError if needed


def get_user_traceability_scanner_config(user: UserModel):
    user_config_dir = get_user_config_folder_path(user)
    user_config_path = os.path.join(user_config_dir, "config.yaml")
    if not os.path.exists(user_config_path):
        try:
            initial_config = "api: []\n"
            if not os.path.exists(user_config_dir):
                os.makedirs(user_config_dir, exist_ok=True)
            f = open(user_config_path, "w")
            f.write(initial_config)
            f.close()
            return initial_config
        except Exception as exc:
            logger.error(f"Unable to write user settings file {user_config_path}: {exc}")
            return None
    try:
        f = open(user_config_path, "r")
        fc = f.read()
        f.close()
        return fc
    except Exception:
        logger.error(f"Unable to read user settings file: {user_config_path}")
    return None


def string_to_html(text: str) -> str:
    text = get_safe_str(text)
    text = html_module.escape(text)
    return text.replace("\n", "<br/>")


def code_to_html(text: str) -> str:
    """Escape HTML for rendering inside <pre><code> blocks, preserving whitespace."""
    return html_module.escape(get_safe_str(text, trim=False))


def description_to_html(text: str) -> str:
    """Render description text with + bullet lists and inline code from backticks."""
    text = get_safe_str(text)
    text = html_module.escape(text)
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("+ "):
            if not in_list:
                result.append("<ul style='margin:4px 0;padding-left:20px;'>")
                in_list = True
            item_text = _render_inline_code(stripped[2:])
            result.append(f"<li>{item_text}</li>")
        elif stripped == "":
            if in_list:
                result.append("</ul>")
                in_list = False
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            escaped = _render_inline_code(stripped)
            result.append(f"{escaped}<br/>")
    if in_list:
        result.append("</ul>")
    return "".join(result)


def section_to_html(text: str) -> str:
    """Lightweight markdown-to-HTML for Document section fields."""
    text = get_safe_str(text)
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_list:
                result.append("</ul>")
                in_list = False
            heading_text = html_module.escape(stripped[3:])
            result.append(
                f"<h4 style='margin:12px 0 4px;font-size:14px;'>{heading_text}</h4>"
            )
        elif stripped.startswith("# "):
            if in_list:
                result.append("</ul>")
                in_list = False
            heading_text = html_module.escape(stripped[2:])
            result.append(
                f"<h4 style='margin:12px 0 4px;font-size:15px;font-weight:700;'>"
                f"{heading_text}</h4>"
            )
        elif stripped.startswith("- "):
            if not in_list:
                result.append("<ul style='margin:4px 0;padding-left:20px;'>")
                in_list = True
            item_text = html_module.escape(stripped[2:])
            item_text = _render_inline_code(item_text)
            result.append(f"<li>{item_text}</li>")
        elif stripped == "":
            if in_list:
                result.append("</ul>")
                in_list = False
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            escaped = html_module.escape(stripped)
            escaped = _render_inline_code(escaped)
            result.append(f"<p style='margin:4px 0;'>{escaped}</p>")
    if in_list:
        result.append("</ul>")
    return "".join(result)


def sw_requirement_to_html(sw_requirement: dict, comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_SW_REQUIREMENT)
    anchor = f"sw_requirement-{sw_requirement['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>SW REQUIREMENT</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Sw Requirement {sw_requirement['id']}</h3>"
    html += f"<div id='sw_requirement-details-{sw_requirement['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Version</b>: {string_to_html(sw_requirement['version'])} &nbsp; • &nbsp;"
    html += f"<b>Status</b>: {string_to_html(sw_requirement['status'])} &nbsp; • &nbsp; "
    html += f"<b>Created by</b>: {string_to_html(sw_requirement['created_by'])}"
    html += "</td></tr>"
    html += tr("<b>Title</b>:", string_to_html(sw_requirement['title']))
    html += tr("<b>Description</b>:", description_to_html(sw_requirement['description']))
    html += "</table>"
    html += "</div>"

    if comments:
        html += comments_to_html(comments)

    html += "</div>"
    return html


def test_specification_to_html(test_specification: dict, comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_TEST_SPECIFICATION)
    anchor = f"test_specification-{test_specification['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>TEST SPECIFICATION</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Test Specification {test_specification['id']}</h3>"
    html += f"<div id='test_specification-details-{test_specification['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Version</b>: {string_to_html(test_specification['version'])} &nbsp; • &nbsp;"
    html += f"<b>Status</b>: {string_to_html(test_specification['status'])} &nbsp; • &nbsp; "
    html += f"<b>Created by</b>: {string_to_html(test_specification['created_by'])}"
    html += "</td></tr>"
    html += tr("<b>Title</b>:", string_to_html(test_specification['title']))
    html += tr("<b>Preconditions</b>:", description_to_html(test_specification['preconditions']))
    html += tr("<b>Test Description</b>:", description_to_html(test_specification['test_description']))
    html += tr("<b>Expected behavior</b>:", description_to_html(test_specification['expected_behavior']))
    html += "</table>"
    html += "</div>"

    if comments:
        html += comments_to_html(comments)

    html += "</div>"
    return html


def test_case_to_html(test_case: dict, comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_TEST_CASE)
    anchor = f"test_case-{test_case['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>TEST CASE</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Test Case {test_case['id']}</h3>"
    html += f"<div id='test_case-details-{test_case['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Version</b>: {string_to_html(test_case['version'])} &nbsp; • &nbsp;"
    html += f"<b>Status</b>: {string_to_html(test_case['status'])} &nbsp; • &nbsp; "
    html += f"<b>Created by</b>: {string_to_html(test_case['created_by'])}"
    html += "</td></tr>"
    html += tr("<b>Title</b>:", string_to_html(test_case['title']))
    html += tr("<b>Description</b>:", description_to_html(test_case['description']))
    html += tr("<b>Repository</b>:", string_to_html(test_case['repository']))
    html += tr("<b>Relative Path</b>:", string_to_html(test_case['relative_path']))
    html += "</table>"
    html += "</div>"

    if comments:
        html += comments_to_html(comments)

    html += "</div>"
    return html


def test_run_to_html(test_run: dict) -> str:
    style = _section_type_style(BORDER_COLOR_TEST_RUN)
    anchor = f"test_run-{test_run['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>TEST RUN</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Test Run {test_run['id']}</h3>"
    html += f"<div id='test_run-details-{test_run['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += tr("<b>Test Run Config ID</b>:", string_to_html(test_run['config']['id']))
    html += tr(
        "<b>Result</b>:",
        "<span class='pf-c-label'><span class='pf-c-label__content uppercase'>"
        f"{string_to_html(str(test_run['result']).upper())}</span></span>"
    )
    html += tr("<b>Notes</b>:", string_to_html(test_run['notes']))
    html += tr("<b>Bugs</b>:", string_to_html(test_run['bugs']))
    html += tr("<b>Fixes</b>:", string_to_html(test_run['fixes']))
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Created by</b>: {test_run['created_by']} &nbsp; • &nbsp;"
    html += f"<b>Created at</b>: {test_run['created_at']}"
    html += "</td></tr>"
    html += "</table>"
    html += "</div></div>"
    return html


def test_run_config_to_html(test_run_config: dict) -> str:
    style = _section_type_style(BORDER_COLOR_TEST_RUN)
    anchor = f"test_run_config-{test_run_config['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>TEST RUN CONFIG</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Test Run Config {test_run_config['id']}</h3>"
    html += f"<div id='test_run_config-details-{test_run_config['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += tr("<b>Title</b>:", string_to_html(test_run_config['title']))
    html += tr("<b>Plugin</b>:", string_to_html(test_run_config['plugin']))
    html += tr("<b>Plugin Preset</b>:", string_to_html(test_run_config['plugin_preset']))
    html += tr("<b>Plugin Vars</b>:", string_to_html(test_run_config['plugin_vars']))
    html += tr("<b>Git Repo Ref</b>:", string_to_html(test_run_config['git_repo_ref']))
    html += tr("<b>Context Vars</b>:", string_to_html(test_run_config['context_vars']))
    html += tr("<b>Environment Vars</b>:", string_to_html(test_run_config['environment_vars']))
    html += tr("<b>Provision Type</b>:", string_to_html(test_run_config['provision_type']))
    html += tr("<b>Provision Guest</b>:", string_to_html(test_run_config['provision_guest']))
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Created by</b>: {test_run_config['created_by']} &nbsp; • &nbsp;"
    html += "</td></tr>"
    html += "</table>"
    html += "</div></div>"
    return html


def document_to_html(document: dict, comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_DOCUMENT)
    anchor = f"document-{document['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>DOCUMENT</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Document {document['id']}</h3>"
    html += f"<div id='document-details-{document['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Version</b>: {string_to_html(document['version'])} &nbsp; • &nbsp;"
    html += f"<b>Status</b>: {string_to_html(document['status'])} &nbsp; • &nbsp; "
    html += f"<b>Created by</b>: {string_to_html(document['created_by'])}"
    html += "</td></tr>"
    html += tr("<b>Title</b>:", string_to_html(document['title']))
    html += tr("<b>Description</b>:", description_to_html(document['description']))
    url_escaped = string_to_html(document['url'])
    html += tr("<b>Url</b>:", f"<a href='{html_module.escape(document['url'])}'>{url_escaped}</a>")
    html += tr("<b>Type</b>:", string_to_html(document['document_type']))
    html += tr("<b>SPDX Relationship</b>:", string_to_html(document['spdx_relation']))
    if document['document_type'] == 'text':
        html += tr("<b>Section</b>:", section_to_html(document['section']))
        html += tr("<b>Offset</b>:", string_to_html(str(document['offset'])))
    html += "</table>"
    html += "</div>"

    if comments:
        html += comments_to_html(comments)

    html += "</div>"
    return html


def justification_to_html(justification: dict, comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_JUSTIFICATION)
    anchor = f"justification-{justification['id']}"
    html = f"<a name='{anchor}'></a>"
    html += f"<div style='{style}' id='{anchor}'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>JUSTIFICATION</span></span>"
    )
    html += f"<h3 style='page-break-after:avoid;'>Justification {justification['id']}</h3>"
    html += f"<div id='justification-details-{justification['id']}'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += "<tr><td colspan='2' style='padding:10px; font-size: 12px;'>"
    html += f"<b>Version</b>: {string_to_html(justification['version'])} &nbsp; • &nbsp;"
    html += f"<b>Status</b>: {string_to_html(justification['status'])} &nbsp; • &nbsp; "
    html += f"<b>Created by</b>: {string_to_html(justification['created_by'])}"
    html += "</td></tr>"
    html += tr("<b>Title</b>:", description_to_html(justification['description']))
    html += "</table>"
    html += "</div>"

    if comments:
        html += comments_to_html(comments)

    html += "</div>"
    return html


def comments_to_html(comments: list[dict]) -> str:
    style = _section_type_style(BORDER_COLOR_COMMENT)
    html = f"<div style='{style}' id='comments'>"
    html += (
        "<span class='pf-c-label'>"
        "<span class='pf-c-label__content uppercase'>COMMENTS</span></span>"
    )
    html += "<h3 style='page-break-after:avoid;'>Comments</h3>"
    html += "<div id='comments-details'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    for comment in comments:
        username = html_module.escape(str(comment['created_by_username']))
        updated = html_module.escape(str(comment['updated_at']))
        body = string_to_html(comment['comment'])
        html += (
            f"<tr><td style='vertical-align:top;padding:8px 10px;width:30%;"
            f"border-bottom:1px solid #e0e0e0;white-space:nowrap;'>"
            f"{username}<br><small>{updated}</small></td>"
            f"<td style='vertical-align:top;padding:8px 10px;width:70%;"
            f"border-bottom:1px solid #e0e0e0;'>{body}</td></tr>"
        )
    html += "</table>"
    html += "</div></div>"
    return html


def test_runs_tarball(user: UserModel, test_runs: list) -> str:
    from api import USER_FILES_BASE_DIR, TEST_RUNS_BASE_DIR

    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    artifacts_dir = os.path.join(USER_FILES_BASE_DIR, f"{user.id}.artifacts")
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir, exist_ok=True)

    # Collect artifcats of test runs into a tarball and return the path to the tarball
    tarball_path = os.path.join(artifacts_dir, f"test_runs_{now_str}.tar.gz")
    with tarfile.open(tarball_path, "w:gz") as tar:
        for test_run in test_runs:
            # Add the test run folder to the tarball
            tar.add(os.path.join(TEST_RUNS_BASE_DIR, test_run['uid']), arcname=test_run['uid'])
    return tarball_path


def get_tmt_version() -> str:
    try:
        return subprocess.check_output(["tmt", "--version"]).decode("utf-8").strip()
    except Exception:
        return None


def get_python_version() -> str:
    try:
        return subprocess.check_output(["python", "--version"]).decode("utf-8").strip()
    except Exception:
        return None


def tools_to_html() -> str:
    from api import API_VERSION

    tmt_version = get_tmt_version()
    if tmt_version:
        tmt_version = tr("<b>tmt</b>:", string_to_html(tmt_version))
    else:
        tmt_version = ""

    python_version = get_python_version()
    if python_version:
        python_version = tr("<b>Python</b>:", string_to_html(python_version))
    else:
        python_version = ""

    html = "<div style='border-bottom:1px solid #CCC;' id='tools'>"
    html += "<h2>Tools</h2>"
    html += "<div id='tools-details'>"
    html += "<table style='table-layout: auto; width: 100%;'>"
    html += tr("<b>BASIL</b>:", string_to_html(API_VERSION))
    html += tmt_version
    html += python_version
    html += "</table>"
    html += "</div></div>"
    return html


def get_user_folder_path(user: UserModel, folder_name: str) -> str:
    from api import USER_FILES_BASE_DIR
    user_path = os.path.join(USER_FILES_BASE_DIR, f"{user.id}", folder_name)
    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)
    return user_path


def get_user_config_folder_path(user: UserModel) -> str:
    return get_user_folder_path(user, ".config")


def get_user_html_folder_path(user: UserModel) -> str:
    return get_user_folder_path(user, ".html")


def get_user_pdf_folder_path(user: UserModel) -> str:
    return get_user_folder_path(user, ".pdf")


def get_user_tarball_folder_path(user: UserModel) -> str:
    return get_user_folder_path(user, ".tarball")


def get_custom_actions(user: UserModel) -> list:
    """ Return Custom actions from admin settings """
    from api import SETTINGS_CACHE, SETTINGS_LAST_MODIFIED
    actions = {}

    # Load admin settings
    settings, settings_last_modified = load_settings(
        settings_cache=SETTINGS_CACHE, settings_last_modified=SETTINGS_LAST_MODIFIED
    )
    if settings:
        admin_settings = settings.get("actions", {})
        actions.update(admin_settings)
    return actions


def is_safe_user_path(user_root, requested_path):
    """Return True only if *requested_path* resolves under *user_root*."""
    abs_root = os.path.realpath(user_root)
    abs_target = os.path.realpath(requested_path)
    return abs_target == abs_root or abs_target.startswith(abs_root + os.sep)


def is_safe_local_user_file_path(path: str) -> bool:
    from api import USER_FILES_BASE_DIR
    return path.startswith(os.path.abspath(USER_FILES_BASE_DIR) + os.sep)


def extend_unmapped_sections_for_auto_fix(unmapped_sections: list, api_specification: str) -> list:
    """ Extend unmapped sections for auto-fix by adding the offset of the section in the api_specification
    if the section exists in the api_specification, otherwise assign -1
    """
    for iUS in range(len(unmapped_sections)):
        current_section = unmapped_sections[iUS]["section"]
        if current_section in api_specification:
            unmapped_sections[iUS]["auto-fix-offset"] = api_specification.index(current_section)
        else:
            unmapped_sections[iUS]["auto-fix-offset"] = -1
    return unmapped_sections


def get_missing_mandatory_fields(mandatory_fields: list, request_data: dict) -> list:
    """ Return the missing mandatory fields from the request data """
    missing_fields = []
    for field in mandatory_fields:
        if field not in request_data.keys():
            missing_fields.append(field)
    return missing_fields


def get_mapping_comments(dbi: DbInterface, relation_id: int, tablename: str) -> list:
    if not relation_id or not tablename or not dbi:
        return []

    comments = (
        dbi.session.query(
            CommentModel.id,
            CommentModel.comment,
            CommentModel.updated_at,
            UserModel.email,
            UserModel.username
        )
        .filter(CommentModel.parent_table == tablename)
        .filter(CommentModel.parent_id == relation_id)
        .join(UserModel, CommentModel.created_by_id == UserModel.id)
        .order_by(CommentModel.created_at.asc())
        .all()
    )

    return [
        {
            "id": c.id,
            "comment": c.comment,
            "updated_at": c.updated_at.strftime(Base.dt_short_format_str),
            "created_by_email": c.email,
            "created_by_username": c.username
        }
        for c in comments
    ]
