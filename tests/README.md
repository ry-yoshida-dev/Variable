# tests

## Overview

Pytest suite for the `variable` package. Each test module mirrors a module in `src/variable`.

## Components

| Component | Description |
|-----------|-------------|
| [test_variable.py](./test_variable.py) | Tests for validation, permitted operations, aggregation rules, and warnings of `Variable`. |
| [test_measurement_level.py](./test_measurement_level.py) | Tests for the partial order and kind of `MeasurementLevel`. |
| [test_dimension.py](./test_dimension.py) | Tests for predefined and user-defined `Dimension`s. |
| [test_combination.py](./test_combination.py) | Tests for which additivities of `Combination` take a weight. |

## Examples

```bash
uv run pytest
```
