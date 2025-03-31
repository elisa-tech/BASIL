#! /bin/python3
import time
import traceback

import requests
from testrun_base import TestRunnerBasePlugin


class TestRunnerTestingFarmPlugin(TestRunnerBasePlugin):

    # Documentation at https://api.dev.testing-farm.io/redoc
    # Supported composes: https://api.dev.testing-farm.io/v0.1/composes

    # Constants
    config_mandatory_fields = ["arch", "compose", "git_repo_ref", "private_token", "url"]
    HTTP_REQUEST_TIMEOUT = 30
    WAIT_INTERVAL = 60 * 1  # seconds
    TMT_PLAN_URL = "https://github.com/elisa-tech/BASIL.git"
    TMT_PLAN_REF = "main"
    TMT_PLAN_NAME = "/api/tmt-plan"

    # Variables
    artifacts = []
    result_overall_map_result = {}
    prepare_log = "PREPARATION\n"
    execution_log = "EXECUTION\n"
    local_status = None

    api_base_url = ""
    owner = ""
    repo = ""
    uuid = ""
    request_id = ""
    valid_job = False

    headers = {
        "Accept": "application/json",
    }

    payload = {
      "api_key": "",
      "test": {
        "fmf": {
          "url": "",
          "ref": "",
          "name": "",
          "test_filter": ""
        }
      },
      "environments": [
        {
          "arch": "",
          "os": {"compose": ""},
          "tmt": {
            "environment": {
            },
            "context": {
            }
          },
          "variables": {
          }
        }
      ]
    }

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        self.result_overall_map_result = {"passed": self.runner.RESULT_PASS,
                                          "failed": self.runner.RESULT_FAIL,
                                          "skipped": self.runner.RESULT_FAIL,
                                          "unknown": self.runner.RESULT_FAIL,
                                          "error": self.runner.RESULT_FAIL}

        self.payload["api_key"] += self.config["private_token"]
        self.payload["environments"][0]["variables"]["uid"] = self.runner.db_test_run.uid
        self.payload["environments"][0]["variables"]["basil_test_case_id"] = self.runner.mapping.test_case.id
        self.payload["environments"][0]["variables"]["basil_test_case_title"] = self.runner.mapping.test_case.title
        self.payload["environments"][0]["variables"]["basil_api_api"] = self.runner.db_test_run.api.api
        self.payload["environments"][0]["variables"]["basil_api_library"] = self.runner.db_test_run.api.library
        self.payload["environments"][0]["variables"]["basil_api_library_version"] = \
            self.runner.db_test_run.api.library_version
        self.payload["environments"][0]["variables"]["basil_test_case_mapping_table"] = \
            self.runner.db_test_run.mapping_to
        self.payload["environments"][0]["variables"]["basil_test_case_mapping_id"] = self.runner.db_test_run.mapping_id
        self.payload["environments"][0]["variables"]["basil_test_relative_path"] = \
            self.runner.mapping.test_case.relative_path
        self.payload["environments"][0]["variables"]["basil_test_repo_path"] = self.runner.mapping.test_case.repository
        self.payload["environments"][0]["variables"]["basil_test_repo_url"] = self.runner.mapping.test_case.repository
        self.payload["environments"][0]["variables"]["basil_test_repo_ref"] = self.config["git_repo_ref"]
        self.payload["environments"][0]["variables"]["basil_test_run_id"] = self.runner.db_test_run.uid
        self.payload["environments"][0]["variables"]["basil_test_run_title"] = self.runner.db_test_run.title
        self.payload["environments"][0]["variables"]["basil_test_run_config_id"] = self.config["id"]
        self.payload["environments"][0]["variables"]["basil_test_run_config_title"] = self.config["title"]
        self.payload["environments"][0]["variables"]["basil_user_email"] = self.runner.db_test_run.created_by.email

        self.payload["test"]["fmf"]["url"] = self.TMT_PLAN_URL
        self.payload["test"]["fmf"]["ref"] = self.TMT_PLAN_REF
        self.payload["test"]["fmf"]["name"] = self.TMT_PLAN_NAME

        self.payload["environments"][0]["arch"] = self.config["arch"]
        self.payload["environments"][0]["os"]["compose"] = self.config["compose"]

        if len(self.config["context"].keys()) > 0:
            for k, v in self.config["context"].items():
                if len(str(v)):
                    self.payload["environments"][0]["tmt"]["context"][k] = v

        if len(self.config["env"].keys()) > 0:
            for k, v in self.config["env"].items():
                if len(str(v)):
                    self.payload["environments"][0]["variables"][k] = v

        self.append_log(self.prepare_log)
        self.status_update()

    def get_result(self):
        """
        Jobs are monitored using the api endpoint
        and the state variable
        """

        completed = False
        overall_result = ""

        self.execution_log = ""
        api_endpoint = f"{self.config['url']}/{self.request_id}"
        self.test_report = api_endpoint

        iteration = 1
        while not completed:
            try:
                # Update the state and log on each iteration
                response_json = {}
                self.execution_log = ""
                response = requests.get(url=api_endpoint, headers=self.headers)
                if response.status_code != 200:
                    self.throw_error(f"Unable to read request status from the api at {api_endpoint}. "
                                     f"Status Code {response.status_code}", self.MONITOR_ERROR_NUM)

                response_json = response.json()
                if "state" not in response_json.keys():
                    self.throw_error("`state` is not in the response",
                                     self.MONITOR_ERROR_NUM)

                self.execution_log += f"request id: {response_json['id']}\n"
                self.execution_log += f"request state: {response_json['state']}\n"

                if "run" in response_json.keys():
                    if isinstance(response_json["run"], dict):
                        if "artifacts" in response_json["run"].keys():
                            if response_json['run']['artifacts']:
                                self.test_report = response_json['run']['artifacts']

                if response_json["state"] in ['complete']:
                    if isinstance(response_json['result'], dict):
                        self.execution_log += f"request result overall: {response_json['result']['overall']}\n"
                        self.execution_log += f"workflow result summary: {response_json['result']['summary']}\n"
                        overall_result = self.result_overall_map_result.get(response_json['result']['overall'],
                                                                            self.runner.RESULT_FAIL)
                        completed = True
                elif response_json["state"] in ['error']:
                    overall_result = 'error'
                    completed = True

                if not completed:
                    self.execution_log += f"Not completed yet at iteration {iteration}\n"
                    iteration += 1
                    time.sleep(self.WAIT_INTERVAL)
                else:
                    self.execution_log += f"Completed at iteration {iteration}\n"
                    self.execution_log += f"Overall result: {overall_result}\n"

                self.append_log(self.execution_log)
                self.execution_log = ""
                self.status_update()  # Update the log

            except Exception:
                print(f"Exception: {traceback.format_exc()}")
                self.append_log(f"Exception: {traceback.format_exc()}")
                self.append_log(f"{response_json}")
                self.status_update()  # Update the log
                time.sleep(self.WAIT_INTERVAL)

        self.test_status = self.runner.STATUS_COMPLETED
        self.test_result = overall_result
        self.status_update()

    def cleanup(self):
        pass

    def run(self):
        super().run()

        payload_to_log = self.payload.copy()
        payload_to_log["api_key"] = "***"  # Hide api key in the log

        self.append_log(f"CI trigger payload: {payload_to_log}")

        response = requests.post(url=self.config['url'],
                                 json=self.payload,
                                 headers=self.headers,
                                 timeout=self.HTTP_REQUEST_TIMEOUT)

        response_json = response.json()
        if response.status_code == 200:
            if 'id' in response_json.keys():
                self.test_status = self.runner.STATUS_RUNNING
                self.request_id = response_json['id']
                self.append_log(f"STATUS: RUNNING\nTesting Farm request id: {self.request_id}")
                self.status_update()
                self.get_result()
            else:
                self.log += "\nid not in the response"
                self.log += f"\nResponse: {response_json}"
                self.test_status = self.runner.STATUS_ERROR
                self.test_result = self.runner.RESULT_FAIL
                self.status_update()
        else:
            self.test_status = self.runner.STATUS_ERROR
            self.test_result = self.runner.RESULT_FAIL
            self.status_update()

    def validate(self):
        # Validate mandatory fields
        for f in self.config_mandatory_fields:
            if f not in self.config.keys():
                self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n",
                                 self.VALIDATION_ERROR_NUM)
            else:
                if not self.config[f]:
                    self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n",
                                     self.VALIDATION_ERROR_NUM)

        # Expected url format examples:
        # - https://api.dev.testing-farm.io/v0.1/requests
        # - https://api.dev.testing-farm.io/v0.1/requests/
        if self.config['url'].endswith("/"):
            self.config['url'] = self.config['url'][:-1]
