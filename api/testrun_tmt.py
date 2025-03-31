#! /bin/python3
import datetime
import os
import shutil
import subprocess

import yaml
from testrun_base import TestRunnerBasePlugin


class TestRunnerTmtPlugin(TestRunnerBasePlugin):

    # Constants
    config_mandatory_fields = ["provision_type"]
    connect_mandatory_fields = ["provision_guest", "provision_guest_port", "ssh_key_id"]
    plan = 'tmt-plan'
    root_dir = os.getenv('TEST_RUNS_BASE_DIR', '/var/test-runs')  # Same as TEST_RUNS_BASE_DIR defined in api.py

    # Variables
    artifacts = []
    context_str = ""
    environment_str = ""

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        if not os.path.exists(self.root_dir):
            os.mkdir(self.root_dir)

        self.config["env"]["uid"] = self.runner.db_test_run.uid
        self.config["env"]["basil_test_case_id"] = self.runner.mapping.test_case.id
        self.config["env"]["basil_test_case_title"] = self.runner.mapping.test_case.title
        self.config["env"]["basil_api_api"] = self.runner.db_test_run.api.api
        self.config["env"]["basil_api_library"] = self.runner.db_test_run.api.library
        self.config["env"]["basil_api_library_version"] = self.runner.db_test_run.api.library_version
        self.config["env"]["basil_test_case_mapping_table"] = self.runner.db_test_run.mapping_to
        self.config["env"]["basil_test_case_mapping_id"] = self.runner.db_test_run.mapping_id
        self.config["env"]["basil_test_relative_path"] = self.runner.mapping.test_case.relative_path
        self.config["env"]["basil_test_repo_path"] = self.runner.mapping.test_case.repository
        self.config["env"]["basil_test_repo_url"] = self.runner.mapping.test_case.repository
        self.config["env"]["basil_test_repo_ref"] = self.config.get("git_repo_ref", "")
        self.config["env"]["basil_test_run_id"] = self.runner.db_test_run.uid
        self.config["env"]["basil_test_run_title"] = self.runner.db_test_run.title
        self.config["env"]["basil_test_run_config_id"] = self.config["id"]
        self.config["env"]["basil_test_run_config_title"] = self.config["title"]
        self.config["env"]["basil_user_email"] = self.runner.db_test_run.created_by.email

        if len(self.config["context"].keys()) > 0:
            for k, v in self.config["context"].items():
                if len(str(v)):
                    self.context_str += f"-c {k}='\"{v}\"' "

        if len(self.config["env"].keys()) > 0:
            for k, v in self.config["env"].items():
                if len(str(v)):
                    self.environment_str += f"-e {k}='\"{v}\"' "

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

        if self.config["provision_type"] == "connect":
            for f in self.connect_mandatory_fields:
                if f not in self.config.keys():
                    self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n",
                                     self.VALIDATION_ERROR_NUM)
                else:
                    if not self.config[f]:
                        self.throw_error(f"Wrong configuration. Miss mandatory field {f}\n",
                                         self.VALIDATION_ERROR_NUM)

    def run(self):
        super().run()
        self.validate()

        provision_str = 'container --stop-time 30'
        root_dir_var_str = ''

        log_txt_file_path = None
        report_file_path = None

        if self.config["provision_type"] == 'connect':
            if self.config["provision_guest"] != '' and self.config["ssh_key_id"] != '':
                provision_str = f'connect --guest {self.config["provision_guest"]} '
                provision_str += f'--key {self.runner.ssh_keys_dir}/{self.config["ssh_key_id"]}'
                if self.config["provision_guest_port"] != '':
                    provision_str += f' --port {self.config["provision_guest_port"]}'

        if self.root_dir != '':
            root_dir_var_str = f'export TMT_WORKDIR_ROOT={self.root_dir}'

        # skip prepare that can generate package manager error on some systems
        cmd = f'{root_dir_var_str} && cd {self.currentdir} &&' \
              f' tmt {self.context_str} run -vvv -a --id {self.runner.db_test_run.uid}' \
              f' {self.environment_str}' \
              f' provision --how {provision_str} plan --name {self.plan}'
        cmd = cmd.replace('  ', ' ')

        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        self.log += f'TEST RUN {self.runner.db_test_run.uid}\n'
        self.log += '======================================\n'
        self.log += f'STARTED AT {datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")}\n'
        self.log += '--------------------------------------\n'
        self.status_update()

        out, err = process.communicate()
        execution_return_code = process.returncode
        self.execution_result = self.runner.RESULT_FAIL

        if execution_return_code in [0, 1]:
            self.execution_result = self.runner.RESULT_PASS

        self.log += f'out: {out.decode("utf-8")}\n'
        self.log += '--------------------------------------\n'
        self.log += f'err: {err.decode("utf-8")}\n'
        self.log += '\n\n'
        self.log += '--------------------------------------\n'
        self.log += f'EXECUTION RESULT: {self.execution_result}\n'
        self.log += '======================================\n'
        self.status_update()

        # Test Result Evaluation
        if self.execution_result == self.runner.RESULT_PASS:
            log_txt_file_path = f'{self.root_dir}/{self.runner.db_test_run.uid}/log.txt'
            results_file_path = f'{self.root_dir}/{self.runner.db_test_run.uid}/api/{self.plan}/execute/results.yaml'
            report_file_path = f'{self.root_dir}/{self.runner.db_test_run.uid}/api/{self.plan}/report/html-report' \
                               f'/index.html'

            if not os.path.exists(results_file_path):
                self.test_result = self.runner.RESULT_FAIL
                self.artifacts.append(report_file_path)
            else:
                with open(results_file_path, 'r') as file:
                    result_yaml = yaml.safe_load(file)
                    if isinstance(result_yaml, list):
                        if 'result' in result_yaml[0].keys():
                            self.test_result = result_yaml[0]['result']
                        if 'log' in result_yaml[0].keys():
                            if isinstance(result_yaml[0]['log'], list):
                                log_file = result_yaml[0]['log'][0]
                                if os.path.exists(log_file):
                                    f = open(log_file, 'r')
                                    self.log += 'Log File Content\n'
                                    self.log += '--------------------------------------\n'
                                    self.log += f.read()
                                    self.log += '======================================\n'
                                    f.close()
        else:
            self.test_status = 'error'
            self.test_result = 'not executed'

        if report_file_path:
            if os.path.exists(report_file_path):
                self.test_report = report_file_path
                self.artifacts.append(report_file_path)

        if log_txt_file_path:
            if os.path.exists(log_txt_file_path):
                self.artifacts.append(log_txt_file_path)

        self.status_update()

    def collect_artifacts(self):
        for artifact in self.artifacts:
            try:
                shutil.copy(artifact, f"{self.root_dir}/{self.runner.db_test_run.uid}/api/{self.plan}/data/")
            except Exception as e:
                print(f"Unable to copy {artifact} to TMT_PLAN_DATA: {e}")

    def cleanup(self):
        cmd = "podman container prune -f"
        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
