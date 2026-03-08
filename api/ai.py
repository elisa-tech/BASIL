from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
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


class AIResponseSwRequirementModel(BaseModel):
    schema_name: str = "software_requirement"
    title: str = Field(..., description="Short and meaningful description ot the software requirement")
    description: str = Field(..., description="Detailed software requirement statement")
    completeness: int = Field(..., description="The completeness of the software requirement, integer from 0 to 100")
    reasoning: str = Field(..., description="The reasoning of the software requirement")


class AIResponseTestCaseModel(BaseModel):
    schema_name: str = "test_case"
    title: str = Field(..., description="Short and meaningful test description")
    description: str = Field(..., description="Detailed test case description, with steps and goals")
    completeness: int = Field(..., description="The completeness of the test case, integer from 0 to 100")
    reasoning: str = Field(..., description="The reasoning of the test case")


class AIResponseTestCaseImplementationModel(BaseModel):
    schema_name: str = "test_case_implementation"
    implementation: str = Field(..., description="Test Case implementation developed as a single file")


class AIResponseTestSpecificationModel(BaseModel):
    schema_name: str = "test_specification"
    title: str = Field(..., description="Short and meaningful test description")
    preconditions: str = Field(..., description="System state before test execution")
    test_description: str = Field(..., description="Detailed test maneuvers")
    expected_behavior: str = Field(..., description="The system's expected response")
    completeness: int = Field(..., description="The completeness of the test specification, integer from 0 to 100")
    reasoning: str = Field(..., description="The reasoning of the test specification")


class AIPrompter():

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"

    SETTINGS_AI_SECTION = "ai"
    SETTINGS_AI_FIELD_HOST = "host"
    SETTINGS_AI_FIELD_API_VERSION = "api_version"
    SETTINGS_AI_FIELD_PORT = "port"
    SETTINGS_AI_FIELD_MODEL = "model"
    SETTINGS_AI_FIELD_TEMPERATURE = "temperature"
    SETTINGS_AI_FIELD_TOKEN = "token"
    SETTINGS_AI_FIELD_MAX_TOKENS = "max_tokens"
    ENV_AI_HOST = "BASIL_AI_HOST"
    ENV_AI_PORT = "BASIL_AI_PORT"
    ENV_AI_MODEL = "BASIL_AI_MODEL"
    ENV_AI_API_VERSION = "BASIL_AI_API_VERSION"
    ENV_AI_TEMPERATURE = "BASIL_AI_TEMPERATURE"
    ENV_AI_TOKEN = "BASIL_AI_TOKEN"
    ENV_AI_MAX_TOKENS = "BASIL_AI_MAX_TOKENS"
    DEFAULT_AI_HOST = None
    DEFAULT_AI_API_VERSION = "v1"
    DEFAULT_AI_PORT = None
    DEFAULT_AI_MODEL = None
    DEFAULT_AI_TEMPERATURE = 0
    DEFAULT_AI_TOKEN = None
    DEFAULT_AI_MAX_TOKENS = 4096

    _tools = []
    _host = None
    _port = None
    _api_version = None
    _model = None
    _temperature = None
    _token = None
    _base_url = None
    _user_files_base_dir = os.path.join(currentdir, "user-files")
    _max_tokens = None

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

        self._api_version = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_API_VERSION,
            env_key=self.ENV_AI_API_VERSION,
            default_value=self.DEFAULT_AI_API_VERSION,
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

        self._max_tokens = get_configuration(
            setting_section=self.SETTINGS_AI_SECTION,
            setting_key=self.SETTINGS_AI_FIELD_MAX_TOKENS,
            env_key=self.ENV_AI_MAX_TOKENS,
            default_value=self.DEFAULT_AI_MAX_TOKENS,
            settings=settings,
            settings_last_modified=settings_last_modified
        )
        if self._max_tokens is not None:
            self._max_tokens = int(self._max_tokens)
        else:
            self._max_tokens = self.DEFAULT_AI_MAX_TOKENS

        self._host = str(self._host).rstrip("/")
        self._api_version = str(self._api_version).rstrip("/")

        if self._host and self._port:
            self._base_url = f"{self._host}:{self._port}/{self._api_version}"

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
        elif text.startswith("```json"):
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        elif text.startswith("```"):
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    def ai_health_check(self):
        url = f"{self._base_url}/models"
        req = urllib.request.Request(url, method="GET")

        if self._base_url.startswith(self.GEMINI_BASE_URL):
            req.add_header("x-goog-api-key", self._token)

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

    def _parse_response_content(self, content: str, model_class: type[BaseModel]):
        """
        Normalize AI response (strip markdown) and parse as the given Pydantic model.
        On invalid or truncated JSON, log a snippet and re-raise.
        """
        if not content or not content.strip():
            raise ValueError("AI returned empty content")
        raw = content
        content = self.remove_markdown_formatting(content)
        try:
            return model_class.model_validate_json(content)
        except PydanticValidationError:
            snippet = raw[:400] + "..." if len(raw) > 400 else raw
            logger.error(
                "AI response was invalid or truncated (e.g. max_tokens). "
                "Snippet: %s",
                snippet,
                exc_info=True,
            )
            raise

    def ai_askfor__software_requirement_metadata(self, api: str = "", spec: str = ""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design software requirement for "
            "safety critical software based on given functionality specification.\n"
        )
        user_prompt = (
            f"Design a software requirement for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
        )

        response = self.ai_askfor(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=AIResponseSwRequirementModel
        )

        content = response.choices[0].message.content
        software_requirement = self._parse_response_content(content, AIResponseSwRequirementModel)
        return software_requirement.model_dump()

    def ai_askfor__test_case_implementation(self, api: str = "", title: str = "", spec: str = "", user_id: int = 0):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design test cases for "
            "safety critical software based on given specification."
        )
        user_prompt = (
            f"Design a test case for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
            "Provide a test case implementation proposal in the programming language "
            "you think more appropriate in a single file."
        )
        response = self.ai_askfor(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=AIResponseTestCaseImplementationModel
        )

        content = response.choices[0].message.content
        test_case_implementation = self._parse_response_content(content, AIResponseTestCaseImplementationModel)

        filename = title.replace(" ", "_").lower().strip()
        filepath = os.path.join(self._user_files_base_dir, f"{user_id}", f"{filename}.ai")
        filepath = get_available_filepath(filepath=filepath)

        f = open(filepath, "w")
        f.write(test_case_implementation.implementation)
        f.close()

        return {
            "filepath": filepath,
            "response": test_case_implementation.implementation
        }

    def ai_askfor__test_case_metadata(self, api: str = "", spec: str = ""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant that helps design test cases for"
            "safety critical software based on given specification.\n"
        )
        user_prompt = (
            f"Design a test case for this software specification: '{spec_prompt}', "
            f"that is related to the software functionality named '{api}'."
        )

        response = self.ai_askfor(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=AIResponseTestCaseModel
        )

        content = response.choices[0].message.content
        test_case = self._parse_response_content(content, AIResponseTestCaseModel)
        return test_case.model_dump()

    def ai_askfor__test_specification_metadata(self, api: str = "", spec: str = ""):
        spec_prompt = self.strip_outer_quotes(normalize_whitespace(spec))
        system_prompt = (
            "You are an AI assistant helping to design test specifications for "
            "safety-critical software based on given requirements.\n"
        )
        user_prompt = (
            f"Design a test specification based on the following requirement: '{spec_prompt}'\n"
            f"This relates to the software functionality named '{api}'."
        )

        response = self.ai_askfor(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=AIResponseTestSpecificationModel
        )

        content = response.choices[0].message.content
        test_specification = self._parse_response_content(content, AIResponseTestSpecificationModel)
        return test_specification.model_dump()

    def ai_askfor(self, system_prompt: str = "", user_prompt: str = "", response_format: BaseModel = None):
        if self._base_url.startswith(self.GEMINI_BASE_URL):
            url = f"{self._base_url}/openai"
        else:
            url = f"{self._base_url}"

        client = OpenAI(
            base_url=url,
            api_key=self._token if self._token else "empty",
        )

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        logger.info(f"AIPrompter ai_askfor messages: {messages}")

        schema = response_format.model_json_schema()
        schema_name = schema.get("properties", {}).get("schema_name", {}).get("default", "json_schema")

        response = client.chat.completions.create(
            model=self._model,
            temperature=0.1,
            top_p=0.9,
            max_tokens=self._max_tokens,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema
                }
            }
        )
        return response


if __name__ == "__main__":
    spec = "The cruise control system must deactivate if the driver presses the brake pedal for more than 1 second."
    settings, settings_last_modified = load_settings(None, None)
    ai_prompter = AIPrompter(settings=settings, settings_last_modified=settings_last_modified)
    ai_prompter.ai_askfor__test_specification_metadata(spec=spec)
