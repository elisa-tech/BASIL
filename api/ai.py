from openai import OpenAI
import logging
import os
import re
import sys
import urllib

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from api_utils import (
    get_configuration,
    get_available_filepath,
    load_settings,
    normalize_whitespace
)

logger = logging.getLogger(__name__)


class AIPrompter():

    SETTINGS_AI_SECTION = "ai"
    SETTINGS_AI_FIELD_HOST = "host"
    SETTINGS_AI_FIELD_PORT = "port"
    SETTINGS_AI_FIELD_MODEL = "model"
    SETTINGS_AI_FIELD_TEMPERATURE = "temperature"
    SETTINGS_AI_FIELD_TOKEN = "token"
    ENV_AI_HOST = "BASIL_AI_HOST"
    ENV_AI_PORT = "BASIL_AI_PORT"
    ENV_AI_MODEL = "BASIL_AI_MODEL"
    ENV_AI_TEMPERATURE = "BASIL_AI_TEMPERATURE"
    ENV_AI_TOKEN = "BASIL_AI_TOKEN"
    DEFAULT_AI_HOST = None
    DEFAULT_AI_PORT = None
    DEFAULT_AI_MODEL = None
    DEFAULT_AI_TEMPERATURE = 0
    DEFAULT_AI_TOKEN = None

    _tools = []
    _host = None
    _port = None
    _model = None
    _temperature = None
    _token = None
    _base_url = None
    _user_files_base_dir = os.path.join(currentdir, "user-files")

    def __init__(self, settings, settings_last_modified):

        self._host = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_HOST,
            env_key=self.ENV_AI_HOST,
            default_value=self.DEFAULT_AI_HOST,
            settings=settings,
            settings_last_modified=settings_last_modified
        )

        self._port = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_PORT,
            env_key=self.ENV_AI_PORT,
            default_value=self.DEFAULT_AI_PORT,
            settings=settings,
            settings_last_modified=settings_last_modified
        )

        self._model = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_MODEL,
            env_key=self.ENV_AI_MODEL,
            default_value=self.DEFAULT_AI_MODEL,
            settings=settings,
            settings_last_modified=settings_last_modified
        )

        self._temperature = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_TEMPERATURE,
            env_key=self.ENV_AI_TEMPERATURE,
            default_value=self.DEFAULT_AI_TEMPERATURE,
            settings=settings,
            settings_last_modified=settings_last_modified
        )

        self._token = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_TOKEN,
            env_key=self.ENV_AI_TOKEN,
            default_value=self.DEFAULT_AI_TOKEN,
            settings=settings,
            settings_last_modified=settings_last_modified
        )

        if self._host and self._port:
            self._base_url = f"{self._host}:{self._port}/v1"

    def validate_settings(self) -> bool:
        """Validate mandatory fields"""

        if not self._host:
            logger.warning("Error. `AI host` is not configured")
            return False

        if not self._port:
            logger.warning("Error. `AI port` is not configured")
            return False

        if not self._model:
            logger.warning("Error. `AI model` is not configured")
            return False

        logger.info("AIPromter settings are valid")
        return True

    def remove_markdown_formatting(self, text: str) -> str:
        """
        Remove Markdown prefix/suffix from AI-generated text.
        """
        # Remove markdown-style code block markers
        text = text.strip()

        # Case 1: Fenced with ```yaml
        if text.startswith("```yaml"):
            text = re.sub(r"^```yaml\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        elif text.startswith("```"):
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    def ai_health_check(self):
        url = f"{self._base_url}/models"

        req = urllib.request.Request(url, method="GET")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=1) as resp:
                status = resp.getcode()
                if status == 200:
                    return True
                else:
                    logger.error(f"⚠️ AIPromter health check failed: {url} response {status}")
                    return False
        except urllib.error.HTTPError as e:
            # Server responded with an error (e.g. 401 Unauthorized)
            logger.error(f"❌ AIPrompter ai_health_check - HTTP error: {e.code}")
            return False
        except Exception:
            # Network error, timeout, connection refused, etc.
            logger.error("❌ AIPrompter ai_health_check - Connection failed",)
            return False

    def strip_outer_quotes(self, value: str) -> str:
        """
        Remove matching outer quotes from a string (single or double).
        """
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value

    def extract_block_by_key(self, text: str, key: str) -> str:
        """
        Extracts the block of text corresponding to a key (like 'title') from a YAML-like string.
        It captures everything from 'key:' to the next top-level key or end of text.
        """
        # Build a regex pattern that:
        # - Matches the key at start of a line (possibly with spaces)
        # - Captures all text after the key line, until the next key or end of string
        pattern = rf"^\s*{re.escape(key)}\s*:\s*(.*?)\n(?=\s*\w+\s*:|\Z)"

        match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if match:
            return self.strip_outer_quotes(match.group(1).strip())
        return ""

    def ai_askfor__software_requirement_metadata(self, api="", spec=""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design software requirement for "
            "safety critical software based on given functionality specification.\n"
            "Each software requirement MUST include:\n"
            "- title: a short and meaningful description ot the software requirement\n"
            "- description: detailed description of the software requirement\n"
            "- completeness: integer from 0 to 100\n"
            "- reasoning: step-by-step justification for your requirement.\n"
            "You ONLY output a valid YAML without nested keys."
        )
        user_prompt = (
            f"Design a software requirement for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
        )

        response = self.ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

        content = response.choices[0].message.content
        content = self.remove_markdown_formatting(content)

        ai_suggestion_template = {"title": "", "description": "", "completeness": 0, "reasoning": ""}

        ai_suggestion = {}
        for key in ai_suggestion_template.keys():
            ai_suggestion[key] = self.extract_block_by_key(content, key)

        if ai_suggestion["completeness"].endswith("%"):
            ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")

        ai_suggestion["response"] = content

        return ai_suggestion

    def ai_askfor__test_case_implementation(self, api="", title="", spec="", user_id=0):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design test cases for "
            "safety critical software based on given specification.\n"
            "Each test case MUST include an implementation proposal in the programming language "
            "you think more appropriate in a single file.\n"
            "AVOID adding extra explaination or text as you output, "
            "put all your reasoning into the file as comment."
        )
        user_prompt = (
            f"Design a test case for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
            "Provide a test case implementation proposal."
        )
        response = self.ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

        content = response.choices[0].message.content
        content = self.remove_markdown_formatting(content)

        filename = title.replace(" ", "_").lower().strip()
        filepath = os.path.join(self._user_files_base_dir, f"{user_id}", f"{filename}.ai")
        filepath = get_available_filepath(filepath=filepath)

        f = open(filepath, "w")
        f.write(content)
        f.close()

        ai_suggestion = {"filepath": filepath}
        ai_suggestion["response"] = content

        return ai_suggestion

    def ai_askfor__test_case_metadata(self, api="", spec=""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design test cases for"
            "safety critical software based on given specification.\n"
            "Each test case must include the following fields:\n"
            "- title: a short, meaningful test description\n"
            "- description: detailed test case description, with steps and goals\n"
            "- completeness: integer from 0 to 100\n"
            "- reasoning: step-by-step justification for your test.\n"
            "You ONLY output a valid YAML without nested keys."
        )
        user_prompt = (
            f"Design a test case for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
        )

        response = self.ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

        content = response.choices[0].message.content
        content = self.remove_markdown_formatting(content)

        ai_suggestion_template = {"title": "", "description": "", "completeness": 0, "reasoning": ""}

        ai_suggestion = {}
        for key in ai_suggestion_template.keys():
            ai_suggestion[key] = self.extract_block_by_key(content, key)

        if ai_suggestion["completeness"].endswith("%"):
            ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")

        ai_suggestion["response"] = content

        return ai_suggestion

    def ai_askfor__test_specification_metadata(self, api="", spec=""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant helping to design test specifications for "
            "safety-critical software based on given requirements.\n"
            "Each test specification must include the following fields:\n"
            "- title: a short, meaningful test description\n"
            "- preconditions: system state before test execution\n"
            "- test_description: detailed test maneuvers\n"
            "- expected_behavior: the system's expected response\n"
            "- completeness: integer from 0 to 100\n"
            "- reasoning: step-by-step justification for your test. \n"
            "You ONLY output a valid YAML without nested keys."
        )
        user_prompt = (
            f"Design a test specification based on the following requirement: '{spec_prompt}'\n"
            f"This relates to the software functionality named '{api}'."
        )

        response = self.ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

        content = response.choices[0].message.content
        content = self.remove_markdown_formatting(content)

        ai_suggestion_template = {
            "title": "",
            "preconditions": "",
            "test_description": "",
            "expected_behavior": "",
            "completeness": 0,
            "reasoning": "",
        }

        ai_suggestion = {}
        for key in ai_suggestion_template.keys():
            ai_suggestion[key] = self.extract_block_by_key(content, key)

        if ai_suggestion["completeness"].endswith("%"):
            ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")

        ai_suggestion["response"] = content

        return ai_suggestion

    def ai_askfor(self, system_prompt="", user_prompt=""):
        client = OpenAI(
            base_url=self._base_url,
            api_key=self._token if self._token else "empty",
        )

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        logger.info(f"AIPrompter ai_askfor messages: {messages}")

        response = client.chat.completions.create(
            model=self._model,
            temperature=0.1,
            top_p=0.9,
            max_tokens=800,
            messages=messages
        )
        return response


if __name__ == "__main__":
    spec = "The cruise control system must deactivate if the driver presses the brake pedal for more than 1 second."
    settings, settings_last_modified = load_settings(None, None)
    ai_prompter = AIPrompter(settings=settings, settings_last_modified=settings_last_modified)
    ai_prompter.ai_askfor__test_specification_metadata(spec=spec)
