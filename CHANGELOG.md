# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on **Keep a Changelog**
and this project adheres to **Semantic Versioning (SemVer)**.

## [3.1.0] - 2026-06-10

### Changed
- Major internal refactor of project structure:
  - Introduced `electrical/` domain layer
  - Consolidated engineering logic under cohesive modules
  - Removed redundant naming across modules and data packages

### Improved
- Simplified module naming (removed redundant prefixes like `voltage_drop_*`)
- Cleaner package layout aligned with domain-driven design principles
- Improved import structure (more intuitive and maintainable)

### Refactored
- Moved:
  - selection → electrical.conductor
  - protection → electrical.protection
  - voltage_drop → electrical.voltage_drop
  - short_circuit → electrical.short_circuit
- Renamed:
  - service.py → sizing.py
  - schemas.py → domain.py
  - common.py → exporters.utils

### Fixed
- Broken imports after restructuring
- Resource loading paths for JSON data (standards folder)
- Missing `__init__.py` issues
- Ruff lint errors (ARG, F, SIM, etc.)
- Duplicate function definitions in exporters

### Quality
- Achieved full Ruff compliance:
  - E, F, I, B, UP, ARG, RET, SIM rules
- Maintained full test coverage:
  - ✅ 14/14 tests passing after refactor
- Codebase cleaned from unused variables and dead code

### Notes
- No breaking changes to public API (`SelmaEngine`)
- Internal architecture now stable for future extensions

## [3.0.0] - 2026-06-10

### Added
- Complete refactor to a modular library-based architecture.
- `SelmaEngine` as the main public API.
- Support for multiple circuit processing (`size_project`).
- Full traceability via `trace` outputs.
- Exporters:
  - Detailed report
  - Executive report
  - Visual/calculation log report
- Structured input model with:
  - `purpose` (type + subtype)
  - `electrical`
  - `installation`
  - `short_circuit`
  - `cable`
- Support for:
  - Ampacity selection
  - Voltage drop (GDC / Impedance)
  - Protection selection and coordination
  - Short-circuit thermal verification
- Support for parallel conductors.

### Changed
- Migration from monolithic script to modular package (`src/selma`).
- All internal imports updated to package-relative structure.
- Separation of:
  - calculation logic
  - validation
  - exporters
- Removal of implicit global state.
- Inputs now validated before calculation.

### Fixed
- Protection selection returning incorrect type (float → object).
- Multiple legacy `engine.*` import issues.
- Voltage drop router dependencies.
- Missing helper functions in exporters.
- Template injection errors in reports.

## [2.x.x] - Legacy versions

### Notes
- Monolithic script-based implementation.
- Limited separation of concerns.
- No package structure.
- No formal test suite.

## [1.x.x] - Initial prototype

### Notes
- Early experimentation with electrical calculation logic.
- No modular architecture.
- No formal API.

## Upcoming (Planned)

### Added (planned)
- CLI interface:
  - `selma run project.json`
- JSON/Excel input support.
- PDF export (technical report).
- Support for additional standards (IEC, NEC).
- Web/API integration.

## Versioning Strategy

This project follows **Semantic Versioning**:

- MAJOR: breaking changes in API or behavior
- MINOR: new features without breaking changes
- PATCH: bug fixes

## Notes

This changelog is intended to provide a clear evolution of SELMA as a technical
engineering tool and library.