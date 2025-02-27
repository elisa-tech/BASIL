import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import traceback


class EmailNotifier():

    settings = None

    def __init__(self, settings):
        """Init the class with the settings"""
        self.settings = settings

    def validate_settings(self) -> bool:
        """Validate instance settings."""
        smtp_mandatory_settings = ["from", "host", "password", "port", "user"]

        if not self.settings:
            print("Invalid settings")
            return False

        if "smtp" not in self.settings.keys():
            return False

        for setting in smtp_mandatory_settings:
            if setting not in self.settings["smtp"]:
                print(f"Field {setting} not in settings")
                return False
            else:
                if not self.settings["smtp"][setting]:
                    print(f"Setting field {setting} is not valid")
                    return False
                if str(self.settings["smtp"][setting]).strip() == "":
                    print(f"Setting field {setting} is not valid")
                    return False
        return True

    def send_email(self, recipient, subject, body, is_html=False):

        if not self.validate_settings():
            print("Settings not valid")
            return False

        try:
            smtp_from = self.settings["smtp"]["from"]
            smtp_host = self.settings["smtp"]["host"]
            smtp_password = self.settings["smtp"]["password"]
            smtp_port = self.settings["smtp"]["port"]
            smtp_user = self.settings["smtp"]["user"]

            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = recipient
            msg['Subject'] = subject

            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error on send_email: {e}")
            print(traceback.format_exc())
            return False
