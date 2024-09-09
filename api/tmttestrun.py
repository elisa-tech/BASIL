#! /bin/python3
import argparse
import os
import subprocess
import sys
import yaml

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from db.models.test_specification_test_case import TestSpecificationTestCaseModel
from db.models.test_run import TestRunModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.notification import NotificationModel
from db.models.api_test_case import ApiTestCaseModel
from db import db_orm
from sqlalchemy.orm.exc import NoResultFound


class TmtTestRunner():

    RESULT_FAIL = 'fail'
    RESULT_PASS = 'pass'

    context = {}
    env = {}
    id = None
    plan = 'tmt-plan'
    execution_result = ''
    execution_return_code = -1
    test_result = ''
    test_report = ''
    root_dir = os.getenv('BASIL_TMT_WORKDIR_ROOT', '/var/tmp/tmt')  # Same as TMT_LOGS_PATH defined in api.py
    ssh_keys_dir = os.path.join(currentdir, 'ssh_keys')  # Same as SSH_KEYS_PATH defined in api.py
    dbi = None
    db_test_run = None
    db_test_case = None
    DB_NAME = 'basil.db'

    def __del__(self):
        if self.dbi:
            self.dbi.engine.dispose()

    def __init__(self, id):
        self.id = id
        self.dbi = db_orm.DbInterface(self.DB_NAME)

        if not os.path.exists(self.root_dir):
            os.mkdir(self.root_dir)

        # Test Run
        try:
            self.db_test_run = self.dbi.session.query(TestRunModel).filter(
                TestRunModel.id == self.id
            ).one()
        except NoResultFound:
            print("No Test Run")
            sys.exit(1)

        # Test Case
        mapping_model = None
        if self.db_test_run.mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif self.db_test_run.mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif self.db_test_run.mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            # Update db with the error info
            sys.exit(2)

        try:
            mapping = self.dbi.session.query(mapping_model).filter(
                mapping_model.id == self.db_test_run.mapping_id
            ).one()
        except BaseException:
            # Update db with the error info
            sys.exit(3)

        env_str = f'basil_test_case_id={mapping.test_case.id};'
        env_str += f'basil_test_case_title={mapping.test_case.title};'
        env_str += f'basil_api_api={mapping.api.api};'
        env_str += f'basil_api_library={mapping.api.library};'
        env_str += f'basil_api_library_version={mapping.api.library_version};'
        env_str += f'basil_test_case_mapping_table={self.db_test_run.mapping_to};'
        env_str += f'basil_test_case_mapping_id={self.db_test_run.mapping_id};'
        env_str += f'basil_test_relative_path={mapping.test_case.relative_path};'
        env_str += f'basil_test_repo_path={mapping.test_case.repository};'
        env_str += f'basil_test_repo_url={mapping.test_case.repository};'
        env_str += f'basil_test_repo_ref={self.db_test_run.test_run_config.git_repo_ref};'
        env_str += f'basil_test_run_id={self.db_test_run.uid};'
        env_str += f'basil_test_run_title={self.db_test_run.title};'
        env_str += f'basil_test_run_config_id={self.db_test_run.test_run_config.id};'
        env_str += f'basil_test_run_config_title={self.db_test_run.test_run_config.title};'
        env_str += f'basil_user_email={self.db_test_run.created_by.email};'
        env_str += self.db_test_run.test_run_config.environment_vars
        self.env = self.unpack_kv_str(env_str)
        self.context = self.unpack_kv_str(self.db_test_run.test_run_config.context_vars)

    def unpack_kv_str(self, _string):
        # return a dict froma string formatted as
        # key1=value1;key2=value2...
        PAIRS_DIV = ';'
        KV_DIV = '='
        ret = {}
        pairs = _string.split(PAIRS_DIV)
        for pair in pairs:
            if KV_DIV in pair:
                if pair.count(KV_DIV) == 1:
                    ret[pair.split(KV_DIV)[0].strip()] = pair.split(KV_DIV)[1].strip()
        return ret

    def notify(self):
        # Notification
        if self.db_test_run.mapping_to == ApiTestCaseModel.__tablename__:
            mapping_model = ApiTestCaseModel
        elif self.db_test_run.mapping_to == SwRequirementTestCaseModel.__tablename__:
            mapping_model = SwRequirementTestCaseModel
        elif self.db_test_run.mapping_to == TestSpecificationTestCaseModel.__tablename__:
            mapping_model = TestSpecificationTestCaseModel
        else:
            return False

        try:
            mapping = self.dbi.session.query(mapping_model).filter(
                mapping_model.id == self.db_test_run.mapping_id
            ).one()
        except BaseException:
            return False

        if self.test_result == 'pass':
            variant = 'success'
        else:
            variant = 'danger'

        notification = f'Test Run for Test Case ' \
                       f'{mapping.test_case.title} as part of the sw component ' \
                       f'{self.db_test_run.api.api}, library {self.db_test_run.api.library} ' \
                       f'completed with: {self.test_result.upper()}'
        notifications = NotificationModel(self.db_test_run.api,
                                          variant,
                                          f'Test Run for {self.db_test_run.api.api} {self.test_result.upper()}',
                                          notification,
                                          '',
                                          f'/mapping/{self.db_test_run.api.id}')
        self.dbi.session.add(notifications)
        self.dbi.session.commit()

    def publish(self):
        if self.execution_result == self.RESULT_PASS:
            results_file_path = f'{self.root_dir}/{self.db_test_run.uid}/api/{self.plan}/execute/results.yaml'
            report_file_path = f'{self.root_dir}/{self.db_test_run.uid}/api/{self.plan}/report/html-report/index.html'

            if not os.path.exists(results_file_path):
                self.execution_result = self.RESULT_FAIL
                self.test_result = self.RESULT_FAIL
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
                                    self.log = f.read()
                                    f.close()

            if os.path.exists(report_file_path):
                self.test_report = report_file_path

        else:
            self.test_result = 'not executed'

        # Update db
        try:
            db_test_run = self.dbi.session.query(TestRunModel).filter(
                TestRunModel.id == self.id
            ).one()
        except NoResultFound:
            print("No Test Run")
            sys.exit(1)

        db_test_run.status = 'done'
        db_test_run.result = self.test_result
        db_test_run.log = self.log
        self.dbi.session.add(db_test_run)
        self.dbi.session.commit()

    def run(self):
        context_options_str = ''
        env_options_str = ''
        provision_str = 'container --stop-time 30'
        root_dir_var_str = ''

        if len(self.context.keys()) > 0:
            for k, v in self.context.items():
                if len(v):
                    context_options_str += f"-c {k}='\"{v}\"' "

        if len(self.env.keys()) > 0:
            for k, v in self.env.items():
                if len(v):
                    env_options_str += f"-e {k}='\"{v}\"' "

        if self.db_test_run.test_run_config.provision_type == 'connect':
            if self.db_test_run.test_run_config.provision_guest != '' and \
                    self.db_test_run.test_run_config.ssh_key_id != '':
                provision_str = f'connect --guest {self.db_test_run.test_run_config.provision_guest} '
                provision_str += f'--key {self.ssh_keys_dir}/{self.db_test_run.test_run_config.ssh_key_id}'
                if self.db_test_run.test_run_config.provision_guest_port != '':
                    provision_str += f' --port {self.db_test_run.test_run_config.provision_guest_port}'

        if self.root_dir != '':
            root_dir_var_str = f'export TMT_WORKDIR_ROOT={self.root_dir}'

        # skip prepare that can generate package manager error on some systems
        cmd = f'{root_dir_var_str} && cd {currentdir} && ' \
              f'tmt {context_options_str} run -vvv -a --id {self.db_test_run.uid} {env_options_str} ' \
              f'provision --how {provision_str} plan --name {self.plan}'
        cmd = cmd.replace('  ', ' ')

        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        out, err = process.communicate()
        self.execution_return_code = process.returncode
        if self.execution_return_code in [0, 1]:
            self.execution_result = self.RESULT_PASS
        else:
            self.execution_result = self.RESULT_FAIL

        self.log = f'out: {out.decode("utf-8")}'
        self.log += '\n--------------------------'
        self.log += f'\nerr: {err.decode("utf-8")}'

        self.publish()
        self.notify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", type=str, help="TODO")
    args = parser.parse_args()

    tr = TmtTestRunner(id=args.id)
    tr.run()
