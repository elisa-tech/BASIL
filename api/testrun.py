#! /bin/python3
import argparse
import os
import sys

import yaml

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from sqlalchemy.orm.exc import NoResultFound
from testrun_github_actions import TestRunnerGithubActionsPlugin
from testrun_gitlab_ci import TestRunnerGitlabCIPlugin
from testrun_tmt import TestRunnerTmtPlugin

from db import db_orm
from db.models.api_test_case import ApiTestCaseModel
from db.models.notification import NotificationModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.test_run import TestRunModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel


class TestRunner:
    """
    TestRunner class is aimed to read the request from the database
    and to run the test using the desired plugin.
    The default plugin is `tmt` implemented at testrun_tmt.py
    this file provides a class named TestRunnerTmtPlugin that inherit from
    TestRunnerBasePlugin and is aimed to implement the run() method.
    The goal of the run() is to execute the test and provide information for the following
    variables:
    + log
    + test_report
    + test_result
    + test_status

    TestRunner - Error numbers
     - 1: Unable to find the Test Run in the db
     - 2: Test Run has been already triggered
     - 3: Unable to find the Model of the parent item in the mapping definition
     - 4: Unable to find the Mapping in the db
     - 5: The selected plugin is not supported yet
     - 6: Exceptions
    """
    RESULT_FAIL = 'fail'
    RESULT_PASS = 'pass'

    STATUS_CREATED = 'created'
    STATUS_ERROR = 'error'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'

    KERNEL_CI = 'KernelCI'
    GITLAB_CI = 'gitlab_ci'
    GITHUB_ACTIONS = 'github_actions'
    TMT = 'tmt'

    test_run_plugin_models = {GITHUB_ACTIONS: TestRunnerGithubActionsPlugin,
                              GITLAB_CI: TestRunnerGitlabCIPlugin,
                              KERNEL_CI: None,
                              TMT: TestRunnerTmtPlugin}

    runner_plugin = None
    config = {}

    id = None
    execution_result = ''
    execution_return_code = -1
    test_result = ''
    test_report = ''
    ssh_keys_dir = os.path.join(currentdir, 'ssh_keys')  # Same as SSH_KEYS_PATH defined in api.py
    presets_filepath = os.path.join(currentdir, 'testrun_plugin_presets.yaml')

    dbi = None
    db_test_run = None
    db_test_case = None
    mapping_to_model = None
    mapping = None
    DB_NAME = 'basil.db'

    def __del__(self):
        if self.dbi:
            self.dbi.engine.dispose()

    def __init__(self, id):
        self.id = id
        self.dbi = db_orm.DbInterface(self.DB_NAME)

        # Test Run
        try:
            self.db_test_run = self.dbi.session.query(TestRunModel).filter(
                TestRunModel.id == self.id
            ).one()
        except NoResultFound:
            print("ERROR: Unable to find the Test Run in the db")
            sys.exit(1)

        if self.db_test_run.status != self.STATUS_CREATED:
            print(f"ERROR: Test Run {id} has been already triggered, current status is `{self.db_test_run.status}`.")
            sys.exit(2)

        # Test Case
        if self.db_test_run.mapping_to == ApiTestCaseModel.__tablename__:
            self.mapping_model = ApiTestCaseModel
        elif self.db_test_run.mapping_to == SwRequirementTestCaseModel.__tablename__:
            self.mapping_model = SwRequirementTestCaseModel
        elif self.db_test_run.mapping_to == TestSpecificationTestCaseModel.__tablename__:
            self.mapping_model = TestSpecificationTestCaseModel
        else:
            # TODO: Update db with the error info
            print("Unable to find the Model of the parent item in the mapping definition")
            sys.exit(3)

        try:
            self.mapping = self.dbi.session.query(self.mapping_model).filter(
                self.mapping_model.id == self.db_test_run.mapping_id
            ).one()
        except BaseException:
            # TODO: Update db with the error info
            print("ERROR: Unable to find the Mapping in the db")
            sys.exit(4)

        db_config = self.db_test_run.test_run_config.as_dict()

        # Load preset configuration or explode the plugin_vars
        preset = self.db_test_run.test_run_config.plugin_preset
        if preset:
            # Init config with preset if required
            self.load_preset()
        else:
            plugin_vars = self.unpack_kv_str(db_config["plugin_vars"])
            for k, v in plugin_vars.items():
                db_config[k] = v
        del db_config["plugin_vars"]

        # Override preset values from test run configuration
        # but for lists, for the ones we append to the existing values
        db_config["env"] = self.unpack_kv_str(db_config["environment_vars"])

        del db_config["environment_vars"]

        db_config["context"] = self.unpack_kv_str(db_config["context_vars"])
        del db_config["context_vars"]

        for k, v in db_config.items():
            if isinstance(v, dict):
                if k in self.config.keys():
                    pass
                else:
                    self.config[k] = {}
                for kk, vv in v.items():
                    self.config[k][kk] = vv
            else:
                if v:
                    self.config[k] = v

        self.config["uid"] = self.db_test_run.uid
        self.config["env_str"] = ""
        self.config["context_str"] = ""

        env_str = f'basil_test_case_id={self.mapping.test_case.id};'
        env_str += f'basil_test_case_title={self.mapping.test_case.title};'
        env_str += f'basil_api_api={self.mapping.api.api};'
        env_str += f'basil_api_library={self.mapping.api.library};'
        env_str += f'basil_api_library_version={self.mapping.api.library_version};'
        env_str += f'basil_test_case_mapping_table={self.db_test_run.mapping_to};'
        env_str += f'basil_test_case_mapping_id={self.db_test_run.mapping_id};'
        env_str += f'basil_test_relative_path={self.mapping.test_case.relative_path};'
        env_str += f'basil_test_repo_path={self.mapping.test_case.repository};'
        env_str += f'basil_test_repo_url={self.mapping.test_case.repository};'
        env_str += f'basil_test_repo_ref={self.config["git_repo_ref"]};'
        env_str += f'basil_test_run_id={self.db_test_run.uid};'
        env_str += f'basil_test_run_title={self.db_test_run.title};'
        env_str += f'basil_test_run_config_id={self.config["id"]};'
        env_str += f'basil_test_run_config_title={self.config["title"]};'
        env_str += f'basil_user_email={self.db_test_run.created_by.email};'
        env_str += self.pack_str_kv(self.config['env'])

    def load_preset(self):
        plugin = self.db_test_run.test_run_config.plugin
        preset = self.db_test_run.test_run_config.plugin_preset

        if preset:
            presets_file = open(self.presets_filepath, "r")
            presets = yaml.safe_load(presets_file)
            presets_file.close()

            if plugin in presets.keys():
                tmp = [x for x in presets[plugin] if x["name"] == preset]
                if tmp:
                    # Init the config with the preset
                    # Values from test_run_config will override preset values
                    self.config = tmp[0]

    def unpack_kv_str(self, _string):
        # return a dict from a string formatted as
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

    def pack_str_kv(self, _dict):
        # return a string formatted as following
        # key1=value1;key2=value2...
        # from a flat key values dict
        ret = ""
        for k, v in _dict.items():
            ret += f"{k}={v};"
        if ret.endswith(";"):
            ret = ret[:-1]
        return ret

    def notify(self):
        # Notification
        if self.test_result == self.RESULT_PASS:
            variant = 'success'
        else:
            variant = 'danger'

        notification = f'Test Run for Test Case ' \
                       f'{self.mapping.test_case.title} as part of the sw component ' \
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
        """
        Update the database with the current version of the TestRunModel instance
        """
        self.dbi.session.add(self.db_test_run)
        self.dbi.session.commit()

    def run(self):
        # Test Run Plugin
        try:
            if self.db_test_run.test_run_config.plugin in self.test_run_plugin_models:
                self.runner_plugin = self.test_run_plugin_models[
                    self.db_test_run.test_run_config.plugin](runner=self,
                                                             currentdir=currentdir)
                self.runner_plugin.validate()
                self.runner_plugin.run()
                self.runner_plugin.cleanup()
                self.publish()
            else:
                reason = "\nERROR: The selected plugin is not supported yet"
                print(reason)
                self.db_test_run.status = "error"
                self.db_test_run.log += reason
                self.publish()
                sys.exit(5)
        except Exception as e:
            self.db_test_run.status = "error"
            self.db_test_run.log += f"\n{e}"
            self.publish()
            sys.exit(6)


if __name__ == '__main__':
    """
    This file is called by the api.py via a terminal and
    require as argument an id of the TestRun table
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", type=str, help="TODO")
    args = parser.parse_args()

    tr = TestRunner(id=args.id)
    tr.run()
    tr.notify()
