#! /bin/python3
import datetime


class TestRunnerBasePlugin():

    """
    Error numbers:
    7: validation issue
    8: execution issue
    9: monitor issue
    """
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

    def append_log(self, _log):
        self.log += f"\n\n----------> {self.timestamp()}"
        self.log += f"\n{_log.strip()}"
        self.log += "\n<------------"

    def cleanup(self):
        pass

    def get_result(self):
        pass

    def run(self):
        self.test_status = self.runner.STATUS_RUNNING
        self.status_update()

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
        pass
