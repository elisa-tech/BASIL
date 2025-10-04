#! /bin/python3
import argparse
import logging
import os
import sys
import traceback

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from pyaml_env import parse_config
from sqlalchemy.orm.exc import NoResultFound
from testrun_github_actions import TestRunnerGithubActionsPlugin
from testrun_gitlab_ci import TestRunnerGitlabCIPlugin
from testrun_lava import TestRunnerLAVAPlugin
from testrun_testing_farm import TestRunnerTestingFarmPlugin
from testrun_tmt import TestRunnerTmtPlugin

from db import db_orm
from db.models.api_test_case import ApiTestCaseModel
from db.models.notification import NotificationModel
from db.models.sw_requirement_test_case import SwRequirementTestCaseModel
from db.models.test_run import TestRunModel
from db.models.test_specification_test_case import TestSpecificationTestCaseModel

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("Starting BASIL Test Run")


class TestRunner:
    """
    TestRunner class is aimed to read the request from the database
    and to run the test using the desired plugin.
    The default plugin is `tmt` implemented at testrun_tmt.py
    this file provides a class named TestRunnerTmtPlugin that inherit from
    TestRunnerBasePlugin and is aimed to implement the run() method.

    TestRunner - Error numbers
     - 1: Unable to find the Test Run in the db
     - 2: Test Run has been already triggered
     - 3: Unable to find the Model of the parent item in the mapping definition
     - 4: Unable to find the Mapping in the db
     - 5: The selected plugin is not supported yet
     - 6: Exceptions
    """

    RESULT_FAIL = "fail"
    RESULT_PASS = "pass"

    STATUS_CREATED = "created"
    STATUS_ERROR = "error"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"

    KERNEL_CI = "KernelCI"
    GITLAB_CI = "gitlab_ci"
    GITHUB_ACTIONS = "github_actions"
    LAVA = "LAVA"
    TMT = "tmt"
    TESTING_FARM = "testing_farm"

    CONFIGS_FOLDER = "configs"

    test_run_plugin_models = {
        "KernelCI": None,
        "LAVA": TestRunnerLAVAPlugin,
        "github_actions": TestRunnerGithubActionsPlugin,
        "gitlab_ci": TestRunnerGitlabCIPlugin,
        "testing_farm": TestRunnerTestingFarmPlugin,
        "tmt": TestRunnerTmtPlugin,
    }

    runner_plugin = None
    config = {}

    id = None
    ssh_keys_dir = os.path.join(
        currentdir, "ssh_keys"
    )  # Same as SSH_KEYS_PATH defined in api.py
    presets_filepath = os.path.join(
        currentdir, CONFIGS_FOLDER, "testrun_plugin_presets.yaml"
    )

    dbi = None
    db_test_run = None
    db_test_case = None
    mapping_to_model = None
    mapping = None
    DB_NAME = "basil"

    def __init__(self, id, unit_test=False):
        self.id = id
        # Use 'test' database during unit testing, otherwise use default 'basil'
        db_name = "test" if unit_test else self.DB_NAME

        logger.info(f"TestRunner initializing with database: {db_name}")
        if unit_test:
            logger.info("Unit test mode enabled - using 'test' database")

        self.dbi = db_orm.DbInterface(db_name=db_name)

        # Test Run
        try:
            self.db_test_run = (
                self.dbi.session.query(TestRunModel)
                .filter(TestRunModel.id == self.id)
                .one()
            )
        except NoResultFound:
            logging.error(f"Unable to find the Test Run `{self.id}` in the db")
            sys.exit(1)

        logging.info(f"Test Run {id} data collected from the db")

        if not self.db_test_run.log:
            self.db_test_run.log = ""

        if self.db_test_run.status != self.STATUS_CREATED:
            logging.error(
                f"Test Run {id} has been already triggered, current status is `{self.db_test_run.status}`."
            )
            sys.exit(2)

        logging.info(f"Test Run {id} status: CREATED")

        # Test Case
        if self.db_test_run.mapping_to == ApiTestCaseModel.__tablename__:
            self.mapping_model = ApiTestCaseModel
        elif self.db_test_run.mapping_to == SwRequirementTestCaseModel.__tablename__:
            self.mapping_model = SwRequirementTestCaseModel
        elif (
            self.db_test_run.mapping_to == TestSpecificationTestCaseModel.__tablename__
        ):
            self.mapping_model = TestSpecificationTestCaseModel
        else:
            # TODO: Update db with the error info
            logging.error(
                "Unable to find the Model of the parent item in the mapping definition"
            )
            sys.exit(3)

        try:
            self.mapping = (
                self.dbi.session.query(self.mapping_model)
                .filter(self.mapping_model.id == self.db_test_run.mapping_id)
                .one()
            )
        except BaseException:
            # TODO: Update db with the error info
            logging.error("Unable to find the Mapping in the db")
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

        # Override preset values from test run configuration
        # but for lists, for the ones we append to the existing values
        db_config["env"] = self.unpack_kv_str(db_config["environment_vars"])
        db_config["context"] = self.unpack_kv_str(db_config["context_vars"])

        del db_config["plugin_vars"]
        del db_config["environment_vars"]
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

    def load_preset(self):
        plugin = self.db_test_run.test_run_config.plugin
        preset = self.db_test_run.test_run_config.plugin_preset

        if preset:
            presets = parse_config(self.presets_filepath)

            if plugin in presets.keys():
                tmp = [x for x in presets[plugin] if x["name"] == preset]
                if tmp:
                    # Init the config with the preset
                    # Values from test_run_config will override preset values
                    self.config = tmp[0]

    def unpack_kv_str(self, _string):
        # return a dict from a string formatted as
        # key1=value1;key2=value2...
        PAIRS_DIV = ";"
        KV_DIV = "="
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
        if not self.db_test_run:
            return

        if self.db_test_run.result == self.RESULT_PASS:
            variant = "success"
        else:
            variant = "danger"

        notification = (
            f"Test Run for Test Case "
            f"`{self.mapping.test_case.title}` as part of the sw component "
            f"`{self.db_test_run.api.api}`, library `{self.db_test_run.api.library}` "
            f"completed with: {self.db_test_run.result.upper()}"
        )
        notifications = NotificationModel(
            self.db_test_run.api,
            variant,
            f"Test Run for `{self.db_test_run.api.api}` "
            f"{self.db_test_run.result.upper()}",
            notification,
            "",
            f"/mapping/{self.db_test_run.api.id}",
        )
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
        logging.info(f"Test run {self.id} start execution")
        try:
            if (
                self.db_test_run.test_run_config.plugin
                in self.test_run_plugin_models.keys()
            ):
                self.runner_plugin = self.test_run_plugin_models[
                    self.db_test_run.test_run_config.plugin
                ](runner=self, currentdir=currentdir)
                self.runner_plugin.run()
                self.runner_plugin.collect_artifacts()
                self.runner_plugin.cleanup()
                self.publish()
            else:
                reason = "\nERROR: The selected plugin is not supported yet"
                logging.error(reason)
                self.db_test_run.status = "error"
                self.db_test_run.log += reason
                self.publish()
                sys.exit(5)
        except Exception:
            logger.error(f"Exception: {traceback.format_exc()}")
            self.db_test_run.status = "error"
            self.db_test_run.log += f"\nException: {traceback.format_exc()}"
            self.publish()
            logging.error(self.db_test_run.log)
            sys.exit(6)

    def close(self):
        self.dbi.close()


if __name__ == "__main__":
    """
    This file is called by the api.py via a terminal and
    require as argument an id of the TestRun table
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", type=str, help="Test Run ID from the TestRun table")
    parser.add_argument(
        "--unit-test",
        action="store_true",
        help="Use 'test' database instead of 'basil' database (for unit testing)",
    )
    args = parser.parse_args()

    tr = TestRunner(id=args.id, unit_test=args.unit_test)
    tr.run()
    tr.notify()
    tr.close()
