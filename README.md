# SpiralDB

[![CI](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/ci.yml/badge.svg)](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/codeql.yml/badge.svg)](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/codeql.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Content-addressed spiral database: blake2b-keyed slots, one record per row, XOR parity verification.

**Part of the [Kapildhinwa2010-dev Toolkit](https://github.com/kapildhinwa2010-dev/Kapildhinwa2010-dev).**

## What it does

Keys are hashed with blake2b onto spiral rows; taken rows are probed
spiral-wise. Each row stores one full record plus an XOR parity byte.
verify() detects corruption, read_checked() refuses corrupted rows,
and repair() restores parity bytes. This is the slot-lattice design
the source experiments kept as the safe one.

## Install

    pip install -r requirements.txt

## Quick start

    from spiraldb import HelixMemory

    db = HelixMemory(size=8, record_size=4)
    db.write("alpha", b"\x01\x02\x03\x04")
    print(db.read_checked("alpha"))

## API

- write / read / read_checked / read_cell / verify / repair / corrupt /
  corrupt_parity / usage / address
- spiral_coordinates(size)

## Honest results and limitations

- One XOR parity byte per row DETECTS corruption but cannot locate it.
  repair() restores the parity byte assuming the record is intact; a
  flipped record byte stays corrupted after repair - use read_checked().
- Capacity is one record per row; the arena fills up and raises
  MemoryError instead of evicting.
- Two flipped bytes in one row cancel out and pass verify().
- Research toy, not trustworthy storage. For single-cell correction see
  ECC-Memory (row+column parity).

## License

MIT - see [LICENSE](LICENSE).
