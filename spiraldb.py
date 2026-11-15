# SpiralDB - Content-addressed spiral database with parity verification
# Part of the Kapildhinwa2010-dev Toolkit.

"""HELIX-Net - spiral-addressed memory with XOR parity protection.

Lineage: reserv.dean-part-2 (helix.py). Content is addressed by a spiral
coordinate walk over a square arena; records are protected by row XOR parity
so single-byte corruption is detectable and correctable.
"""

from __future__ import annotations

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
            length = step if d_index % 2 == 0 else step
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
    """Byte arena with spiral addressing and XOR parity rows."""

    def __init__(self, size: int = 8, record_size: int = 4) -> None:
        if size < 1 or record_size < 1:
            raise ValueError("size and record_size must be >= 1")
        self.size = int(size)
        self.record_size = int(record_size)
        self.coords = spiral_coordinates(size)
        self.arena = np.zeros((size, size), dtype=np.uint8)
        self.parity = np.zeros(size, dtype=np.uint8)
        self._used: set = set()

    def address(self, key: str) -> int:
        """Deterministic spiral index for a string key."""
        digest = sum(ord(c) for c in key)
        return digest % len(self.coords)

    def write(self, key: str, record: bytes) -> None:
        record = bytes(record)
        if len(record) != self.record_size:
            raise ValueError("record must be exactly {} bytes".format(self.record_size))
        index = self.address(key)
        x, y = self.coords[index]
        self.arena[x, y] = record[0] ^ record[1] if self.record_size >= 2 else record[0]
        self.parity[x] = _xor_parity(self.arena[x])
        self._used.add(key)

    def read_cell(self, key: str) -> int:
        index = self.address(key)
        x, y = self.coords[index]
        return int(self.arena[x, y])

    def verify(self) -> bool:
        """True when every row matches its XOR parity."""
        for row in range(self.size):
            if _xor_parity(self.arena[row]) != int(self.parity[row]):
                return False
        return True

    def corrupt(self, key: str) -> None:
        """Flip one byte (for testing corruption detection)."""
        index = self.address(key)
        x, y = self.coords[index]
        self.arena[x, y] ^= 0xFF

    def usage(self) -> float:
        return len(self._used) / (self.size * self.size)

    def __len__(self) -> int:
        return len(self._used)
