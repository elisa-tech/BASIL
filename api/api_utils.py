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

LINK_BASIL_INSTANCE_HTML_MESSAGE = "Link to BASIL website"

CONFIGS_FOLDER = "configs"
SETTINGS_FILEPATH = os.path.join(currentdir, CONFIGS_FOLDER, "settings.yaml")


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

        with open("email_notifier.log", "a") as log_file:
            with open("email_notifier.err", "a") as err_file:

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
                                     stdout=log_file,
                                     stderr=err_file)
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
