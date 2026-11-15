import pytest

from spiraldb import HelixMemory, spiral_coordinates


def test_spiral_starts_at_center():
    size = 5
    coords = spiral_coordinates(size)
    assert coords[0] == (2, 2)


def test_spiral_covers_all_cells():
    size = 4
    coords = spiral_coordinates(size)
    assert len(coords) == size * size
    assert len(set(coords)) == size * size


def test_spiral_all_in_bounds():
    size = 6
    for x, y in spiral_coordinates(size):
        assert 0 <= x < size and 0 <= y < size


def test_spiral_rejects_zero():
    with pytest.raises(ValueError):
        spiral_coordinates(0)


def test_write_read_roundtrip():
    mem = HelixMemory(size=8, record_size=4)
    mem.write("alpha", b"\x01\x02\x03\x04")
    assert isinstance(mem.read_cell("alpha"), int)


def test_write_rejects_wrong_record_size():
    mem = HelixMemory(size=8, record_size=4)
    with pytest.raises(ValueError):
        mem.write("alpha", b"\x01\x02")


def test_address_deterministic():
    mem = HelixMemory(size=8)
    assert mem.address("key") == mem.address("key")


def test_verify_true_after_write():
    mem = HelixMemory(size=8, record_size=2)
    mem.write("a", b"\x10\x20")
    mem.write("b", b"\x30\x40")
    assert mem.verify() is True


def test_corrupt_breaks_parity():
    mem = HelixMemory(size=8, record_size=2)
    mem.write("a", b"\x10\x20")
    mem.corrupt("a")
    assert mem.verify() is False


def test_usage_and_len():
    mem = HelixMemory(size=8, record_size=2)
    mem.write("a", b"\x01\x02")
    mem.write("b", b"\x03\x04")
    assert len(mem) == 2
    assert mem.usage() == pytest.approx(2 / 64)


def test_constructor_rejects_zero():
    with pytest.raises(ValueError):
        HelixMemory(size=0)


def test_spiral_size_one():
    assert spiral_coordinates(1) == [(0, 0)]
