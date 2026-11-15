from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class Dimension:
    """
    Direction along which units are combined or split.

    A variable can behave differently along each dimension. Population at a
    point in time adds up over space but not over time, while precipitation
    in millimeters adds up over time but not over space. ``Dimension.SPACE``
    and ``Dimension.TIME`` cover the common cases; define others for any
    breakdown along which values are combined, such as age groups, industry
    classes, depth layers, or monitoring stations.

    Parameters
    ----------
    name : str
        Name of the dimension, such as "age group".
    is_sized : bool
        Whether each unit has a size that values can be weighted or split
        by, such as the area of a polygon, the duration of an interval, or
        the thickness of a layer. Points, instants, and categories such as
        age groups or industries have none.
    is_ordered : bool
        Whether the units follow one another, so that the first and the last
        of them are defined, as for time intervals or depth layers.

    Raises
    ------
    ValueError
        If the name is blank.
    """

    SPACE: ClassVar[Dimension]
    TIME: ClassVar[Dimension]

    name: str
    is_sized: bool
    is_ordered: bool

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name of a dimension must not be blank.")


Dimension.SPACE = Dimension(name="space", is_sized=True, is_ordered=False)
Dimension.TIME = Dimension(name="time", is_sized=True, is_ordered=True)
