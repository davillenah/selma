# SELMA

![Version](https://img.shields.io/badge/version-3.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-BSD-green)
![CI](https://github.com/davillenah/selma/actions/workflows/tests.yml/badge.svg)
![Lint](https://img.shields.io/badge/lint-ruff-informational)

Standardized Electrical Load and Modeling Assistant (**SELMA**) is a Python library for *low-voltage electrical conductor sizing- and *protection coordination*, with a strong focus on *standards compliance and full calculation traceability*.

Currently, SELMA is aligned with:

- **AEA 90364 (Argentina)**

## ✨ Key Features

- Deterministic electrical sizing engine
- Ampacity-based conductor selection
- Protection coordination (normative-compliant)
- Voltage drop calculations:
  - GDC method
  - Impedance-based method
- Short-circuit thermal verification
- Full calculation traceability via `trace`
- Modular, domain-driven architecture
- Console and Markdown report generation

## 🧱 Project Structure

```text
src/selma/

  core/              # execution logic
  electrical/        # engineering domain
  data/              # standards & tables
  exporters/         # report generation
  models/            # domain models
  validation/        # input validation
```

## ⚙️ Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/davillenah/selma.git
```

Install a specific version:

```bash
pip install git+https://github.com/davillenah/selma.git@v3.1.0
```

## ✅ Requirements

- Python 3.10+

## 🚀 Quick Example

```python
from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={
        "cos_phi": 0.90,
        "ampacity_margin": 1.00,
    },
)

results = engine.size_project(circuits)
```

## 📚 Documentation

Full documentation is available in the `/docs` folder:

- docs/getting-started.md
- docs/usage.md
- docs/input-model.md
- docs/outputs.md
- docs/architecture.md

## 🧪 Testing

```bash
pytest
```

## 🧹 Code Quality

```bash
ruff check .
ruff format .
```

## 🧠 Design Philosophy

SELMA is built as an engineering tool with:

- deterministic behaviour
- reproducible calculations
- clear and auditable results
- modular architecture

The goal is to deliver a **reliable and extensible electrical calculation engine**.

## 📜 License

See `LICENSE`

## 👤 Author

Developed as a professional electrical engineering sizing engine.

💡 *SELMA is designed to be a reusable, traceable and production-ready tool for electrical system design.*
