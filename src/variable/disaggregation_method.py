from enum import Enum


class DisaggregationMethod(Enum):
    """
    Way to derive the values of the parts when a unit is split.

    Attributes
    ----------
    PROPORTIONAL
        Divide the value among the parts in proportion to the weight of the
        variable's ``Combination``, for extensive variables. ``Weighting.SIZE``
        assumes the quantity is spread evenly over the unit, and an ancillary
        variable, as in dasymetric mapping, assumes it follows that variable.
        A split count becomes fractional and must be rounded by a method that
        keeps the total, if whole numbers are needed.
    REPLICATE
        Give every part the value of the whole, for intensive variables.
        This assumes the unit is homogeneous.
    TOTAL_PRESERVING_INTERPOLATION
        Spread the value smoothly across the parts while keeping the total of
        the unit, as pycnophylactic interpolation does (Tobler 1979). An
        alternative to proportional division for extensive variables.
    INTERPOLATION
        Estimate the values of the parts from the surrounding units, as
        bilinear or cubic resampling or area-to-point kriging do. An
        alternative to replication for intensive quantitative variables.
    RECOMPUTE
        Compute the values of the parts from the underlying data. Required
        for maximal, minimal, first, last, and non-additive variables, and
        always correct for the others. The maximum of the whole is only an
        upper bound for each part, the minimum only a lower bound, and the
        first or last value belongs to one part only.
    """

    PROPORTIONAL = "proportional division"
    REPLICATE = "replication"
    TOTAL_PRESERVING_INTERPOLATION = "total-preserving interpolation"
    INTERPOLATION = "interpolation"
    RECOMPUTE = "recomputation"
