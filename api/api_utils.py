import os
import subprocess
import urllib
from string import Template
from urllib.error import HTTPError, URLError


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
