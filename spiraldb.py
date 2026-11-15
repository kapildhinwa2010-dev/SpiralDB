# SpiralDB - Content-addressed spiral database with parity verification
# Part of the Kapildhinwa2010-dev Toolkit.

"""SpiralDB - content-addressed record store on a spiral arena.

Lineage: reserv.dean-part-2 (helix.py) - the slot-lattice design that
the source experiments kept as the safe one. Each key owns one row
(blake2b-addressed, spiral-probed when taken); the full record is
stored in that row and the last byte is the row XOR parity.

HONEST SCOPE: one XOR parity byte per row DETECTS any odd number of
flipped bytes but cannot locate them. repair() restores the parity
byte assuming the record is intact; a flipped record byte is detected
but NOT repairable - read_checked() refuses such rows.
"""

from __future__ import annotations

import hashlib

import numpy as np

__all__ = ["spiral_coordinates", "HelixMemory"]


def spiral_coordinates(size: int):
    """Clockwise spiral walk of a size x size grid from the center."""
    if size < 1:
        raise ValueError("size must be >= 1")
    coords = []
    x = y = size // 2
    coords.append((x, y))
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, down, left, up
    step = 1
    while len(coords) < size * size:
        for d_index, (dx, dy) in enumerate(directions):
            for _ in range(step):
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
    """Content-addressed arena: one record per row, XOR parity byte."""

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
        self._row_hashes: dict = {}  # sha256 of record bytes at write time

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
        self._row_hashes[key] = hashlib.sha256(bytes(self.arena[row, : self.record_size])).digest()
        self._used.add(key)

    def read(self, key: str) -> bytes:
        """Return the stored record (raises KeyError for unknown keys)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        return bytes(self.arena[row, : self.record_size])

    def read_checked(self, key: str) -> bytes:
        """Read and verify integrity; raises ValueError on any detected corruption.

        Checks both XOR parity AND the content hash recorded at write time.
        A single-bit record flip passes parity after repair() but fails the hash.
        """
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        rec = bytes(self.arena[row, : self.record_size])
        # Parity check (catches parity-byte flips)
        if _xor_parity(self.arena[row, : self.record_size + 1]) != int(self.parity[row]):
            raise ValueError("row parity mismatch for key: {}".format(key))
        # Content hash check (catches record-byte flips that parity repair masked)
        stored_hash = self._row_hashes.get(key)
        if stored_hash is not None and hashlib.sha256(rec).digest() != stored_hash:
            raise ValueError("content hash mismatch for key: {} (record corrupted)".format(key))
        return rec

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
        """Restore parity bytes of mismatching rows; returns rows touched.

        HONEST SCOPE: with one parity byte the flipped position is
        unknown. repair() assumes the record bytes are intact and
        rewrites the parity byte. A flipped RECORD byte is detected by
        verify() but NOT repairable - repairing after a record flip
        hides the corruption, so prefer read_checked() for reads.
        """
        fixed = 0
        for row in set(self._slots.values()):
            rec = self.arena[row, : self.record_size]
            stored_p = int(self.arena[row, self.record_size])
            if _xor_parity(rec) != stored_p:
                self.arena[row, self.record_size] = _xor_parity(rec)
                self.parity[row] = _xor_parity(self.arena[row, : self.record_size + 1])
                fixed += 1
        return fixed

    def corrupt(self, key: str) -> None:
        """Flip one record byte (detected by verify, NOT repairable)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        self.arena[row, 0] ^= 0xFF

    def corrupt_parity(self, key: str) -> None:
        """Flip the stored parity byte (the case repair() actually fixes)."""
        if key not in self._slots:
            raise KeyError(key)
        row = self._slots[key]
        self.arena[row, self.record_size] ^= 0xFF

    def usage(self) -> float:
        return len(self._used) / (self.size * self.size)

    def __len__(self) -> int:
        return len(self._used)
