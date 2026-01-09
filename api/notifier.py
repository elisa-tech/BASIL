import os
import smtplib
import ssl
import sys
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from api_utils import (
    get_configuration,
    load_settings,
    parse_int
)

# Configure logger to write to both stdout and file with timestamp and level
logger = logging.getLogger("email_notifier")
logger.setLevel(logging.INFO)
logger.propagate = False
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

stream_handler_exists = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
if not stream_handler_exists:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

# Simple per-process file logging (one file per PID)
log_file_path = os.path.join(currentdir, f"email_notifier.{os.getpid()}.log")
file_handler_exists = any(
    isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == log_file_path
    for h in logger.handlers
)
if not file_handler_exists:
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)


class EmailNotifier():

    settings = None
    settings_last_modified = None

    SETTINGS_SMTP_SECTION = "smtp"
    SETTINGS_SMPT_FIELD_FROM = "from"
    SETTINGS_SMPT_FIELD_HOST = "host"
    SETTINGS_SMPT_FIELD_PASSWORD = "password"
    SETTINGS_SMPT_FIELD_PORT = "port"
    SETTINGS_SMPT_FIELD_REPLY_TO = "reply_to"
    SETTINGS_SMPT_FIELD_SSL = "ssl"
    SETTINGS_SMPT_FIELD_USER = "user"
    ENV_SMPT_FROM = "BASIL_SMTP_FROM"
    ENV_SMPT_HOST = "BASIL_SMTP_HOST"
    ENV_SMPT_PASSWORD = "BASIL_SMTP_PASSWORD"
    ENV_SMPT_PORT = "BASIL_SMTP_PORT"
    ENV_SMPT_REPLY_TO = "BASIL_SMTP_REPLY_TO"
    ENV_SMPT_SSL = "BASIL_SMTP_SSL"
    ENV_SMPT_USER = "BASIL_SMTP_USER"
    DEFAULT_SMPT_FROM = None
    DEFAULT_SMPT_HOST = None
    DEFAULT_SMPT_PASSWORD = None
    DEFAULT_SMPT_PORT = None
    DEFAULT_SMPT_REPLY_TO = None
    DEFAULT_SMPT_SSL = None
    DEFAULT_SMPT_USER = None

    _dry_mode = False
    _from = None
    _host = None
    _password = None
    _port = None
    _reply_to = None
    _ssl = None
    _user = None

    def __init__(self, settings, settings_last_modified, dry_mode):
        """Init the class with the settings"""
        self.settings = settings
        self.settings_last_modified = settings_last_modified
        self._dry_mode = dry_mode

        self._from = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_FROM,
            env_key=self.ENV_SMPT_FROM,
            default_value=self.DEFAULT_SMPT_FROM,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

        self._host = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_HOST,
            env_key=self.ENV_SMPT_HOST,
            default_value=self.DEFAULT_SMPT_HOST,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

        self._password = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_PASSWORD,
            env_key=self.ENV_SMPT_PASSWORD,
            default_value=self.DEFAULT_SMPT_PASSWORD,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

        config_port = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_PORT,
            env_key=self.ENV_SMPT_PORT,
            default_value=self.DEFAULT_SMPT_PORT,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )
        # Try to parse the port as int; leave it as None if not valid.
        self._port = parse_int(config_port)

        self._reply_to = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_REPLY_TO,
            env_key=self.ENV_SMPT_REPLY_TO,
            default_value=self.DEFAULT_SMPT_REPLY_TO,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

        self._ssl = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_SSL,
            env_key=self.ENV_SMPT_SSL,
            default_value=self.DEFAULT_SMPT_SSL,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

        self._user = get_configuration(
            setting_section=self.SETTINGS_SMTP_SECTION,
            setting_key=self.SETTINGS_SMPT_FIELD_USER,
            env_key=self.ENV_SMPT_USER,
            default_value=self.DEFAULT_SMPT_USER,
            settings=self.settings,
            settings_last_modified=self.settings_last_modified
        )

    def validate_settings(self) -> bool:
        """Validate mandatory settings"""

        if not self._from:
            logger.error("`from` field is not configured")
            return False

        if not self._host:
            logger.error("`host` field is not configured")
            return False

        if not self._password:
            logger.error("`password` field is not configured")
            return False

        if not self._port:
            logger.error("`port` field is not configured")
            return False

        if not self._user:
            logger.error("`user` field is not configured")
            return False

        return True

    def send_email(self, recipient, subject, body, is_html=False):

        if not self.validate_settings():
            logger.info("Settings are not valid")
            return False

        try:
            logger.info(f"Preparing email to {recipient} with subject '{subject}'")
            msg = MIMEMultipart()
            msg['From'] = self._from
            msg['To'] = recipient
            msg['Subject'] = subject

            if self._reply_to:
                msg['Reply-To'] = self._reply_to

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            if self._ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self._host, self._port, context=context) as server:
                    server.login(self._user, self._password)
                    if not self._dry_mode:
                        server.sendmail(msg['From'], msg['To'], msg.as_string())
            else:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                with smtplib.SMTP(self._host, self._port) as server:
                    server.starttls(context=context)
                    server.login(self._user, self._password)
                    if not self._dry_mode:
                        server.sendmail(msg['From'], msg['To'], msg.as_string())
            if self._dry_mode:
                logger.info(f"[DRY MODE] Email to {recipient} with subject '{subject}' not sent")
            else:
                logger.info(f"Email sent to {recipient} with subject '{subject}'")
            return True
        except Exception as e:
            logger.exception(f"Error on send_email: {e}")
            return False


if __name__ == "__main__":
    # To run email async
    # Read configuration file and send an email
    EXPECTED_ARGV_COUNT = 7

    if len(sys.argv) < EXPECTED_ARGV_COUNT:
        # Use less (<) as logical operator as we can call this script also with ending &
        logger.info(
            "Usage: python3 notifier.py <config_filepath> <recipient> <title> <body> <is_html> <dry mode [true|false]>"
        )
        sys.exit(1)

    config_filepath = sys.argv[1]
    email_recipient = sys.argv[2]
    email_subject = sys.argv[3]
    email_body = sys.argv[4]
    email_is_html = True if sys.argv[5] in [1, "1", "true", "True", True] else False
    dry_mode = True if sys.argv[6] in [1, "1", "true", "True", True] else False

    settings, settings_last_modified = load_settings(None, None)

    notifier = EmailNotifier(settings=settings, settings_last_modified=settings_last_modified, dry_mode=dry_mode)
    sent = notifier.send_email(email_recipient, email_subject, email_body, email_is_html)
    if sent:
        logger.info(f"Email '{email_subject}' sent to {email_recipient}")
    # Ensure all logs are flushed to disk before the process exits
    logging.shutdown()
