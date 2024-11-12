#! /bin/python3
import datetime
import os
import subprocess
import yaml
from testrun_base import TestRunnerBasePlugin


class TestRunnerTmtPlugin(TestRunnerBasePlugin):

    # Constants
    plan = 'tmt-plan'
    root_dir = os.getenv('BASIL_TMT_WORKDIR_ROOT', '/var/tmp/tmt')  # Same as TMT_LOGS_PATH defined in api.py

    def __init__(self, runner=None, *args, **kwargs):
        super().__init__(runner=runner, *args, **kwargs)

        if not os.path.exists(self.root_dir):
            os.mkdir(self.root_dir)

        if len(self.config["context"].keys()) > 0:
            for k, v in self.config["context"].items():
                if len(v):
                    self.config["context_str"] += f"-c {k}='\"{v}\"' "

        if len(self.config["env"].keys()) > 0:
            for k, v in self.config["env"].items():
                if len(v):
                    self.config["env_str"] += f"-e {k}='\"{v}\"' "

    def validate(self):
        # Check that all the required config are set
        pass

    def run(self):
        super().run()
        self.validate()

        provision_str = 'container --stop-time 30'
        root_dir_var_str = ''

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
              f' tmt {self.config["context_str"]} run -vvv -a --id {self.runner.db_test_run.uid}' \
              f' {self.config["env_str"]}' \
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
            results_file_path = f'{self.root_dir}/{self.runner.db_test_run.uid}/api/{self.plan}/execute/results.yaml'
            report_file_path = f'{self.root_dir}/{self.runner.db_test_run.uid}/api/{self.plan}/report/html-report' \
                               f'/index.html'

            if not os.path.exists(results_file_path):
                self.test_result = self.runner.RESULT_FAIL
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

            if os.path.exists(report_file_path):
                self.test_report = report_file_path
        else:
            self.test_result = 'not executed'

        self.status_update()

    def cleanup(self):
        cmd = "podman container prune -f"
        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
