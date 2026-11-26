"""Enumerations shared by every layer. Values are the stored and wire format."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class Behaviour(StrEnum):
    """What happens when a task is completed."""

    ONCE = "once"
    RECURRING = "recurring"
    HABIT = "habit"
    SOMEDAY = "someday"


class TaskStatus(StrEnum):
    ACTIVE = "active"
    WAITING = "waiting"
    DONE = "done"
    ARCHIVED = "archived"


class TriggerKind(StrEnum):
    """What makes a task due."""

    AT = "at"
    AFTER_COMPLETION = "after_completion"
    SCHEDULE = "schedule"
    EVENT = "event"


class CompletionKind(StrEnum):
    DONE = "done"
    SKIPPED = "skipped"
    MISSED = "missed"
    PROGRESS = "progress"


class CompletionSource(StrEnum):
    APP = "app"
    WEB = "web"
    MCP = "mcp"
    HA = "ha"
    API = "api"
    SYSTEM = "system"
