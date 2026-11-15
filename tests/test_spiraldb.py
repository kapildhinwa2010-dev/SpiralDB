"""Tests for SpiralDB: content addressing, parity detection, honest repair."""

import pytest

from spiraldb import HelixMemory


def test_write_read_roundtrip():
    memory = HelixMemory(size=8, record_size=4)
    memory.write("alpha", b"\x01\x02\x03\x04")
    assert memory.read("alpha") == b"\x01\x02\x03\x04"


def test_deterministic_addressing():
    memory = HelixMemory(size=8, record_size=4)
    assert memory.address("alpha") == memory.address("alpha")


def test_record_flip_detected_not_repairable():
    memory = HelixMemory(size=8, record_size=4)
    memory.write("alpha", b"\x01\x02\x03\x04")
    memory.corrupt("alpha")
    assert memory.verify() is False
    memory.repair()
    assert memory.verify() is True
    with pytest.raises(ValueError):
        memory.read_checked("alpha")


def test_parity_flip_detected_and_repaired():
    memory = HelixMemory(size=8, record_size=4)
    memory.write("alpha", b"\x01\x02\x03\x04")
    memory.corrupt_parity("alpha")
    assert memory.verify() is False
    assert memory.repair() == 1
    assert memory.read_checked("alpha") == b"\x01\x02\x03\x04"


def test_keys_keep_their_row():
    memory = HelixMemory(size=8, record_size=4)
    memory.write("alpha", b"\x01\x02\x03\x04")
    row = memory._slots["alpha"]
    memory.write("alpha", b"\x05\x06\x07\x08")
    assert memory._slots["alpha"] == row
    assert memory.read("alpha") == b"\x05\x06\x07\x08"


def test_unknown_key_raises():
    memory = HelixMemory(size=8, record_size=4)
    with pytest.raises(KeyError):
        memory.read("nope")
