from enum import Enum


class Operation(Enum):
    """
    Operation on the values of a variable whose meaning depends on its definition.

    These are statistics over a set of values. Combining units into one is
    checked separately, because its meaning depends on the dimension; see
    ``Variable.permits_aggregation``. See ``docs/rules.md`` for which
    variables support each operation.

    Attributes
    ----------
    SUM
        Total of the values, as in a column total. Meaningful only for ratio
        variables that are extensive along some dimension; whether a total
        along a particular dimension is right is checked by
        ``Variable.permits_aggregation``.
    MODE
        Most frequent value. Continuous values rarely repeat, so for them the
        mode is meaningful only after binning them into classes.
    ORDERING
        Comparison by size, including ranks, minimums, and maximums.
    MEDIAN
        Middle value in order.
    DIFFERENCE
        Subtraction of one value from another. For cyclic values the
        difference must be wrapped into one period.
    MEAN
        Arithmetic mean.
    STANDARD_DEVIATION
        Spread around the arithmetic mean.
    CIRCULAR_MEAN
        Mean direction of cyclic values.
    CIRCULAR_STANDARD_DEVIATION
        Spread around the circular mean.
    RATIO
        Division of one value by another, as in "twice as large". Meaningless
        when the values can be negative.
    GEOMETRIC_MEAN
        Mean of the logarithms, transformed back. Meaningless when the values
        can be negative, and undefined when any value is zero, which the
        definition of a variable cannot rule out.
    COEFFICIENT_OF_VARIATION
        Standard deviation divided by the mean. Meaningless when the values
        can be negative, because the mean can then be near zero.
    """

    SUM = "sum"
    MODE = "mode"
    ORDERING = "ordering"
    MEDIAN = "median"
    DIFFERENCE = "difference"
    MEAN = "mean"
    STANDARD_DEVIATION = "standard deviation"
    CIRCULAR_MEAN = "circular mean"
    CIRCULAR_STANDARD_DEVIATION = "circular standard deviation"
    RATIO = "ratio"
    GEOMETRIC_MEAN = "geometric mean"
    COEFFICIENT_OF_VARIATION = "coefficient of variation"
