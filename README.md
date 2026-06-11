# SELMA

**SELMA*- (**S**tandardized **E**lectrical **L**oad and **M**odeling **A**ssistant) es una librería Python para el **dimensionamiento de conductores eléctricos de baja tensión*- y la **selección/coordinación de protecciones*- con enfoque normativo y trazabilidad técnica.

Actualmente, SELMA está orientada al uso con la norma:

- **AEA 90364**

La librería permite:

- calcular corrientes de proyecto a partir de distintas unidades de carga,
- seleccionar la sección del conductor por:
  - ampacidad,
  - protección,
  - caída de tensión,
  - cortocircuito,
- generar reportes técnicos en consola,
- exportar reportes en formato Markdown.

## Características principales

- Arquitectura modular orientada a librería
- Uso directo desde Python mediante `import selma`
- Separación clara entre:
  - motor de cálculo,
  - validaciones,
  - tablas normativas,
  - exportadores
- Trazabilidad técnica mediante `trace`
- Reportes independientes:
  - detallado,
  - ejecutivo,
  - visual / bitácora
- Preparado para escalar a futuras normas y exportadores

## Estructura general del proyecto

```text
src/
  selma/
    core/
    data/
    exporters/
    factors/
    models/
    protection/
    selection/
    short_circuit/
    sources/
    tables/
    validation/
    voltage_drop/
    service.py
    api.py
    __init__.py
```

## Instalación

### Instalación editable para desarrollo

Desde la raíz del proyecto:

```bash
pip install -e .
```

### Verificación rápida

```bash
python -c "from selma import SelmaEngine; print('SELMA OK')"
```

## Requisitos

- Python **3.10*- o superior

## Uso rápido

```python
from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={
        "cos_phi": 0.90,
        "ampacity_margin": 1.00,
    },
)

circuits = [
    {
        "tag": "C-01",
        "origin": "TAB",
        "destination": "Iluminación",
        "purpose": {
            "type": "lighting",
            "subtype": "iug",
        },
        "electrical": {
            "phase_type": "1PH",
            "voltage_v": 220,
            "parallels": 1,
            "length_m": 25.0,
            "load": {
                "value": 1.5,
                "unit": "kVA",
            },
        },
        "installation": {
            "installation_method": "B2-2x",
            "material": "Cu",
            "insulation": "PVC",
            "installation_temp_c": 30.0,
            "grouped_circuits": 1,
            "soil_type": "default",
            "wire_burial_depth_m": 0.0,
        },
        "short_circuit": {
            "mode": "skip",
            "Icc_kA": 4.5,
            "time_s": 0.5,
        },
        "cable": {
            "voltage_drop_method": "GDC",
            "reactance_ohm_per_m": 0.0,
            "mode": "auto",
            "section_mm2": None,
        },
    }
]

results = engine.size_project(circuits)

print(results)
print(engine.render_detailed_report(results))
print(engine.render_executive_report(results))
print(engine.render_visual_report(results))
```

## Flujo típico de trabajo

El flujo recomendado con SELMA es:

1. definir el estándar,
2. definir los criterios globales,
3. construir la lista de circuitos,
4. ejecutar el motor,
5. revisar los resultados,
6. renderizar o exportar reportes.

Ejemplo:

```python
from selma import SelmaEngine

STANDARD = "aea90364"

CRITERIA = {
    "cos_phi": 0.90,
    "ampacity_margin": 1.00,
}

engine = SelmaEngine(
    standard=STANDARD,
    criteria=CRITERIA,
)

results = engine.size_project(circuits)
```

## Modelo de entrada

Cada circuito se define como un diccionario con la siguiente estructura general:

```python
{
    "tag": "...",
    "origin": "...",
    "destination": "...",
    "purpose": {
        "type": "...",
        "subtype": "...",
    },
    "electrical": {
        "phase_type": "...",
        "voltage_v": ...,
        "parallels": ...,
        "length_m": ...,
        "load": {
            "value": ...,
            "unit": "...",
        },
    },
    "installation": {
        "installation_method": "...",
        "material": "...",
        "insulation": "...",
        "installation_temp_c": ...,
        "grouped_circuits": ...,
        "soil_type": "...",
        "wire_burial_depth_m": ...,
    },
    "short_circuit": {
        "mode": "...",
        "Icc_kA": ...,
        "time_s": ...,
    },
    "cable": {
        "voltage_drop_method": "...",
        "reactance_ohm_per_m": ...,
        "mode": "...",
        "section_mm2": ...,
    },
}
```

## Campos principales

### `purpose`

Representa el propósito del circuito.

Ejemplos:

```python
{"type": "lighting", "subtype": "iug"}
{"type": "lighting", "subtype": "iue"}
{"type": "outlet", "subtype": "tug"}
{"type": "outlet", "subtype": "tue"}
{"type": "power", "subtype": "general"}
{"type": "motor", "subtype": "direct"}
{"type": "motor", "subtype": "heavy"}
{"type": "board", "subtype": "distribution"}
```

### `electrical.load.unit`

Unidades soportadas:

- `A`
- `W`
- `kW`
- `MW`
- `VA`
- `kVA`
- `MVA`
- `HP`

### `installation.installation_method`

Valores típicos soportados:

- `B1-2x`
- `B1-3x`
- `B2-2x`
- `B2-3x`
- `C-2x`
- `C-3x`
- `E-2x`
- `E-3x`
- `F-2x`
- `F-3xT`
- `F-3xP`
- `G-3xH`
- `G-3xV`
- `D1-2x`
- `D1-3x`
- `D2-1x`
- `D2-2xA`
- `D2-2xB`
- `D2-3xA`
- `D2-3xB`

### `short_circuit.mode`

Modos soportados:

- `manual`
- `board_icc`
- `skip`

### `cable.voltage_drop_method`

Métodos soportados:

- `GDC`
- `IMPEDANCE`

### `cable.mode`

Opciones soportadas:

- `auto`
- `fixed`


## Resultados

`engine.size_project(...)` devuelve una lista de resultados, uno por circuito.

Cada resultado incluye, entre otros:

- `status`
- `checks`
- `trace`
- `current_a`
- `cable_section`
- `pe_section_mm2`
- `protection`
- `protection_curve`
- `voltage_drop_pct`

Ejemplo simplificado:

```python
[
    {
        "tag": "C-01",
        "status": "OK",
        "current_a": 10.0,
        "cable_section": "PVC 2x2.5mm² + PE2.5mm² Cu",
        "protection": "MCB - 2x10A - Curva B",
        "voltage_drop_pct": 1.85,
        "checks": {
            "ampacity": True,
            "protection_coordination": True,
            "voltage_drop": True,
            "short_circuit": True,
            "minimum_section": True,
        },
        "trace": {
            ...
        },
    }
]
```

## Reportes disponibles

SELMA ofrece tres renderizadores principales:

### 1. Reporte detallado

```python
engine.render_detailed_report(results)
```

Devuelve un reporte técnico detallado en Markdown.

### 2. Reporte ejecutivo

```python
engine.render_executive_report(results)
```

Devuelve una salida resumida tipo pliego o resumen ejecutivo.

### 3. Reporte visual / bitácora

```python
engine.render_visual_report(results)
```

Devuelve una bitácora técnica de cálculo en Markdown.

## Exportación de reportes

Si quieres exportar los reportes a archivos Markdown:

```python
engine.export_reports(results, output_dir="outputs")
```

Esto genera los archivos en la carpeta indicada.

## Ejemplo básico

```python
from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={"cos_phi": 0.90, "ampacity_margin": 1.00},
)

circuits = [
    {
        "tag": "C-01",
        "origin": "TAB",
        "destination": "Iluminación",
        "purpose": {"type": "lighting", "subtype": "iug"},
        "electrical": {
            "phase_type": "1PH",
            "voltage_v": 220,
            "parallels": 1,
            "length_m": 20.0,
            "load": {"value": 1.5, "unit": "kVA"},
        },
        "installation": {
            "installation_method": "B2-2x",
            "material": "Cu",
            "insulation": "PVC",
            "installation_temp_c": 30.0,
            "grouped_circuits": 1,
            "soil_type": "default",
            "wire_burial_depth_m": 0.0,
        },
        "short_circuit": {
            "mode": "skip",
            "Icc_kA": 4.5,
            "time_s": 0.5,
        },
        "cable": {
            "voltage_drop_method": "GDC",
            "reactance_ohm_per_m": 0.0,
            "mode": "auto",
            "section_mm2": None,
        },
    }
]

results = engine.size_project(circuits)

for r in results:
    print(r["tag"], r["status"], r["cable_section"], r["protection"])
```

## Ejemplo con múltiples circuitos

```python
from copy import deepcopy
from selma import SelmaEngine

engine = SelmaEngine(
    standard="aea90364",
    criteria={"cos_phi": 0.90, "ampacity_margin": 1.00},
)

base_circuit = {
    "origin": "TAB",
    "destination": "Aire acondicionado",
    "purpose": {"type": "motor", "subtype": "direct"},
    "electrical": {
        "phase_type": "1PH",
        "voltage_v": 220,
        "parallels": 1,
        "length_m": 24.0,
        "load": {"value": 14, "unit": "A"},
    },
    "installation": {
        "installation_method": "B2-2x",
        "material": "Cu",
        "insulation": "PVC",
        "installation_temp_c": 40.0,
        "grouped_circuits": 1,
        "soil_type": "default",
        "wire_burial_depth_m": 0.0,
    },
    "short_circuit": {
        "mode": "skip",
        "Icc_kA": 4.5,
        "time_s": 0.5,
    },
    "cable": {
        "voltage_drop_method": "GDC",
        "reactance_ohm_per_m": 0.0,
        "mode": "auto",
        "section_mm2": None,
    },
}

circuits = []

for i in range(1, 6):
    c = deepcopy(base_circuit)
    c["tag"] = f"C-{i:02d}"
    circuits.append(c)

results = engine.size_project(circuits)

for r in results:
    print(r["tag"], r["status"], r["cable_section"], r["protection"])
```

## Ejemplos incluidos

Se recomienda incluir en la carpeta `examples/` archivos como:

- `example_basic.py`
- `example_intermediate.py`
- `example_advanced.py`


## Tests

Para ejecutar los tests:

```bash
pytest
```

Para ejecutar un test específico:

```bash
pytest tests/test_engine_regression.py
```

Para ver salida detallada:

```bash
pytest -v
```

## Desarrollo

Instalación de desarrollo:

```bash
pip install -e .
pip install pytest
```

Lint / formato (si usas Ruff):

```bash
ruff check .
ruff format .
```

## Filosofía de diseño

SELMA está estructurado como una librería profesional con separación por responsabilidades:

- `core/` → lógica base
- `factors/` → factores de corrección
- `protection/` → coordinación de protecciones
- `selection/` → selección de sección
- `short_circuit/` → verificación térmica al cortocircuito
- `voltage_drop/` → métodos de caída de tensión
- `exporters/` → renderizado y exportación
- `validation/` → validación de entradas
- `data/` → tablas normativas empaquetadas

## Limitaciones actuales

- Enfoque actual orientado a **AEA 90364**
- Exportación principal en **Markdown**
- La metadata de proyecto puede existir a nivel aplicación, pero el motor se centra en el cálculo técnico

## Hoja de ruta sugerida

Posibles extensiones futuras:

- soporte para otras normas,
- CLI (`selma run project.json`),
- importación desde JSON / Excel,
- exportación a PDF / DOCX,
- integración con interfaces gráficas,
- validación avanzada de escenarios normativos.

## Licencia

Ver archivo `LICENSE`.

## Autoría

Desarrollado como motor técnico de cálculo para dimensionamiento eléctrico de baja tensión y generación de documentación técnica trazable.

## Ejecución rápida recomendada

```bash
pip install -e .
python examples/example_basic.py
```

## Resumen

SELMA permite pasar de un conjunto de datos de circuito a un resultado técnico estructurado mediante:

1. validación,
2. cálculo,
3. selección,
4. verificación,
5. generación de reportes.

Su objetivo es facilitar la construcción de herramientas de ingeniería eléctrica mantenibles, auditables y reutilizables desde Python.