# SpiralDB

Spiral-addressed memory with XOR parity protection.

**Part of the [Kapildhinwa2010-dev Toolkit](https://github.com/kapildhinwa2010-dev/Kapildhinwa2010-dev).**

![CI](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/ci.yml/badge.svg)
![CodeQL](https://github.com/kapildhinwa2010-dev/SpiralDB/actions/workflows/codeql.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- Clockwise spiral coordinate walk over a square arena
- Deterministic string-key addressing
- Row XOR parity detects byte corruption

## 📦 Install

```bash
pip install -r requirements.txt
```

## 🚀 Quick start

```python
from spiraldb import HelixMemory

mem = HelixMemory(size=8, record_size=2)
mem.write('a', b'\x10\x20')
assert mem.verify()
```

## 🧪 Tests

```bash
pytest tests/ -v
```

## 📄 License

MIT — see [LICENSE](LICENSE).
