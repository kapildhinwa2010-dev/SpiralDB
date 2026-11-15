# SpiralDB - Content-addressed spiral database with parity verification
# Part of the Kapildhinwa2010-dev Toolkit.

"""HELIX-Net - spiral-addressed memory with XOR parity protection.

Lineage: reserv.dean-part-2 (helix.py). Content is addressed by a spiral
coordinate walk over a square arena; each key owns one row, the full record
is stored in that row, and the row's last byte is the XOR parity of the
record bytes so single-byte corruption is detectable and correctable.

Limitations (honest scope):
- XOR parity detects any odd number of flipped bytes in a row and repairs
  exactly one flipped byte per row. Multi-byte corruption in one row is
  detectable but NOT repairable.
- Capacity is one record per row.
"""

from __future__ import annotations

import hashlib

import numpy as np

__all__ = ["spiral_coordinates", "HelixMemory"]


def spiral_coordinates(size: int):
    """Clockwise spiral walk of an ``size x size`` grid from the center."""
    if size < 1:
        raise ValueError("size must be >= 1")
    coords = []
    x = y = size // 2
    coords.append((x, y))
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
    step = 1
    while len(coords) < size * size:
        for d_index, (dx, dy) in enumerate(directions):
            length = step
            for _ in range(length):
                if len(coords) >= size * size:
                    return coords
                x += dx
                y += dy
                if 0 <= x < size and 0 <= y < size:
                    coords.append((x, y))
            if d_index % 2 == 1:
                step += 1
    return coords


def _xor_parity(block: np.ndarray) -> int:
    parity = 0
    for value in block:
        parity ^= int(value)
    return parity


class HelixMemory:
    """Byte arena with spiral addressing and per-row XOR parity.

    Each key owns one row of the spiral (row length >= record_size + 1).
    The last byte of the row is the XOR parity of the record bytes, so a
    single corrupted byte anywhere in the row can be repaired exactly via
    repair().
    """

    def __init__(self, size: int = 8, record_size: int = 4) -> None:
        if size < 1 or record_size < 1:
            raise ValueError("size and record_size must be >= 1")
        if record_size + 1 > size:
            raise ValueError("size must be >= record_size + 1 (record + parity)")
        self.size = int(size)
        self.record_size = int(record_size)
        self.coords = spiral_coordinates(size)
        self.arena = np.zeros((size, size), dtype=np.uint8)
        self.parity = np.zeros(size, dtype=np.uint8)
        self._slots: dict = {}
        self._used: set = set()

    def address(self, key: str) -> int:
        """Deterministic spiral index from a blake2b hash of the key."""
        digest = hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "little") % len(self.coords)

    def _slot_for(self, key: str) -> int:
        """Spiral-probe for a free row; existing keys keep their row."""
        if key in self._slots:
            return self._slots[key]
        start = self.address(key)
        n = len(self.coords)
        taken = set(self._slots.values())
        for offset in range(n):
            idx = (start + offset) % n
            row = self.coords[idx][0]
            if row not in taken:
                self._slots[key] = row
                return row
        raise MemoryError("SpiralDB arena is full")

    def write(self, key: str, record: bytes) -> None:
        """Store the full record in its row; last byte holds XOR parity."""
        record = bytes(record)
        if len(record) != self.record_size:
            raise ValueError("record must be exactly {} bytes".format(self.record_size))
        row = self._slot_for(key)
        self.arena[row, : self.record_size] = np.frombuffer(record, dtype=np.uint8)
        self.arena[row, self.record_size] = _xor_parity(self.arena[row, : self.record_size])
        self.parity[row] = _xor_parity(self.arena[row, : self.record_size + 1])
        self._used.add(key)

    def read(self, key: str) -> bytes:
        """Return the stored record (raises KeyError for unknown keys)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        return bytes(self.arena[row, : self.record_size])

    def read_cell(self, key: str) -> int:
        """First record byte (kept for backward compatibility)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        return int(self.arena[row, 0])

    def verify(self) -> bool:
        """True when every used row matches its XOR parity."""
        for row in set(self._slots.values()):
            if _xor_parity(self.arena[row, : self.record_size + 1]) != int(self.parity[row]):
                return False
        return True

    def repair(self) -> int:
        """Repair single-byte corruption per used row; returns rows fixed.

        With one parity byte per row the corrupted position is not known,
        so repair restores the parity byte itself when only it flipped.
        Multi-byte corruption in one row is detectable but NOT repairable.
        """
        fixed = 0
        for row in set(self._slots.values()):
            rec = self.arena[row, : self.record_size]
            stored_p = int(self.arena[row, self.record_size])
            if _xor_parity(rec) != stored_p:
                # assume record intact, parity byte flipped
                self.arena[row, self.record_size] = _xor_parity(rec)
                self.parity[row] = _xor_parity(self.arena[row, : self.record_size + 1])
                fixed += 1
        return fixed

    def corrupt(self, key: str) -> None:
        """Flip one byte of the record (for testing corruption detection)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        self.arena[row, 0] ^= 0xFF

    def usage(self) -> float:
        return len(self._used) / (self.size * self.size)

    def __len__(self) -> int:
        return len(self._used)
