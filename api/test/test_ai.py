import os
import pytest
import yaml
from ai import AIPrompter
from api_utils import load_settings, SETTINGS_FILEPATH


def get_valid_settings(ssl=None):
    settings, settings_last_modified = load_settings(None, None)
    ai_section = AIPrompter.SETTINGS_AI_SECTION
    settings[ai_section] = {}
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_HOST] = "host"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_PORT] = "1234"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_MODEL] = "phi3.5"
    settings[ai_section][AIPrompter.SETTINGS_AI_FIELD_TOKEN] = "token"
    return settings, settings_last_modified


def save_settings(settings=None):
    if settings:
        with open(SETTINGS_FILEPATH, 'w') as f:
            yaml.dump(settings, f, default_flow_style=False)


def delete_env_variables():
    env_props = [
        AIPrompter.ENV_AI_HOST,
        AIPrompter.ENV_AI_PORT,
        AIPrompter.ENV_AI_API_VERSION,
        AIPrompter.ENV_AI_MODEL,
        AIPrompter.ENV_AI_TEMPERATURE,
        AIPrompter.ENV_AI_TOKEN,
        AIPrompter.ENV_AI_MAX_TOKENS]
    for key in env_props:
        if key in os.environ:
            del os.environ[key]


def test_wrong_settings():
    # In case the api/configs/settings.yaml doesn't have a correct ai definition
    delete_env_variables()

    settings = {AIPrompter.SETTINGS_AI_SECTION: {}}
    save_settings(settings)

    ai_prompter = AIPrompter(settings=None, settings_last_modified=None)
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

    # Update the settings file with a valid ai definition
    settings, settings_last_modified = load_settings(None, None)
    settings["ai"] = {"host": "http://localhost",
                      "port": 8808,
                      "model": "deepseek-r1:1.5b",
                      "temperature": 0.3,
                      "token": ""}

    save_settings(settings)
    ai_prompter = AIPrompter(settings=None, settings_last_modified=None)
    assert ai_prompter.validate_settings()

    # clean up
    del settings["ai"]
    save_settings(settings)
