"""Identifier generation.

All entity IDs are UUIDv7 (RFC 9562): a 48-bit Unix timestamp in milliseconds
followed by random bits. They sort by creation time, which keeps indexes compact,
and can be generated on any device without coordination.

Within one process, IDs are strictly increasing: if two are made in the same
millisecond (or the clock steps backwards), the random part is incremented
instead of redrawn (RFC 9562 section 6.2, method 2).
"""

import os
import threading
import time
from uuid import UUID

_TIMESTAMP_MASK = (1 << 48) - 1
_RANDOM_BITS = 74  # 128 - 48 timestamp - 4 version - 2 variant
_RANDOM_MASK = (1 << _RANDOM_BITS) - 1

_lock = threading.Lock()
_last_millis = -1
_last_random = 0


def uuid7() -> UUID:
    global _last_millis, _last_random
    with _lock:
        millis = time.time_ns() // 1_000_000
        if millis > _last_millis:
            random = int.from_bytes(os.urandom(10)) & _RANDOM_MASK
        else:
            millis = _last_millis
            random = _last_random + 1
            if random > _RANDOM_MASK:  # astronomically unlikely: borrow the next millisecond
                millis += 1
                random = int.from_bytes(os.urandom(10)) & _RANDOM_MASK
        _last_millis, _last_random = millis, random

    rand_a = random >> 62  # 12 bits
    rand_b = random & ((1 << 62) - 1)  # 62 bits
    value = (millis & _TIMESTAMP_MASK) << 80 | 0x7 << 76 | rand_a << 64 | 0x2 << 62 | rand_b
    return UUID(int=value)


def uuid7_timestamp_ms(value: UUID) -> int:
    """The creation time embedded in a UUIDv7, in Unix milliseconds."""
    return value.int >> 80
