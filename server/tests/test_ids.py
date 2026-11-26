import time

from todo_server.ids import uuid7, uuid7_timestamp_ms


def test_version_and_variant() -> None:
    value = uuid7()
    assert value.version == 7
    assert value.variant == "specified in RFC 4122"


def test_embeds_current_time() -> None:
    before = time.time_ns() // 1_000_000
    value = uuid7()
    after = time.time_ns() // 1_000_000
    assert before <= uuid7_timestamp_ms(value) <= after


def test_sorts_by_creation_time() -> None:
    first = uuid7()
    time.sleep(0.002)
    second = uuid7()
    assert first < second


def test_unique() -> None:
    assert len({uuid7() for _ in range(10_000)}) == 10_000


def test_strictly_increasing_within_a_millisecond() -> None:
    values = [uuid7() for _ in range(1_000)]
    assert values == sorted(values)
    assert all(v.version == 7 for v in values)
