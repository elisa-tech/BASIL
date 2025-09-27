#! /bin/python3
import logging
import time

import requests
from testrun_base import TestRunnerBasePlugin

logger = logging.getLogger(__name__)


class TestRunnerGithubActionsPlugin(TestRunnerBasePlugin):

    # To get the dispatched request ID we need to implement an input
    # in the workflow file as described at
    # https://github.com/orgs/community/discussions/9752
    #
    # Once the ID will be returned by the API we can change the current
    # implementation, reducing the configuration work for BASIL users

    # Constants
    config_mandatory_fields = ["private_token", "url"]
    HTTP_REQUEST_TIMEOUT = 30
    WAIT_INTERVAL = 60 * 1  # seconds
    SLEEP_DISPATCH = 30  # seconds

    # Variables
    artifacts = []
    conclusion_map_result = {}
    prepare_log = "PREPARATION\n"
    execution_log = "EXECUTION\n"
    local_status = None

    api_base_url = ""
    owner = ""
    repo = ""
    uuid = ""
    workflow_id = ""
    valid_job = False

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer ",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        self.conclusion_map_result = {
            "success": self.runner.RESULT_PASS,
            "failure": self.runner.RESULT_FAIL,
            "neutral": self.runner.RESULT_FAIL,
            "cancelled": self.runner.RESULT_FAIL,
            "skipped": self.runner.RESULT_FAIL,
            "timed_out": self.runner.RESULT_FAIL,
            "action_required": self.runner.RESULT_FAIL,
        }
        optional_fields = ["job"]

        self.headers["Authorization"] += self.config["private_token"]

        # Log optional fields
        for f in optional_fields:
            if f in self.config.keys():
                if self.config[f]:
                    self.prepare_log += f"{f}: {self.config[f]}\n"

        self.append_log(self.prepare_log)
        self.status_update()

    def get_result(self):
        """
        Jobs are monitored using the jobs_url endpoint of github
        at that endpoint jobs are visible only when they start.
        So, if user specify a job name, and the job is not the first of the pipeline,
        you cannot see it at first iterations and need to wait without raising
        exceptions.
        An exceptions can be raised if the job is not in the endpoint when the
        overall workflows end.

        If the job name is not populated, we cannot iterate over all jobs because
        those are incrementally added to the jobs_url.
        We have to rely on the workflow conclusion field.
        """

        completed = False
        overall_result = ""

        self.execution_log += f"job defined: {str(self.valid_job)}\n"
        self.append_log(self.execution_log)
        self.execution_log = ""

        workflow_url = (
            f"{self.api_base_url}/runs?branch={self.config['git_repo_ref']}"
            f"&workflow_id={self.workflow_id}"
            f"&event=workflow_dispatch"
        )
        self.test_report = workflow_url

        iteration = 1
        while not completed:
            try:
                # Update the job status and log on each iteration
                self.execution_log = ""
                workflow_response = requests.get(url=workflow_url, headers=self.headers)
                if workflow_response.status_code != 200:
                    self.throw_error(
                        f"Unable to read workflow runs. Status Code {workflow_response.status_code}",
                        self.MONITOR_ERROR_NUM,
                    )

                if "workflow_runs" not in workflow_response.json().keys():
                    self.throw_error("workflow_runs is not in the response", self.MONITOR_ERROR_NUM)

                if not workflow_response.json()["workflow_runs"]:
                    self.throw_error("workflow_runs is empty", self.MONITOR_ERROR_NUM)

                workflow_runs = workflow_response.json()["workflow_runs"]
                workflow_runs = [x for x in workflow_runs if self.uuid in x["name"]]

                workflow_run = workflow_runs[0]
                self.execution_log += f"workflow run id: {workflow_run['id']}\n"
                self.execution_log += f"workflow run status: {workflow_run['status']}\n"
                self.execution_log += f"workflow run conclusion: {workflow_run['conclusion']}\n"
                self.execution_log += f"workflow run jobs url: {workflow_run['jobs_url']}\n"

                if not self.valid_job:
                    if workflow_run["conclusion"]:
                        overall_result = self.conclusion_map_result[workflow_run["conclusion"]]
                        completed = True
                else:
                    jobs_url = workflow_run["jobs_url"]

                    jobs_response = requests.get(url=jobs_url)
                    if jobs_response.status_code != 200:
                        self.throw_error(
                            f"Unable to read jobs. Status Code {jobs_response.status_code}", self.MONITOR_ERROR_NUM
                        )

                    if "jobs" not in jobs_response.json().keys():
                        self.throw_error("`jobs` is not in the response", self.MONITOR_ERROR_NUM)

                    if not jobs_response.json()["jobs"]:
                        self.throw_error("Job list is empty", self.MONITOR_ERROR_NUM)

                    jobs = jobs_response.json()["jobs"]
                    self.execution_log += f"jobs: {' - '.join([x['name'] for x in jobs])}\n"
                    job_exists = False

                    for job in jobs:
                        if job["name"] == self.config["job"]:
                            self.execution_log += f"target job {self.config['job']} status: {job['status']}\n"
                            job_exists = True
                            if job["status"] == "completed":
                                completed = True
                                overall_result = self.conclusion_map_result[job["conclusion"]]
                                break

                    if not job_exists:
                        if workflow_run["conclusion"]:
                            self.throw_error("Selected job is not part of the workflow", self.MONITOR_ERROR_NUM)

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

            except Exception as e:
                logger.error(f"Exception: {e}")
                self.append_log(f"Exception: {e}")
                self.status_update()  # Update the log

        self.test_status = self.runner.STATUS_COMPLETED
        self.test_result = overall_result
        self.status_update()

    def cleanup(self):
        pass

    def run(self):
        super().run()

        data = {"ref": self.config["git_repo_ref"], "inputs": self.config["env"]}

        # Add and override config inputs
        if "inputs" in self.config.keys():
            for k, v in self.config["inputs"].items():
                data["inputs"][k] = v

        # Remove delay from the inputs
        if "delay" in data["inputs"].keys():
            del data["inputs"]["delay"]

        if "uuid" not in data["inputs"].keys():
            data["inputs"]["uuid"] = self.runner.config["uid"]
            self.uuid = self.runner.config["uid"]
        else:
            self.uuid = data["inputs"]["uuid"]

        self.append_log(f"CI trigger payload: {data}")

        trigger_url = f"{self.api_base_url}/workflows/{self.workflow_id}/dispatches"
        response = requests.post(url=trigger_url, json=data, headers=self.headers, timeout=self.HTTP_REQUEST_TIMEOUT)

        if response.status_code == 204:
            self.test_status = self.runner.STATUS_RUNNING
            self.status_update()
            time.sleep(self.SLEEP_DISPATCH)
            self.get_result()
        else:
            self.test_status = self.runner.STATUS_ERROR
            self.test_result = self.runner.RESULT_FAIL
            self.status_update()

    def validate(self):
        # Validate mandatory fields
        for f in self.config_mandatory_fields:
            if f not in self.config.keys():
                self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n", self.VALIDATION_ERROR_NUM)
            else:
                if not self.config[f]:
                    self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n", self.VALIDATION_ERROR_NUM)

        # Expected url format examples:
        # - https://github.com/elisa-tech/BASIL
        # - https://github.com/elisa-tech/BASIL/
        # - https://github.com/elisa-tech/BASIL.git
        # - https://github.com/elisa-tech/BASIL.git/
        if self.config["url"].endswith("/"):
            self.config["url"] = self.config["url"][:-1]
        if self.config["url"].endswith(".git"):
            self.config["url"] = self.config["url"][:-4]

        if "workflow_id" in self.config.keys():
            if self.config["workflow_id"]:
                self.workflow_id = self.config["workflow_id"]
        if not self.workflow_id:
            self.throw_error("Github workflow_id is not valid", self.VALIDATION_ERROR_NUM)

        url_split = self.config["url"].split("/")
        if len(url_split) < 2:
            self.throw_error("Github repository url is not valid", self.VALIDATION_ERROR_NUM)

        self.owner = url_split[-2]
        self.repo = url_split[-1]
        self.api_base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/actions"

        if "job" in self.config.keys():
            if isinstance(self.config["job"], str):
                if len(self.config["job"].strip()):
                    self.valid_job = True
