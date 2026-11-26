"""Errors raised by the db package, so callers never need to import SQLAlchemy."""


class DatabaseError(Exception):
    """Base class for db package errors."""


class NotFoundError(DatabaseError):
    """The requested record does not exist (or has been deleted)."""


class ConstraintViolation(DatabaseError):
    """A write broke a database constraint, e.g. a reference to a missing record."""
