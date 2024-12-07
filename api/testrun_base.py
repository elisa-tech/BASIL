#! /bin/python3
import datetime
import sys
import time


class TestRunnerBasePlugin():

    """
    Error numbers:
    7: validation issue
    8: execution issue
    9: monitor issue
    """
    VALIDATION_ERROR_NUM = 7
    EXECUTION_ERROR_NUM = 8
    MONITOR_ERROR_NUM = 9

    config = None
    currentdir = None
    execution_result = None
    log = ''
    runner = None
    test_result = None
    test_status = None
    test_report = None

    def __init__(self, runner=None, currentdir=None, *args, **kwargs):
        self.runner = runner
        self.config = runner.config
        self.currentdir = currentdir
        self.test_status = runner.STATUS_CREATED
        self.validate()

    def append_log(self, _log):
        self.log += f"\n\n----------> {self.timestamp()}"
        self.log += f"\n{_log.strip()}"
        self.log += "\n<------------"

    def cleanup(self):
        """
        Called by testrun
        """
        pass

    def collect_artifacts(self):
        """
        Called by testrun
        """
        pass

    def get_result(self):
        """
        Should be called inside each plugin by the run()
        """
        pass

    def delay_run(self, minutes=0):
        delay_log = f"Delayed request, it will start in {minutes} minutes"
        self.append_log(delay_log)
        self.status_update()
        time.sleep(minutes*60)

    def run(self):
        """
        Called by testrun
        """
        self.test_status = self.runner.STATUS_RUNNING
        self.status_update()

        # Delay must be specified in minutes
        if "delay" in self.config.keys():
            if str(self.config["delay"]).isnumeric() and not str(self.config["delay"]).startswith("0"):
                self.delay_run(int(self.config["delay"]))
        elif "delay" in self.config["env"].keys():
            if str(self.config["env"]["delay"]).isnumeric() and not str(self.config["env"]["delay"]).startswith("0"):
                self.delay_run(int(self.config["env"]["delay"]))

    def timestamp(self):
        TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
        return f"{datetime.datetime.utcnow().strftime(TIMESTAMP_FORMAT)} UTC"

    def status_update(self):
        """
        propagate log, report, result, status to the db instance inside the runner
        and update the database using the TestRunner publish method
        """
        self.runner.db_test_run.log = self.log
        self.runner.db_test_run.report = self.test_report
        self.runner.db_test_run.result = self.test_result
        self.runner.db_test_run.status = self.test_status
        self.runner.publish()

    def validate(self):
        """
        Called at init to verify the config
        """
        pass

    def throw_error(self, message: str, return_value: int):
        print(f"ERROR: {message}")
        self.append_log(f"ERROR: {message}\nRETURN VALUE: {return_value}")
        self.test_status = self.runner.STATUS_ERROR
        self.test_result = self.runner.STATUS_ERROR
        self.status_update()
        sys.exit(return_value)
