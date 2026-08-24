import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import DataError

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from testrun import TestRunner, sanitize_db_text
from db.models.api import ApiModel
from db.models.test_run import TestRunModel
from db.models.test_run_config import TestRunConfigModel
from db.models.user import UserModel
from conftest import UT_USER_EMAIL

_CONMON_LOG = (
    "err: container create failed (no logs from conmon): conmon bytes \"\": "
    "readObjectStart: expect { or n, but found \x00"
)


def _make_api(client_db, utilities, user):
    raw_spec = tempfile.NamedTemporaryFile(mode="w", delete=False)
    raw_spec.write("BASIL UT: spec for testrun publish sanitization.")
    raw_spec.close()
    api = ApiModel(
        f"ut_testrun_publish_{utilities.generate_random_hex_string8()}",
        "ut_lib",
        "v1",
        raw_spec.name,
        "ut_cat",
        utilities.generate_random_hex_string8(),
        raw_spec.name + "impl",
        0,
        42,
        "ut_tags",
        user,
    )
    client_db.session.add(api)
    client_db.session.commit()
    return api, raw_spec.name


def _make_test_run(client_db, utilities, user, api):
    config = TestRunConfigModel(
        "tmt",
        "",
        "",
        f"UT Config #{utilities.generate_random_hex_string8()}",
        "main",
        "",
        "",
        "container",
        "",
        "1234",
        None,
        user,
    )
    client_db.session.add(config)
    client_db.session.flush()
    test_run = TestRunModel(
        api,
        f"UT Run #{utilities.generate_random_hex_string8()}",
        "notes",
        config,
        "api_test_case",
        1,
        user,
    )
    client_db.session.add(test_run)
    client_db.session.commit()
    return test_run


def test_sanitize_db_text_strips_nul():
    cleaned = sanitize_db_text(_CONMON_LOG)
    assert "\x00" not in cleaned
    assert "container create failed" in cleaned
    assert "found " in cleaned


def test_sanitize_db_text_none_and_clean_passthrough():
    assert sanitize_db_text(None) is None
    assert sanitize_db_text("no nul here") == "no nul here"
    assert sanitize_db_text(12) == 12


def test_sanitize_db_text_bytes_with_nul():
    cleaned = sanitize_db_text(b"out: ok\x00err: fail")
    assert cleaned == "out: okerr: fail"


def test_publish_strips_nul_before_commit():
    runner = object.__new__(TestRunner)
    runner.dbi = MagicMock()
    runner.db_test_run = MagicMock()
    runner.db_test_run.log = _CONMON_LOG
    runner.db_test_run.report = "report\x00.html"

    runner.publish()

    assert "\x00" not in runner.db_test_run.log
    assert runner.db_test_run.report == "report.html"
    runner.dbi.session.add.assert_called_once_with(runner.db_test_run)
    runner.dbi.session.commit.assert_called_once()


def test_raw_commit_of_nul_log_is_rejected(client_db, ut_user_db, utilities):
    """Document the PostgreSQL limitation that publish() must work around."""
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    api, spec_path = _make_api(client_db, utilities, user)
    try:
        test_run = _make_test_run(client_db, utilities, user, api)
        test_run.log = _CONMON_LOG
        client_db.session.add(test_run)
        try:
            with pytest.raises((ValueError, DataError)):
                client_db.session.commit()
        finally:
            client_db.session.rollback()
    finally:
        if os.path.isfile(spec_path):
            os.remove(spec_path)


def test_publish_persists_status_when_log_contains_nul(client_db, ut_user_db, utilities):
    user = client_db.session.query(UserModel).filter(UserModel.email == UT_USER_EMAIL).one()
    api, spec_path = _make_api(client_db, utilities, user)
    try:
        test_run = _make_test_run(client_db, utilities, user, api)
        runner = object.__new__(TestRunner)
        runner.dbi = client_db
        runner.db_test_run = test_run
        test_run.status = "error"
        test_run.result = "not executed"
        test_run.log = _CONMON_LOG
        test_run.report = "report\x00.html"

        runner.publish()

        persisted = (
            client_db.session.query(TestRunModel).filter(TestRunModel.id == test_run.id).one()
        )
        assert persisted.status == "error"
        assert persisted.result == "not executed"
        assert "\x00" not in (persisted.log or "")
        assert "container create failed" in persisted.log
        assert persisted.report == "report.html"
    finally:
        if os.path.isfile(spec_path):
            os.remove(spec_path)
