from api_utils import get_available_filepath
from openai import OpenAI
import os
import re
import urllib

# Setup your API endpoint (e.g. OpenAI or Ramalama local server)
currentdir = os.path.dirname(os.path.realpath(__file__))
API_BASE_URL = os.environ.get("BASIL_API_URL", "http://localhost")
AI_PORT = os.environ.get("BASIL_AI_PORT", "8080")
AI_API_BASE_URL = f"{API_BASE_URL}:{AI_PORT}/v1"  # For Ramalama
API_KEY = "not-needed"  # Placeholder if keyless
USER_FILES_BASE_DIR = os.path.join(currentdir, "user-files")

# 2. Define available tools (function schema)
tools = []


def remove_markdown_formatting(text: str) -> str:
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


def ai_health_check():
    url = f"{AI_API_BASE_URL}/models"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=1) as resp:
            status = resp.getcode()
            if status == 200:
                return True
            else:
                return False
    except urllib.error.HTTPError as e:
        # Server responded with an error (e.g. 401 Unauthorized)
        print(f"⚠️ HTTP error: {e.code}")
        return False
    except Exception as e:
        # Network error, timeout, connection refused, etc.
        print("❌ Connection failed:", e)
        return False


def strip_outer_quotes(value: str) -> str:
    """
    Remove matching outer quotes from a string (single or double).
    """
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def custom_key_value_parser(text: str, expected_keys: list) -> dict:
    result = {}
    current_key = None
    buffer = []

    for line in text.splitlines():
        # Check if line starts with one of the expected keys
        line = line.rstrip()
        if any(line.startswith(f"{key}:") for key in expected_keys):
            # Save previous key and its value
            if current_key:
                combined = "\n".join(buffer).strip()
                result[current_key] = strip_outer_quotes(combined)

            # Extract new key and initial value
            split_index = line.find(":")
            current_key = line[:split_index].strip()
            initial_value = line[split_index+1:].strip()
            buffer = [initial_value] if initial_value else []
        else:
            # Continuation of previous key's value
            if current_key:
                buffer.append(line)

    # Save the last key/value
    if current_key:
        result[current_key] = "\n".join(buffer).strip()

    for expected_key in expected_keys:
        if expected_key not in result.keys():
            result[expected_key] = ""

    return result


def ai_askfor__software_requirement_metadata(api="", spec=""):
    system_prompt = """You are an AI assistant that helps design software requirement for
 safety critical software based on given functionality specification.
 Each software requirement MUST include:
 - title (text): a meaningful short description ot the requirement
 - description (text): requirement body
 - completeness (integer 0-100): percentage of completeness
 - reasoning (text): your step by step reasoning
"""
    user_prompt = (
        f"Given this software specification: '{spec}' "
        f"for the software functionality '{api}', "
        "respond ONLY with a full set of data: "
        "title, description, "
        "completeness, reasoning."
        "Use a raw YAML format."
        "Keep it short and AVOID adding extra fields or text."
    )

    response = ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

    content = response.choices[0].message.content
    content = remove_markdown_formatting(content)

    ai_suggestion_template = {"title": "", "description": "", "completeness": 0, "reasoning": ""}

    ai_suggestion = custom_key_value_parser(content, ai_suggestion_template.keys())
    if ai_suggestion["completeness"].endswith("%"):
        ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")
    return ai_suggestion


def ai_askfor__test_case_implementation(api="", title="", spec="", user_id=0):
    system_prompt = """You are an AI assistant that helps design test case for
 safety critical software based on given specification.
Each test case MUST include an implementation proposal in the programming language
 you think more appropriate in a single file.
"""
    user_prompt = (
        f"Given this software specification: '{spec}' "
        f"for the software functionality '{api}', "
        "provide a test case implementation proposal."
        "AVOID adding extra explaination or text as you output, "
        "put all your reasoning into the file as comment."
    )
    response = ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

    content = response.choices[0].message.content
    content = remove_markdown_formatting(content)

    filename = title.replace(" ", "_").lower().strip()
    filepath = os.path.join(USER_FILES_BASE_DIR, f"{user_id}", f"{filename}.ai")
    filepath = get_available_filepath(filepath=filepath)

    f = open(filepath, "w")
    f.write(content)
    f.close()

    ai_suggestion = {"filepath": filepath}

    return ai_suggestion


def ai_askfor__test_case_metadata(api="", spec=""):
    system_prompt = """You are an AI assistant that helps design test cases for
 safety critical software based on given specification.
Each test case MUST include:
- title (text): a meaningful short description ot the requirement
- description (text): complete test case description, with steps and goals
- completeness (integer 0-100): percentage of completeness
- reasoning (text): your step by step reasoning
"""
    user_prompt = (
        f"Given this software specification: '{spec}' "
        f"for the software functionality '{api}', "
        "respond ONLY with a full set of data: "
        "title, description, "
        "completeness, reasoning."
        "Use a raw YAML format."
        "Keep it short and AVOID adding extra fields or text."
    )

    response = ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

    content = response.choices[0].message.content
    content = remove_markdown_formatting(content)

    ai_suggestion_template = {"title": "", "description": "", "completeness": 0, "reasoning": ""}

    ai_suggestion = custom_key_value_parser(content, ai_suggestion_template.keys())
    if ai_suggestion["completeness"].endswith("%"):
        ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")
    return ai_suggestion


def ai_askfor__test_specification_metadata(api="", spec=""):
    system_prompt = """You are an AI assistant that helps design test specifications for
 safety critical software based on given requirements.
Each test specification MUST include:
 - title (text): a meaningful short description ot the test specification
 - preconditions (text): system status before starting the test
 - test_description (text): description of the test maneuvers
 - expected_behavior (text): expected response of the system
 - completeness (integer 0-100): percentage of completeness
 - reasoning (text): your step by step reasoning
"""
    user_prompt = (
        f"Given this software requirement: '{spec}' "
        f"for the software functionality '{api}', "
        "respond ONLY with a full set of data: "
        "title, preconditions, test description, expected behavior, "
        "completeness percentage, your reasoning."
        "Respond with raw YAML."
        "Keep it short and AVOID adding extra fields or text."
    )

    response = ai_askfor(system_prompt=system_prompt, user_prompt=user_prompt)

    content = response.choices[0].message.content
    content = remove_markdown_formatting(content)

    ai_suggestion_template = {
        "title": "",
        "preconditions": "",
        "test_description": "",
        "expected_behavior": "",
        "completeness": 0,
        "reasoning": "",
    }

    ai_suggestion = custom_key_value_parser(content, ai_suggestion_template.keys())
    if ai_suggestion["completeness"].endswith("%"):
        ai_suggestion["completeness"] = ai_suggestion["completeness"].rstrip("%")
    return ai_suggestion


def ai_askfor(system_prompt="", user_prompt=""):
    client = OpenAI(
        base_url=AI_API_BASE_URL,
        api_key=API_KEY,  # Most local servers ignore this, but OpenAI client requires a value
    )

    response = client.chat.completions.create(
        model="phi3.5",
        temperature=0,
        top_p=0.9,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        tools=tools,
        tool_choice="auto",
    )
    return response


if __name__ == "__main__":
    spec = "The cruise control system must deactivate if the driver presses the brake pedal for more than 1 second."
    ai_askfor__test_specification_metadata(spec=spec)
