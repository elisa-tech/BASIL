import json
from functools import wraps

OK_STATUS = 200
OK_RESPONSE_TYPE = "OK"

CREATED_STATUS = 201
CREATED_RESPONSE_TYPE = "CREATED"

BAD_REQUEST_RESPONSE_TYPE = "BAD_REQUEST"
BAD_REQUEST_MESSAGE = "Bad request"
BAD_REQUEST_MESSAGE_MISSING_FIELDS = "Missing mandatory field in the request"
BAD_REQUEST_STATUS = 400

UNAUTHORIZED_MESSAGE = "User not authorized"
UNAUTHORIZED_RESPONSE_TYPE = "UNAUTHORIZED"
UNAUTHORIZED_STATUS = 401

FORBIDDEN_MESSAGE = "Forbidden"
FORBIDDEN_MESSAGE_WRITE = "Current user have no write permissions"
FORBIDDEN_MESSAGE_READ = "Current user have no read permissions"
FORBIDDEN_MESSAGE_MANAGE = "Current user have no manage permissions"
FORBIDDEN_MESSAGE_EDIT = "Current user have no edit permissions"
FORBIDDEN_STATUS = 403
FORBIDDEN_RESPONSE_TYPE = "FORBIDDEN"

NOT_FOUND_MESSAGE = "Not found"
NOT_FOUND_MESSAGE_SW_COMPONENT = "Sw Component not found."
NOT_FOUND_MESSAGE_API = "Api not found."
NOT_FOUND_MESSAGE_USER = "User not found."
NOT_FOUND_MESSAGE_NOTIFICATION = "Notification not found."
NOT_FOUND_MESSAGE_SETTING = "Setting not found."
NOT_FOUND_MESSAGE_TEST_RUN = "Test run not found."
NOT_FOUND_MESSAGE_TEST_RUN_CONFIG = "Test run config not found."
NOT_FOUND_MESSAGE_COMMENT = "Comment not found."
NOT_FOUND_MESSAGE_FILE = "File not found."
NOT_FOUND_RESPONSE_TYPE = "NOT_FOUND"
NOT_FOUND_STATUS = 404

CONFLICT_MESSAGE = "Conflict with existing data"
CONFLICT_RESPONSE_TYPE = "CONFLICT"
CONFLICT_STATUS = 409

PRECONDITION_FAILED_MESSAGE = "Some precondition failed"
PRECONDITION_FAILED_RESPONSE_TYPE = "PRECONDITION_FAILED"
PRECONDITION_FAILED_STATUS = 412

SERVER_ERROR_MESSAGE = "Unexpected Server Error"
SERVER_ERROR_RESPONSE_TYPE = "SERVER_ERROR"
SERVER_ERROR_STATUS = 500


class ApiResponse():
    def __init__(self):
        self._route = None
        self._verb = None
        self._response_type = None
        self._args = None
        self._missing_fields = None
        self._message = None
        self._status = None
        self._exception = None
        self._logger = None
        self._data = None

    def set_data(self, data):
        self._data = data

    def set_route(self, route):
        self._route = route

    def set_verb(self, verb):
        self._verb = verb

    def set_response_type(self, response_type):
        self._response_type = response_type

    def set_args(self, args):
        self._args = args

    def set_missing_fields(self, missing_fields):
        self._missing_fields = missing_fields

    def set_message(self, message):
        self._message = message

    def set_status(self, status):
        self._status = status

    def set_exception(self, exception):
        self._exception = exception

    def set_logger(self, logger):
        self._logger = logger

    def log_message(self):
        log_message = f"{self._response_type} at {self._route} with {self._verb} method"
        log_message += f"\n * Message: {self._message}"
        if self._args:
            log_message += f"\n * Args: {json.dumps(self._args, indent=4)}"
        if self._exception:
            log_message += f"\n * Exception: {self._exception}"
        if self._logger:
            self._logger.error(log_message)
        else:
            print(log_message)

    def return_not_found(self):
        self.log_message()
        self.set_status(NOT_FOUND_STATUS)
        self.set_response_type(NOT_FOUND_RESPONSE_TYPE)
        if not self._message:
            self.set_message(NOT_FOUND_MESSAGE)
        return self._message, self._status

    def return_not_found_sw_component(self):
        self.set_message(NOT_FOUND_MESSAGE_SW_COMPONENT)
        return self.return_not_found()

    def return_not_found_api(self):
        self.set_message(NOT_FOUND_MESSAGE_API)
        return self.return_not_found()

    def return_not_found_user(self):
        self.set_message(NOT_FOUND_MESSAGE_USER)
        return self.return_not_found()

    def return_not_found_comment(self):
        self.set_message(NOT_FOUND_MESSAGE_COMMENT)
        return self.return_not_found()

    def return_not_found_file(self):
        self.set_message(NOT_FOUND_MESSAGE_FILE)
        return self.return_not_found()

    def return_bad_request(self):
        self.log_message()
        self.set_status(BAD_REQUEST_STATUS)
        self.set_response_type(BAD_REQUEST_RESPONSE_TYPE)
        if not self._message:
            self.set_message(BAD_REQUEST_MESSAGE)
        return self._message, self._status

    def return_bad_request_missing_fields(self):
        self.set_message(BAD_REQUEST_MESSAGE_MISSING_FIELDS)
        return self.return_bad_request()

    def return_conflict(self):
        self.log_message()
        self.set_status(CONFLICT_STATUS)
        self.set_response_type(CONFLICT_RESPONSE_TYPE)
        if not self._message:
            self.set_message(CONFLICT_MESSAGE)
        return self._message, self._status

    def return_precondition_failed(self):
        self.log_message()
        self.set_status(PRECONDITION_FAILED_STATUS)
        self.set_response_type(PRECONDITION_FAILED_RESPONSE_TYPE)
        if not self._message:
            self.set_message(PRECONDITION_FAILED_MESSAGE)
        return self._message, self._status

    def return_server_error(self):
        self.log_message()
        self.set_status(SERVER_ERROR_STATUS)
        self.set_response_type(SERVER_ERROR_RESPONSE_TYPE)
        if not self._message:
            self.set_message(SERVER_ERROR_MESSAGE)
        return self._message, self._status

    def return_unauthorized(self):
        self.log_message()
        self.set_status(UNAUTHORIZED_STATUS)
        self.set_response_type(UNAUTHORIZED_RESPONSE_TYPE)
        if not self._message:
            self.set_message(UNAUTHORIZED_MESSAGE)
        return self._message, self._status

    def return_forbidden(self):
        self.log_message()
        self.set_status(FORBIDDEN_STATUS)
        self.set_response_type(FORBIDDEN_RESPONSE_TYPE)
        if not self._message:
            self.set_message(FORBIDDEN_MESSAGE)
        return self._message, self._status

    def return_forbidden_write(self):
        self.set_message(FORBIDDEN_MESSAGE_WRITE)
        return self.return_forbidden()

    def return_forbidden_read(self):
        self.set_message(FORBIDDEN_MESSAGE_READ)
        return self.return_forbidden()

    def return_forbidden_manage(self):
        self.set_message(FORBIDDEN_MESSAGE_MANAGE)
        return self.return_forbidden()

    def return_forbidden_edit(self):
        self.set_message(FORBIDDEN_MESSAGE_EDIT)
        return self.return_forbidden()

    def return_created(self):
        self.set_status(CREATED_STATUS)
        self.set_response_type(CREATED_RESPONSE_TYPE)
        return self._data, self._status

    def return_ok(self):
        self.set_status(OK_STATUS)
        return self._data, self._status


def api_response_decorator(func):
    """Expects a Flask-RESTful Resource instance method; reads ``route`` from the
    instance or class, and the verb from the method name (``get``, ``post``, …).
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        api_response = ApiResponse()
        resource_self = args[0] if args else None
        if resource_self is not None:
            route = getattr(resource_self, "route", None) or getattr(
                type(resource_self), "route", None
            )
        else:
            route = None
        api_response.set_route(route)
        api_response.set_verb(func.__name__)
        # inject api_response into the function
        kwargs["api_response"] = api_response
        return func(*args, **kwargs)

    return wrapper
