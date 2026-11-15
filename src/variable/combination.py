from __future__ import annotations

from dataclasses import dataclass

from .additivity import Additivity
from .weighting import Weighting
from .weighting_variable import WeightingVariable


@dataclass(frozen=True, kw_only=True)
class Combination:
    """
    How the values of a variable combine and split along one dimension.

    The weight is the measure over which the variable is spread. An intensive
    variable is averaged by it, as income per person is averaged by
    population. An extensive variable is divided among the parts of a split
    unit in proportion to it, as population is divided by area or, in
    dasymetric mapping, by residential floor area. The other additivities
    neither average nor divide, so they take no weight. Use the class
    methods, which take a weight only where one applies.

    Parameters
    ----------
    additivity : Additivity
        How the values behave when units are combined.
    weight : WeightingVariable | Weighting | None
        A non-negative variable that is extensive along the dimension, or a
        ``Weighting``. Required for extensive and intensive additivity and
        None otherwise.

    Raises
    ------
    ValueError
        If a weight is missing for extensive or intensive additivity, or
        given for another.
    """

    additivity: Additivity
    weight: WeightingVariable | Weighting | None

    def __post_init__(self) -> None:
        match self.additivity:
            case Additivity.EXTENSIVE | Additivity.INTENSIVE:
                if self.weight is None:
                    raise ValueError(
                        f"{self.additivity.value} additivity requires a weight; pass a variable such as population, or a Weighting."
                    )
            case _:
                if self.weight is not None:
                    raise ValueError(
                        f"{self.additivity.value} additivity neither averages nor divides values, so it takes no weight."
                    )

    @classmethod
    def extensive(cls, weight: WeightingVariable | Weighting) -> Combination:
        """
        Sum the values when units are combined, and divide them when a unit is split.

        Parameters
        ----------
        weight : WeightingVariable | Weighting
            Measure in proportion to which the value of a unit is divided
            among its parts, such as ``Weighting.SIZE`` for an even spread
            over area, or residential floor area for population.

        Returns
        -------
        Combination
            Extensive combination.
        """
        return cls(additivity=Additivity.EXTENSIVE, weight=weight)

    @classmethod
    def intensive(cls, weight: WeightingVariable | Weighting) -> Combination:
        """
        Take the weighted central value when units are combined.

        Parameters
        ----------
        weight : WeightingVariable | Weighting
            Weight of each unit, such as population for income per person or
            ``Weighting.SIZE`` for a density.

        Returns
        -------
        Combination
            Intensive combination.
        """
        return cls(additivity=Additivity.INTENSIVE, weight=weight)

    @classmethod
    def maximal(cls) -> Combination:
        """
        Take the largest value when units are combined.
        """
        return cls(additivity=Additivity.MAXIMAL, weight=None)

    @classmethod
    def minimal(cls) -> Combination:
        """
        Take the smallest value when units are combined.
        """
        return cls(additivity=Additivity.MINIMAL, weight=None)

    @classmethod
    def first(cls) -> Combination:
        """
        Take the value of the first unit when units are combined.
        """
        return cls(additivity=Additivity.FIRST, weight=None)

    @classmethod
    def last(cls) -> Combination:
        """
        Take the value of the last unit when units are combined.
        """
        return cls(additivity=Additivity.LAST, weight=None)

    @classmethod
    def non_additive(cls) -> Combination:
        """
        Recompute the value from the underlying data when units are combined.
        """
        return cls(additivity=Additivity.NON_ADDITIVE, weight=None)
