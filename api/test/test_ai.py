import os
import pytest
from ai import AIPrompter
from api_utils import load_settings


def get_valid_settings(ssl=None):
    settings, settings_last_modified = load_settings(None, None)
    ai_section = AIPrompter.SETTINGS_AI_SECTION
    settings[ai_section] = {}
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_HOST] = "host"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_PORT] = "1234"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_MODEL] = "phi3.5"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_TOKEN] = "token"
    return settings, settings_last_modified


@pytest.mark.parametrize('mandatory_field', [
    AIPrompter.SETTINGS_AI_FIELD_HOST,
    AIPrompter.SETTINGS_AI_FIELD_PORT,
    AIPrompter.SETTINGS_AI_FIELD_MODEL])
def test_wrong_settings(mandatory_field):
    ai_prompter = AIPrompter(settings=None, settings_last_modified=None)
    assert not ai_prompter.validate_settings()

    # remove a mandatory field from valid setting
    settings, settings_last_modified = get_valid_settings()
    del settings[AIPrompter.SETTINGS_AI_SECTION][mandatory_field]
    ai_prompter = AIPrompter(settings=settings, settings_last_modified=settings_last_modified)
    assert not ai_prompter.validate_settings()


@pytest.mark.parametrize('mandatory_field', [
    AIPrompter.SETTINGS_AI_FIELD_HOST,
    AIPrompter.SETTINGS_AI_FIELD_PORT,
    AIPrompter.SETTINGS_AI_FIELD_MODEL])
def test_wrong_settings_but_env(mandatory_field):
    """settings are not providing a field but it is defined in the env variables"""
    # remove a mandatory field from valid setting
    settings, settings_last_modified = get_valid_settings()
    del settings[AIPrompter.SETTINGS_AI_SECTION][mandatory_field]
    # populate env variables
    os.environ[AIPrompter.ENV_AI_HOST] = 'host'
    os.environ[AIPrompter.ENV_AI_PORT] = '1234'
    os.environ[AIPrompter.ENV_AI_MODEL] = 'phi3.5'
    ai_prompter = AIPrompter(settings=settings, settings_last_modified=settings_last_modified)
    assert ai_prompter.validate_settings()


def test_valid_settings():
    settings, settings_last_modified = get_valid_settings()
    ai_prompter = AIPrompter(settings=settings, settings_last_modified=settings_last_modified)
    assert ai_prompter.validate_settings()
