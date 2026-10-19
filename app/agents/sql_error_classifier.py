from enum import Enum

from sqlalchemy.exc import DBAPIError


class SQLErrorType(str, Enum):
    SYNTAX_ERROR = "syntax_error"
    UNDEFINED_COLUMN = "undefined_column"
    UNDEFINED_TABLE = "undefined_table"
    PERMISSION_DENIED = "permission_denied"
    QUERY_TIMEOUT = "query_timeout"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


RETRYABLE_SQL_ERRORS = {
    SQLErrorType.SYNTAX_ERROR,
    SQLErrorType.UNDEFINED_COLUMN,
    SQLErrorType.UNDEFINED_TABLE,
}


def classify_sql_error(
    error: Exception,
) -> SQLErrorType:
    if not isinstance(error, DBAPIError):
        return SQLErrorType.UNKNOWN

    original_error = error.orig
    sqlstate = getattr(original_error, "sqlstate", None)

    mapping = {
        "42601": SQLErrorType.SYNTAX_ERROR,
        "42703": SQLErrorType.UNDEFINED_COLUMN,
        "42P01": SQLErrorType.UNDEFINED_TABLE,
        "42501": SQLErrorType.PERMISSION_DENIED,
        "57014": SQLErrorType.QUERY_TIMEOUT,
    }

    if sqlstate in mapping:
        return mapping[sqlstate]

    if error.connection_invalidated:
        return SQLErrorType.CONNECTION_ERROR

    return SQLErrorType.UNKNOWN


def should_retry_sql(error_type: SQLErrorType) -> bool:
    return error_type in RETRYABLE_SQL_ERRORS