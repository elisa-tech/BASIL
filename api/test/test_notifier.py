import os
import pytest
from notifier import EmailNotifier
from api_utils import load_settings


def get_valid_settings(ssl=None):
    settings, settings_last_modified = load_settings(None, None)
    smtp_section = EmailNotifier.SETTINGS_SMTP_SECTION
    settings[smtp_section] = {}
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_FROM] = "from"
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_HOST] = "host"
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_PASSWORD] = "password"
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_PORT] = "1234"
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_REPLY_TO] = "reply_to"
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_SSL] = True if ssl else False
    settings[smtp_section][EmailNotifier.SETTINGS_SMPT_FIELD_USER] = "user"
    return settings, settings_last_modified


@pytest.mark.parametrize('mandatory_field', [
    EmailNotifier.SETTINGS_SMPT_FIELD_FROM,
    EmailNotifier.SETTINGS_SMPT_FIELD_HOST,
    EmailNotifier.SETTINGS_SMPT_FIELD_PASSWORD,
    EmailNotifier.SETTINGS_SMPT_FIELD_PORT,
    EmailNotifier.SETTINGS_SMPT_FIELD_USER])
def test_wrong_settings(mandatory_field):
    en = EmailNotifier(settings=None, settings_last_modified=None, dry_mode=True)
    assert not en.validate_settings()

    # remove a mandatory field from valid setting
    settings, settings_last_modified = get_valid_settings()
    del settings[EmailNotifier.SETTINGS_SMTP_SECTION][mandatory_field]
    en = EmailNotifier(settings=settings, settings_last_modified=settings_last_modified, dry_mode=True)
    assert not en.validate_settings()


@pytest.mark.parametrize('mandatory_field', [
    EmailNotifier.SETTINGS_SMPT_FIELD_FROM,
    EmailNotifier.SETTINGS_SMPT_FIELD_HOST,
    EmailNotifier.SETTINGS_SMPT_FIELD_PASSWORD,
    EmailNotifier.SETTINGS_SMPT_FIELD_PORT,
    EmailNotifier.SETTINGS_SMPT_FIELD_USER])
def test_wrong_settings_but_env(mandatory_field):
    """settings are not providing a field but it is defined in the env variables"""
    # remove a mandatory field from valid setting
    settings, settings_last_modified = get_valid_settings()
    del settings[EmailNotifier.SETTINGS_SMTP_SECTION][mandatory_field]
    # populate env variables
    os.environ[EmailNotifier.ENV_SMPT_FROM] = 'from'
    os.environ[EmailNotifier.ENV_SMPT_HOST] = 'host'
    os.environ[EmailNotifier.ENV_SMPT_PASSWORD] = 'password'
    os.environ[EmailNotifier.ENV_SMPT_PORT] = '1234'
    os.environ[EmailNotifier.ENV_SMPT_USER] = 'user'
    en = EmailNotifier(settings=settings, settings_last_modified=settings_last_modified, dry_mode=True)
    assert en.validate_settings()


@pytest.mark.parametrize('ssl', [None, True, False])
def test_valid_settings(ssl):
    settings, settings_last_modified = get_valid_settings(ssl=ssl)
    en = EmailNotifier(settings=settings, settings_last_modified=settings_last_modified, dry_mode=True)
    assert en.validate_settings()
