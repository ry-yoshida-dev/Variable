from enum import Enum


class AggregationMethod(Enum):
    """
    Way to derive the value of a unit made by combining several units.

    Weighted methods weight each part by the weight of the variable's
    ``Combination`` along the dimension.

    Attributes
    ----------
    SUM
        Total of the parts, for extensive variables.
    WEIGHTED_MEAN
        Weighted arithmetic mean, for intensive interval and ratio variables.
    WEIGHTED_CIRCULAR_MEAN
        Weighted circular mean, for intensive cyclic variables.
    WEIGHTED_MEDIAN
        Weighted median, for intensive ordinal variables.
    WEIGHTED_MODE
        Category with the largest total weight, for intensive nominal
        variables. It discards the other categories; to keep them, aggregate
        the share of each category instead, defined as one intensive ratio
        variable per category.
    MAXIMUM
        Largest value of the parts, for maximal variables.
    MINIMUM
        Smallest value of the parts, for minimal variables.
    FIRST
        Value of the first part, for variables that take the first value.
    LAST
        Value of the last part, for variables that take the last value.
    RECOMPUTE
        Computation from the underlying data. Required for non-additive
        variables, and always correct for the others.
    """

    SUM = "sum"
    WEIGHTED_MEAN = "weighted mean"
    WEIGHTED_CIRCULAR_MEAN = "weighted circular mean"
    WEIGHTED_MEDIAN = "weighted median"
    WEIGHTED_MODE = "weighted mode"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    FIRST = "first value"
    LAST = "last value"
    RECOMPUTE = "recomputation"
