# SpiralDB

SpiralDB is a small Python, in-memory record-store experiment. It assigns string keys to rows in a square byte-array arena using a deterministic BLAKE2b-derived starting position and spiral-order probing. Each row stores one fixed-length record and an XOR parity byte; checked reads also compare the record with a SHA-256 digest retained in memory.

This is an experimental, process-local implementation, not persistent or production-ready database storage.

## Requirements

The project metadata specifies Python 3.9 or later and NumPy 1.24 or later. Install the project from its repository root:

```sh
python -m pip install .
```

## Example

```python
from spiraldb import HelixMemory

db = HelixMemory(size=8, record_size=4)
db.write("alpha", b"\x01\x02\x03\x04")
print(db.read_checked("alpha"))
```

`size` is the arena's row/column dimension. `record_size` is the exact number of bytes accepted by `write`; it must be at least 1, and `size` must be at least `record_size + 1` to leave room for the record and parity byte. Unknown keys raise `KeyError`; records of the wrong length raise `ValueError`.

## Implemented interface

- `spiral_coordinates(size)` returns a clockwise center-out coordinate walk for a square grid; sizes below 1 raise `ValueError`.
- `HelixMemory(size=8, record_size=4)` creates a zero-filled NumPy arena and in-memory key/slot bookkeeping.
- `address(key)` returns a deterministic BLAKE2b-based spiral index. `write(key, record)` stores a fixed-length byte record and its parity; rewriting an existing key keeps its row.
- `read(key)` returns the stored bytes without integrity checks. `read_checked(key)` checks row parity and the in-memory SHA-256 record digest, raising `ValueError` when a mismatch is detected. `read_cell(key)` returns the first record byte.
- `verify()` checks XOR parity for occupied rows. `repair()` rewrites mismatching row parity bytes and returns the number of rows changed.
- `corrupt(key)` and `corrupt_parity(key)` are mutation helpers for exercising record and parity corruption behavior. `usage()` reports a fraction, and `len(db)` returns the number of stored keys.

## Integrity and limitations

- XOR parity can detect many changes, but it cannot locate or correct a damaged record, and changes that cancel under XOR can evade the parity check. `repair()` recomputes parity from the current record bytes; it can restore a corrupted parity byte, but it cannot restore damaged record data. In particular, repairing after record corruption can make `verify()` pass while the record remains wrong. Use `read_checked()` to also compare against the digest captured when the record was written.
- All state, including records, key mappings, parity, and SHA-256 digests, exists only in memory. There is no persistence, serialization, file or network storage, or restart recovery.
- The slot allocator assigns one key per row, so at most `size` keys fit, even though the arena contains `size * size` cells. When no free row remains, `write()` raises `MemoryError`. The current `usage()` calculation divides the number of keys by `size * size`, so it does not represent the fraction of row slots used.
- Records have a single fixed length per instance. The implementation has no deletion, eviction, concurrency controls, or configurable durability/integrity policy.

## Tests and CI

At commit `a9dd6b38848a21debb1d85c1cb5d383b6722b162`, `python3 -m pytest -q` was run and all 6 tests passed. The repository's GitHub Actions CI and CodeQL workflows also have successful completed runs for that same commit. CI runs the tests and a compile/import smoke check on Python 3.10, 3.11, and 3.12; CodeQL is configured for Python analysis.

To run the test suite locally, install the development requirements and run pytest:

```sh
python -m pip install -r requirements.txt
python -m pytest -q
```

## License

The repository includes an MIT License. See [LICENSE](LICENSE).
