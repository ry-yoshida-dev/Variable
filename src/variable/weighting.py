from enum import Enum


class Weighting(Enum):
    """
    Weighting by the units themselves instead of by another variable.

    Attributes
    ----------
    SIZE
        Weight each unit by its size: area or length over space, duration
        over time, or thickness over depth. Applies only to dimensions whose
        units have a size. Correct for values per unit of size, such as a
        density, or a temperature that holds over the whole unit, and for
        splitting an extensive value that is spread evenly over the unit.
    EQUAL
        Give every unit the same weight, as for points, instants, or
        categories, which have no size.
    """

    SIZE = "size"
    EQUAL = "equal"
