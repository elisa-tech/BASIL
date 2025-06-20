#! /bin/python3
import os
import json
import re
import requests
import time
import traceback
import yaml

from api_utils import get_api_specification
from testrun_base import TestRunnerBasePlugin


class TestRunnerLAVAPlugin(TestRunnerBasePlugin):
    """
    Plugin to run test job from BASIL to a LAVA instance
    https://validation.linaro.org/
    """

    # Constants
    config_mandatory_fields = ["private_token", "url"]
    HTTP_REQUEST_TIMEOUT = 30
    WAIT_INTERVAL = 60 * 1  # seconds
    DEFAULT_JOB_FILENAME = "lava-job.yaml"

    # Variables
    artifacts = []
    result_overall_map_result = {}
    prepare_log = "PREPARATION\n"
    execution_log = "EXECUTION\n"
    local_status = None
    test_case_name = ""

    api_base_url = ""
    owner = ""
    repo = ""
    uuid = ""
    request_id = ""
    valid_job = False

    # Api endpoints
    job_trigger_endpoint = ""
    job_state_endpoint = ""
    test_result_endpoint = ""

    headers = {
        "Authorization": "Token ",
        "Content-Type": "application/json"
    }

    LAVA_STATUS = [
        "Submitted",
        "Scheduling",
        "Scheduled",
        "Running",
        "Canceling",
        "Finished"
    ]

    LAVA_RESULTS = ["pass", "fail", "skip", "unknown"]

    ENDING_STATUS = ["Canceling", "Finished"]

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        self.result_overall_map_result = {"pass": self.runner.RESULT_PASS,
                                          "fail": self.runner.RESULT_FAIL,
                                          "skip": self.runner.RESULT_FAIL,
                                          "unknown": self.runner.RESULT_FAIL}

        # Api endpoints
        if self.config['url'].endswith("/"):
            self.config['url'] = self.config['url'][:-1]
        self.update_api_endpoints()

        # Load Job file
        if not self.config.get("job", None):
            self.config["job"] = os.path.join(self.currentdir, self.DEFAULT_JOB_FILENAME)

        try:
            job_config = get_api_specification(self.config["job"])
        except Exception as e:
            self.throw_error(f"Unable to read job file - {e}\n",
                             self.VALIDATION_ERROR_NUM)

        try:
            self.payload = yaml.safe_load(job_config)
        except yaml.YAMLError as e:
            self.throw_error(f"Unable to read job file - {e}\n",
                             self.VALIDATION_ERROR_NUM)

        self.test_case_name = self.generate_lava_test_case_name(self.runner.mapping.test_case.title)

        # Populate token from config
        self.headers["Authorization"] += self.config["private_token"]

        # Extend job definition adding environment variables and test
        self.payload.setdefault('environment', {}).update({'uid': self.runner.db_test_run.uid})
        self.payload["environment"]["basil_test_case_id"] = self.runner.mapping.test_case.id
        self.payload["environment"]["basil_test_case_title"] = self.runner.mapping.test_case.title
        self.payload["environment"]["basil_test_case_lava_title"] = self.test_case_name
        self.payload["environment"]["basil_api_api"] = self.runner.db_test_run.api.api
        self.payload["environment"]["basil_api_library"] = self.runner.db_test_run.api.library
        self.payload["environment"]["basil_api_library_version"] = \
            self.runner.db_test_run.api.library_version
        self.payload["environment"]["basil_test_case_mapping_table"] = \
            self.runner.db_test_run.mapping_to
        self.payload["environment"]["basil_test_case_mapping_id"] = self.runner.db_test_run.mapping_id
        self.payload["environment"]["basil_test_relative_path"] = \
            self.runner.mapping.test_case.relative_path
        self.payload["environment"]["basil_test_repo_path"] = self.runner.mapping.test_case.repository
        self.payload["environment"]["basil_test_repo_url"] = self.runner.mapping.test_case.repository
        self.payload["environment"]["basil_test_repo_ref"] = self.config.get("git_repo_ref", None)
        self.payload["environment"]["basil_test_run_id"] = self.runner.db_test_run.uid
        self.payload["environment"]["basil_test_run_title"] = self.runner.db_test_run.title
        self.payload["environment"]["basil_test_run_config_id"] = self.config["id"]
        self.payload["environment"]["basil_test_run_config_title"] = self.config["title"]
        self.payload["environment"]["basil_user_username"] = self.runner.db_test_run.created_by.username

        test_config = {
            "repository": self.runner.mapping.test_case.repository,
            "from": "git",
            "path": self.runner.mapping.test_case.relative_path,
            "name": self.test_case_name,
        }

        if self.config.get("git_repo_ref", None):
            test_config["branch"] = self.config["git_repo_ref"]

        if "actions" not in self.payload.keys():
            self.throw_error("Missed 'actions' definition in Job file\n", self.VALIDATION_ERROR_NUM)

        self.payload["actions"].append({"test": {"definitions": [test_config]}})

        if len(self.config["env"].keys()) > 0:
            for k, v in self.config["env"].items():
                if len(str(v)):
                    self.payload["environment"][k] = v

        self.append_log(self.prepare_log)
        self.status_update()

    def match_test_name_in_results(self, test_case_name: str, test_result_dict: dict):
        """LAVA Test Case name in the results starts with a number followed by an underscore"""
        if "name" not in test_result_dict.keys():
            return None
        pattern = rf"^\d+_{re.escape(test_case_name)}$"
        return re.match(pattern, test_result_dict["name"]) is not None

    def generate_lava_test_case_name(self, test_case_name):
        """
        LAVA Test Case name should complies with the regex ^[-_a-zA-Z0-9.]+$
        """
        return re.sub(r'[^-_a-zA-Z0-9.]', '', test_case_name)

    def get_result(self):
        """
        Jobs are monitored using the api endpoint
        and the state variable
        """

        completed = False
        overall_result = ""
        self.execution_log = ""

        iteration = 1
        while not completed:
            try:
                # Update the state and log on each iteration
                response_json = {}
                self.execution_log = ""
                response = requests.get(url=self.job_state_endpoint, headers=self.headers)
                if response.status_code != 200:
                    self.throw_error(f"Unable to read request status from the api at {self.job_state_endpoint}. "
                                     f"Status Code {response.status_code}", self.MONITOR_ERROR_NUM)

                response_json = response.json()
                if "state" not in response_json.keys():
                    self.throw_error("`state` is not in the response",
                                     self.MONITOR_ERROR_NUM)

                self.execution_log += f"request id: {response_json['id']}\n"
                self.execution_log += f"request state: {response_json['state']}\n"

                if response_json["state"] in self.ENDING_STATUS:
                    self.execution_log += f"Job completed with state: {response_json['state']}\n"
                    completed = True

                if not completed:
                    self.execution_log += f"Not completed yet at iteration {iteration}\n"
                    iteration += 1
                    time.sleep(self.WAIT_INTERVAL)
                else:
                    self.execution_log += f"Completed at iteration {iteration}\n"

                self.append_log(self.execution_log)
                self.execution_log = ""
                self.status_update()  # Update the log

            except Exception:
                self.append_log(self.execution_log)
                print(f"Exception: {traceback.format_exc()}")
                self.append_log(f"Exception: {traceback.format_exc()}")
                self.append_log(f"{response_json}")
                self.status_update()  # Update the log
                time.sleep(self.WAIT_INTERVAL)

        response = requests.get(url=self.test_result_endpoint, headers=self.headers)
        if response.status_code != 200:
            self.throw_error(f"Unable to read request result from the api at {self.test_result_endpoint}. "
                             f"Status Code {response.status_code}", self.MONITOR_ERROR_NUM)

        try:
            response_data = response.json()
            if "results" not in response_data.keys():
                self.throw_error(f"Results not available from the api at {self.test_result_endpoint}.",
                                 self.MONITOR_ERROR_NUM)
            tc_results = response_data["results"]
            tc_found = False

            for tc_result in tc_results:
                if self.match_test_name_in_results(self.test_case_name, tc_result):
                    tc_found = True
                    if tc_result["result"] in self.LAVA_RESULTS:
                        overall_result = self.result_overall_map_result.get(tc_result["result"],
                                                                            self.runner.RESULT_FAIL)
                        self.append_log(f"Overall result is: `{overall_result}`")
                    else:
                        overall_result = self.runner.RESULT_FAIL
                        self.append_log(f"Test result `{tc_result['result']}` is unknown --> FAIL")
                    break

            if not tc_found:
                overall_result = self.runner.RESULT_FAIL
                self.append_log(f"Test Case `{self.test_case_name}` not in the result yaml")

        except Exception as ex:
            self.throw_error(f"Unable to read request result. Exception: {ex}\n"
                             f"Status Code {response.status_code}", self.MONITOR_ERROR_NUM)

        self.test_status = self.runner.STATUS_COMPLETED
        self.test_result = overall_result
        self.status_update()

    def update_api_endpoints(self):
        """Update api endpoints
        Examples:
        - Job trigger endpoint: http://localhost:8080/api/v0.2/jobs
        - Job state endpoint: http://localhost:8080/api/v0.2/jobs/123
        - Test result endpoint: http://localhost:8080/api/v0.2/tests
        - Test report: http://localhost:8080/scheduler/job/34
        # """
        self.job_trigger_endpoint = f"{self.config['url']}/jobs/"
        if self.request_id:
            self.job_state_endpoint = f"{self.config['url']}/jobs/{self.request_id}"
            self.test_result_endpoint = f"{self.config['url']}/jobs/{self.request_id}/tests"
            self.test_report = f"{self.config['url'].split('/api/')[0]}/scheduler/job/{self.request_id}"
        else:
            self.job_state_endpoint = ""
            self.test_result_endpoint = ""
            self.test_report = ""

    def cleanup(self):
        pass

    def run(self):
        super().run()

        payload_to_log = self.payload.copy()

        tmp_log = f"LAVA Job payload: {payload_to_log}\n"
        tmp_log += f"LAVA Job endpoint: {self.job_trigger_endpoint}\n"

        response = requests.post(url=self.job_trigger_endpoint,
                                 json={"definition": json.dumps(self.payload)},
                                 headers=self.headers,
                                 timeout=self.HTTP_REQUEST_TIMEOUT)

        f = open("request.log", "w")
        f.write(f"{response.__dict__}")
        f.close()

        response_json = response.json()
        tmp_log += f"Response status code: {response.status_code}\n"

        if response.status_code == 201:
            if 'job_ids' in response_json.keys():
                self.test_status = self.runner.STATUS_RUNNING
                self.request_id = response_json["job_ids"][0]
                self.update_api_endpoints()
                tmp_log += f"STATUS: RUNNING\nLAVA job id: {self.request_id}\n"
            else:
                tmp_log += "ERROR: job_ids not in the response\n"
                tmp_log += f"Response: {response_json}\n"
                self.test_status = self.runner.STATUS_ERROR
                self.test_result = self.runner.RESULT_FAIL
        else:
            tmp_log += f"Response: {response_json}\n"
            self.test_status = self.runner.STATUS_ERROR
            self.test_result = self.runner.RESULT_FAIL

        self.append_log(tmp_log)
        self.status_update()
        if self.test_status == self.runner.STATUS_RUNNING:
            self.get_result()

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
