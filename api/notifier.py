import os
import smtplib
import ssl
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pyaml_env import parse_config


class EmailNotifier():

    settings = None

    SMTP_SETTING_FIELD = "smtp"
    SMTP_SETTING_FIELD_FROM = "from"
    SMTP_SETTING_FIELD_HOST = "host"
    SMTP_SETTING_FIELD_PASSWORD = "password"
    SMTP_SETTING_FIELD_PORT = "port"
    SMTP_SETTING_FIELD_REPLY_TO = "reply_to"
    SMTP_SETTING_FIELD_SSL = "ssl"
    SMTP_SETTING_FIELD_USER = "user"

    def __init__(self, settings):
        """Init the class with the settings"""
        self.settings = settings

    def validate_settings(self) -> bool:
        """Validate instance settings."""
        smtp_mandatory_settings = [self.SMTP_SETTING_FIELD_FROM, self.SMTP_SETTING_FIELD_HOST,
                                   self.SMTP_SETTING_FIELD_PASSWORD, self.SMTP_SETTING_FIELD_PORT,
                                   self.SMTP_SETTING_FIELD_SSL, self.SMTP_SETTING_FIELD_USER]

        if not self.settings:
            print("Invalid settings")
            return False

        if "smtp" not in self.settings.keys():
            return False

        for setting in smtp_mandatory_settings:
            if setting not in self.settings[self.SMTP_SETTING_FIELD]:
                print(f"Field {setting} not in settings")
                return False
            else:
                if not self.settings[self.SMTP_SETTING_FIELD][setting]:
                    print(f"Setting field {setting} is not valid")
                    return False
                if str(self.settings[self.SMTP_SETTING_FIELD][setting]).strip() == "":
                    print(f"Setting field {setting} is not valid")
                    return False
        return True

    def send_email(self, recipient, subject, body, is_html=False):

        if not self.validate_settings():
            print("Settings not valid")
            return False
        else:
            print("Settings is valid")

        try:
            smtp_from = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_FROM]
            smtp_host = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_HOST]
            smtp_password = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_PASSWORD]
            smtp_port = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_PORT]
            smtp_user = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_USER]

            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = recipient
            msg['Subject'] = subject

            if "reply_to" in self.settings[self.SMTP_SETTING_FIELD].keys():
                msg['Reply-To'] = self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_REPLY_TO]

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            if self.settings[self.SMTP_SETTING_FIELD][self.SMTP_SETTING_FIELD_SSL]:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(msg['From'], msg['To'], msg.as_string())
            else:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls(context=context)
                    server.login(smtp_user, smtp_password)
                    server.sendmail(msg['From'], msg['To'], msg.as_string())
            return True
        except Exception as e:
            print(f"Error on send_email: {e}")
            print(traceback.format_exc())
            return False


if __name__ == "__main__":
    # To run email async
    # Read configuration file and send an email
    EXPECTED_ARGV_COUNT = 6

    if len(sys.argv) < EXPECTED_ARGV_COUNT:
        # Use less (<) as logical operator as we can call this script also with ending &
        print("Usage: python3 notifier.py <config_filepath> <recipient> <title> <body> <is_html>")
        sys.exit(1)

    config_filepath = sys.argv[1]
    email_recipient = sys.argv[2]
    email_subject = sys.argv[3]
    email_body = sys.argv[4]
    email_is_html = True if sys.argv[5] in [1, "1", "true", "True", True] else False

    if not os.path.exists(config_filepath):
        print("Configuration file does not exists")
        sys.exit(2)

    try:
        email_config = parse_config(path=config_filepath)
    except Exception as e:
        print(f"Exception on reading email settings: {e}")

    notifier = EmailNotifier(settings=email_config)
    notifier.send_email(email_recipient, email_subject, email_body, email_is_html)
