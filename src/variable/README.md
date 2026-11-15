# variable

## Overview

This package defines a variable by independent measurement properties and derives from them the operations that are meaningful and the ways to aggregate and disaggregate its values.

## Components

| Component | Description |
|-----------|-------------|
| [variable.py](./variable.py) | Definition of a variable, its validation, and the rules derived from it. |
| [measurement_level.py](./measurement_level.py) | Enum of the levels of measurement: nominal, ordinal, interval, ratio, and cyclic. |
| [dimension.py](./dimension.py) | Dimension along which units are combined, with space and time predefined and others user-defined. |
| [combination.py](./combination.py) | How a variable combines and splits along one dimension: its additivity and the weight it needs. |
| [additivity.py](./additivity.py) | Enum telling how values behave when units are combined: summed, averaged, maximum, minimum, first, last, or recomputed. |
| [weighting.py](./weighting.py) | Enum of the weightings by the units themselves: by size or equal. |
| [weighting_variable.py](./weighting_variable.py) | Protocol of a variable that can weight another. |
| [operation.py](./operation.py) | Enum of the operations whose meaning depends on the variable. |
| [aggregation_method.py](./aggregation_method.py) | Enum of the ways to combine the values of several units. |
| [disaggregation_method.py](./disaggregation_method.py) | Enum of the ways to split the value of a unit into parts. |
| [meaningless_operation_warning.py](./meaningless_operation_warning.py) | Warning for operations whose results are not meaningful. |
| [dimension_not_combined_error.py](./dimension_not_combined_error.py) | Error for asking about a dimension a variable is not combined along. |
