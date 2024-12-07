#! /bin/python3
import json
import time

import gitlab
import requests
from testrun_base import TestRunnerBasePlugin


class TestRunnerGitlabCIPlugin(TestRunnerBasePlugin):

    # Constants
    config_mandatory_fields = ["private_token", "project_id", "trigger_token", "url"]
    HTTP_REQUEST_TIMEOUT = 30
    WAIT_INTERVAL = 60 * 1  # seconds

    # Variables
    artifacts = []
    status_map_result = {}
    job_id = None
    pipeline_id = None
    project_pipeline_url = None
    project_job_url = None
    prepare_log = "PREPARATION\n"
    execution_log = "EXECUTION\n"
    local_status = None

    valid_job = False
    valid_stage = False

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        if self.config['url'].endswith("/"):
            self.config['url'] = self.config['url'][:-1]
        self.project_pipeline_url = f"{self.config['url']}/api/v4/projects/" \
                                    f"{self.config['project_id']}/trigger/pipeline"

        self.status_map_result = {"failed": self.runner.RESULT_FAIL,
                                  "warning": None,
                                  "pending": None,
                                  "running": None,
                                  "manual": None,
                                  "scheduled": None,
                                  "canceled": self.runner.RESULT_FAIL,
                                  "success": self.runner.RESULT_PASS,
                                  "skipped": self.runner.RESULT_FAIL,
                                  "created": None, }

        optional_fields = ["stage", "job"]

        # Log optional fields
        for f in optional_fields:
            if f in self.config.keys():
                if self.config[f]:
                    self.prepare_log += f"{f}: {self.config[f]}\n"

        self.prepare_log += f"pipeline_url: {self.project_pipeline_url}\n"
        self.append_log(self.prepare_log)
        self.status_update()

    def connect(self):
        project = None
        try:
            gl = gitlab.Gitlab(url=self.config["url"],
                               private_token=self.config["private_token"])
            gl.auth()
            project = gl.projects.get(id=self.config["project_id"])
        except Exception as e:
            self.throw_error(f"Unable to connect to gitlab instance {e}",
                             self.MONITOR_ERROR_NUM)
        return project

    def log_pipeline_job(self, pipeline_job):
        self.execution_log += f"\n-> Job {pipeline_job.id} {pipeline_job.name}: `{pipeline_job.status}`"

    def get_result(self):
        """
        if the job name is not populated, all the jobs of the stage have to pass
        if the stage name is not populated all the pipeline jobs have to pass
        """

        completed = False
        self.execution_log += f"stage defined: {str(self.valid_stage)}\n"
        self.execution_log += f"job defined: {str(self.valid_job)}\n"
        self.append_log(self.execution_log)

        project = self.connect()

        if not project:
            self.throw_error("Unable to connect to gitlab instance",
                             self.MONITOR_ERROR_NUM)

        iteration = 1
        while not completed:
            try:
                # Update the job status and log on each iteration

                if self.valid_stage:
                    if self.valid_job:
                        pipeline_job = None
                        if self.job_id:
                            # Already know the pipeline job id
                            pipeline_job = project.jobs.get(self.job_id)
                            self.local_status = pipeline_job.status
                            self.log_pipeline_job(pipeline_job)
                        else:
                            # First iteration, don't know the pipeline job id
                            pipeline = project.pipelines.get(self.pipeline_id)
                            pipeline_jobs = pipeline.jobs.list()
                            for pjob in pipeline_jobs:
                                if pjob.__dict__["_attrs"]["stage"] == self.config["stage"]:
                                    if pjob.__dict__["_attrs"]["name"] == self.config["job"]:
                                        pipeline_job = pjob
                                        self.job_id = pipeline_job.id
                                        self.log_pipeline_job(pipeline_job)
                                        self.local_status = pipeline_job.status
                                        self.test_report = pjob.__dict__["_attrs"]["web_url"]
                                        break
                        if self.status_map_result.get(pipeline_job.status):
                            completed = True
                    else:
                        # All jobs of the stage have to pass
                        pipeline = project.pipelines.get(self.pipeline_id)
                        self.test_report = pipeline.__dict__["_attrs"]["web_url"]
                        pipeline_jobs = pipeline.jobs.list()
                        completed = True
                        self.local_status = "wait-all"
                        for pipeline_job in pipeline_jobs:
                            if pipeline_job.__dict__["_attrs"]["stage"] == self.config["stage"]:

                                self.log_pipeline_job(pipeline_job)

                                if self.status_map_result.get(pipeline_job.status) == self.runner.RESULT_FAIL:
                                    self.local_status = pipeline_job.status
                                    completed = True
                                    break
                                elif not self.status_map_result.get(pipeline_job.status):
                                    # A job is still running
                                    self.local_status = None
                                    completed = False
                else:
                    # All jobs of all the stages have to pass
                    pipeline = project.pipelines.get(self.pipeline_id)
                    self.test_report = pipeline.__dict__["_attrs"]["web_url"]
                    pipeline_jobs = pipeline.jobs.list()
                    completed = True
                    self.local_status = "wait-all"
                    for pipeline_job in pipeline_jobs:
                        self.log_pipeline_job(pipeline_job)

                        if self.status_map_result.get(pipeline_job.status) == self.runner.RESULT_FAIL:
                            self.local_status = pipeline_job.status
                            completed = True
                            break
                        elif not self.status_map_result.get(pipeline_job.status):
                            # A job is still running
                            self.local_status = None
                            completed = False

                if not completed:
                    self.execution_log = f"Not completed yet at iteration {iteration}"
                    iteration += 1
                    time.sleep(self.WAIT_INTERVAL)

                self.append_log(self.execution_log)
                self.execution_log = ""
                self.status_update()  # Update the log

            except Exception as e:
                print(f"Unable to connect to gitlab: {e}")
                self.append_log(f"Unable to connect to gitlab: {e}")
                self.status_update()  # Update the log

        self.test_status = self.local_status
        if self.test_status == 'wait-all':
            self.test_status = 'success'

        self.test_result = self.status_map_result.get(self.test_status)
        self.status_update()

    def cleanup(self):
        pass

    def run(self):

        super().run()
        data = {"token": self.config["trigger_token"],
                "ref": self.config["git_repo_ref"],
                "variables": self.config["env"]}

        # Hide token in the log
        data_log = data.copy()
        data_log["token"] = "***"
        self.append_log(f"CI trigger payload: {data_log}")

        response = requests.post(self.project_pipeline_url,
                                 json=data,
                                 timeout=self.HTTP_REQUEST_TIMEOUT)

        response_dict = json.loads(response.text)

        if response.status_code == 201 and "id" in response_dict.keys():
            self.pipeline_id = str(response_dict["id"])
            self.test_status = self.runner.STATUS_RUNNING
            self.status_update()
            self.get_result()
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

        if "stage" in self.config.keys():
            if isinstance(self.config["stage"], str):
                if len(self.config["stage"].strip()):
                    self.valid_stage = True

        if "job" in self.config.keys():
            if isinstance(self.config["job"], str):
                if len(self.config["job"].strip()):
                    self.valid_job = True
