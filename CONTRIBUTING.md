# CONTRIBUTING TO SELMA

Thank you for considering contributing to SELMA.

This project aims to provide a structured, traceable and normatively aligned
electrical calculation engine. Contributions are welcome, but must maintain
high standards of technical and software quality.

## Code Philosophy

SELMA follows these principles:

- Deterministic engineering calculations
- Traceability of all results
- Clear separation of responsibilities
- No hidden logic or side effects
- Strict input validation
- Reproducible outputs

## Architecture Overview

The project is organised as a modular library:

```text
src/selma/
  core/
  factors/
  protection/
  selection/
  short_circuit/
  voltage_drop/
  tables/
  validation/
  exporters/
```

Each module has a single responsibility.

## Getting Started

### Clone the repository

```bash
git clone <repo_url>
cd selma
```

### Install in editable mode

```bash
pip install -e .
```

### Install development dependencies

```bash
pip install pytest
```
## Running tests

```bash
pytest
```

Verbose mode:

```bash
pytest -v
```

## Contribution Workflow

1. Fork the repository
2. Create a new branch:

```bash
git checkout -b feature/my-feature
```

3. Make your changes
4. Run tests:

```bash
pytest
```

5. Commit:

```bash
git commit -m "Add my feature"
```

6. Push:

```bash
git push origin feature/my-feature
```

7. Open a Pull Request

## Code Guidelines

### General

* Keep functions pure where possible
* Avoid hidden state
* Avoid duplicated logic
* Prefer explicit over implicit behavior

### Naming

Use descriptive, engineering-friendly naming:

* `compute_...`
* `select_...`
* `calculate_...`
* `resolve_...`

### Structure

Do not mix responsibilities:

* Calculation → `core/`, `selection/`, `factors/`
* Validation → `validation/`
* Rendering → `exporters/`

### Imports

Use package-relative imports:

```python
from ..core.normalization import parse_installation_method
```

Avoid legacy absolute imports like:

```python
from engine...
```

## Tests

### Requirements

Every new feature must include tests.

Tests should:

* validate correctness (not only execution)
* include expected numerical results where applicable
* cover edge cases

### Example test

```python
def test_basic_circuit():
    engine = SelmaEngine()
    result = engine.size_project([circuit])[0]

    assert result["status"] == "OK"
    assert result["cable_section"] is not None
```

## What to Avoid

* Breaking the public API (`SelmaEngine`)
* Introducing non-deterministic behavior
* Adding hardcoded values outside data sources
* Modifying calculation logic without updating tests

## Reporting Bugs

Please include:

* input circuit
* expected result
* actual result
* version used

## Feature Requests

Feature requests should include:

* use case
* engineering justification
* expected behavior

## Style

Keep code:

* clean
* minimal
* explicit
* readable


## Review Criteria

Pull requests will be reviewed based on:

* correctness
* clarity
* consistency with architecture
* test coverage

## License

By contributing, you agree that your contributions will be licensed under the
project's license.

## Final Note

SELMA is not just software — it is an engineering tool.

Contributions must respect:

* technical rigor
* normative consistency
* reproducible results