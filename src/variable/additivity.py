from enum import Enum


class Additivity(Enum):
    """
    How a value behaves when the units it describes are combined.

    A unit is whatever a value is attached to, such as a polygon, a time
    interval, or an age group. Additivity is defined separately for each
    ``Dimension``, and which kinds apply depends on the level of measurement.

    Attributes
    ----------
    EXTENSIVE
        The value of combined units is the sum of their values, so it grows
        with the size of the unit. Examples are population over space and
        over age groups, and sales and precipitation over time. Requires a
        true zero, so only ratio variables can be extensive.
    INTENSIVE
        The value does not grow with the size of the unit, and the value of
        combined units is a weighted central value of their values: the
        mean, or for nominal, ordinal, and cyclic variables the mode, the
        median, and the circular mean. Examples are density, rates,
        temperature, and the land use of a parcel. A stock measured at a
        point in time, such as population, is also intensive over time: a
        longer interval does not hold more of it, and its mean over the
        interval is the mean of the parts weighted by their durations.
    MAXIMAL
        The value of combined units is the largest of their values, as for
        the daily maximum temperature over time, the peak flow, the worst
        hazard rank of an area, or whether any part is flooded. Requires an
        order, so nominal and cyclic variables cannot be maximal.
    MINIMAL
        The value of combined units is the smallest of their values, as for
        the daily minimum temperature over time or whether every part is
        flooded. Requires an order, like ``MAXIMAL``.
    FIRST
        The value of combined units is the value of their first part, as for
        an opening balance. Requires an ordered dimension.
    LAST
        The value of combined units is the value of their last part, as for
        a closing balance or a stock reported at the end of each period,
        which data warehouses call semi-additive. Requires an ordered
        dimension.
    NON_ADDITIVE
        The value of combined units cannot be derived from their values and
        must be recomputed from the underlying data. Examples are counts of
        distinct items, such as the number of species, because the same item
        can appear in several units, medians and percentiles, such as the
        median income, and identifiers, such as a municipality code.
    """

    EXTENSIVE = "extensive"
    INTENSIVE = "intensive"
    MAXIMAL = "maximal"
    MINIMAL = "minimal"
    FIRST = "first"
    LAST = "last"
    NON_ADDITIVE = "non-additive"
