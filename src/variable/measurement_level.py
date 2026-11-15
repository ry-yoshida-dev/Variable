from __future__ import annotations

from enum import Enum


class MeasurementLevel(Enum):
    """
    Level of measurement of a variable, after Stevens (1946), plus a cyclic level.

    Nominal, ordinal, interval, and ratio form a chain in which each level
    supports the operations of the levels before it plus its own: nominal
    values can only be tested for equality, ordinal values can also be
    ordered, interval values can also be subtracted, and ratio values can also
    be divided because their zero means a true absence. Cyclic values branch
    off the chain after nominal: they can be subtracted within one period, but
    they have no order and no true zero, so they support neither the ordinal
    nor the interval operations. Chrisman (1998) treats cyclic values
    as a level of their own; placing it after nominal is this package's
    simplification.

    Stevens also defined a log-interval scale for values such as pH or
    decibels, whose arithmetic mean is not the mean of the underlying
    quantity. It is not covered: convert such values to that quantity, such
    as a concentration or a power, and define it as a ratio variable.

    Attributes
    ----------
    NOMINAL
        Unordered categories, such as land use or a municipality code.
    ORDINAL
        Ordered categories without meaningful distances, such as a hazard rank.
    INTERVAL
        Numbers with meaningful differences but an arbitrary zero, such as a
        temperature in degrees Celsius or a calendar year.
    RATIO
        Numbers with a true zero, such as population, area, or distance.
    CYCLIC
        Numbers that wrap around after a period, such as a direction in
        degrees or a time of day.
    """

    NOMINAL = "nominal"
    ORDINAL = "ordinal"
    INTERVAL = "interval"
    RATIO = "ratio"
    CYCLIC = "cyclic"

    @property
    def is_quantitative(self) -> bool:
        """
        Whether values are numbers rather than categories.
        """
        match self:
            case MeasurementLevel.NOMINAL | MeasurementLevel.ORDINAL:
                return False
            case (
                MeasurementLevel.INTERVAL
                | MeasurementLevel.RATIO
                | MeasurementLevel.CYCLIC
            ):
                return True

    def is_at_least(self, other: MeasurementLevel) -> bool:
        """
        Whether this level supports every operation that ``other`` supports.

        The levels are only partially ordered, so neither of two levels may be
        at least the other, as for interval and cyclic.

        Parameters
        ----------
        other : MeasurementLevel
            Level to compare with.

        Returns
        -------
        bool
            True when this level is ``other`` or extends it.
        """
        return other in self._supported_levels

    @property
    def _supported_levels(self) -> frozenset[MeasurementLevel]:
        match self:
            case MeasurementLevel.NOMINAL:
                return frozenset({MeasurementLevel.NOMINAL})
            case MeasurementLevel.ORDINAL:
                return MeasurementLevel.NOMINAL._supported_levels | {self}
            case MeasurementLevel.INTERVAL:
                return MeasurementLevel.ORDINAL._supported_levels | {self}
            case MeasurementLevel.RATIO:
                return MeasurementLevel.INTERVAL._supported_levels | {self}
            case MeasurementLevel.CYCLIC:
                return MeasurementLevel.NOMINAL._supported_levels | {self}
