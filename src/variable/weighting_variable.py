from typing import Protocol

from .additivity import Additivity
from .dimension import Dimension


class WeightingVariable(Protocol):
    """
    Variable that can weight another, as ``Variable`` does.

    Only a non-negative variable that is extensive along the dimension is
    accepted as a weight; ``Variable`` checks this when it is defined.
    """

    @property
    def name(self) -> str:
        """
        Name of the variable.
        """
        ...

    @property
    def is_signed(self) -> bool | None:
        """
        Whether the values can be negative, or None for non-ratio variables.
        """
        ...

    @property
    def dimensions(self) -> frozenset[Dimension]:
        """
        Dimensions along which units of the variable are combined or split.
        """
        ...

    def additivity(self, dimension: Dimension) -> Additivity:
        """
        How the values behave when units along a dimension are combined.
        """
        ...
