from __future__ import annotations

import math
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field

from .additivity import Additivity
from .aggregation_method import AggregationMethod
from .combination import Combination
from .dimension import Dimension
from .dimension_not_combined_error import DimensionNotCombinedError
from .disaggregation_method import DisaggregationMethod
from .meaningless_operation_warning import MeaninglessOperationWarning
from .measurement_level import MeasurementLevel
from .operation import Operation
from .weighting import Weighting
from .weighting_variable import WeightingVariable


@dataclass(frozen=True, kw_only=True)
class Variable:
    """
    Definition of a variable by its measurement properties.

    The properties are independent axes: the level of measurement, a
    ``Combination`` for each dimension along which units are combined or
    split, a period for cyclic variables, and for ratio variables whether
    they can be negative. Every property must be given, and None states that
    it does not apply; the class methods ``nominal``, ``ordinal``,
    ``interval``, ``ratio``, and ``cyclic`` fill in the ones that never apply
    to their level.

    Which additivities a level takes:

    - Nominal: intensive, first, last, non-additive.
    - Ordinal: those of nominal, plus maximal and minimal.
    - Interval: all but extensive, which needs a true zero.
    - Ratio: all.
    - Cyclic: those of nominal, because its values have no order.

    First and last apply only along ordered dimensions, and
    ``Weighting.SIZE`` only along dimensions whose units have a size.

    Parameters
    ----------
    name : str
        Name of the variable, such as an attribute name.
    level : MeasurementLevel
        Level of measurement.
    combinations : Mapping[Dimension, Combination]
        How the values combine and split along each dimension. Leave out a
        dimension along which units are never combined or split, such as
        time for a single snapshot. At least one dimension is required.
    period : float | None
        Length of the cycle, such as 360 for a direction in degrees or 24 for
        a time of day in hours. Required for cyclic variables and None
        otherwise.
    is_signed : bool | None
        Whether the values can be negative, as for profit or net migration.
        Required for ratio variables and None otherwise. Negative values
        keep the zero meaningful but make ratios meaningless.

    Raises
    ------
    TypeError
        If the period is a bool.
    ValueError
        If the name is blank, no dimension is given, two dimensions share a
        name apart from case and spacing, or the properties contradict each
        other, the level, or the dimensions of a weight.
    """

    name: str
    level: MeasurementLevel
    # A mapping cannot be hashed; the other fields identify the variable well enough.
    combinations: Mapping[Dimension, Combination] = field(hash=False)
    period: float | None
    is_signed: bool | None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be blank.")
        if not self.combinations:
            raise ValueError(
                f"{self.name!r} must be combined along at least one dimension."
            )
        # Copy so that later changes to the caller's mapping cannot alter a frozen
        # variable; the Mapping type keeps the copy read-only for type-checked code.
        object.__setattr__(self, "combinations", dict(self.combinations))
        names: list[str] = [
            _normalize(dimension.name) for dimension in self.combinations
        ]
        if len(set(names)) != len(names):
            raise ValueError(
                f"{self.name!r} has several dimensions of the same name with different definitions."
            )
        self._validate_period()
        self._validate_sign()
        for dimension, combination in self.combinations.items():
            self._validate_additivity(dimension, combination.additivity)
            self._validate_weight(dimension, combination.weight)

    def _validate_period(self) -> None:
        if self.level is not MeasurementLevel.CYCLIC:
            if self.period is not None:
                raise ValueError(
                    f"{self.name!r} is {self.level.value}, so it takes no period; define a variable that wraps around as cyclic."
                )
            return
        if self.period is None:
            raise ValueError(f"{self.name!r} is cyclic, so a period is required.")
        if isinstance(self.period, bool):
            raise TypeError(f"period of {self.name!r} must be a number, not a bool.")
        if not math.isfinite(self.period) or self.period <= 0:
            raise ValueError(
                f"period of {self.name!r} must be positive and finite, got {self.period}."
            )

    def _validate_sign(self) -> None:
        if self.level is MeasurementLevel.RATIO:
            if self.is_signed is None:
                raise ValueError(
                    f"{self.name!r} is ratio, so whether it can be negative is required."
                )
        elif self.is_signed is not None:
            raise ValueError(
                f"{self.name!r} is {self.level.value}, so it takes no sign; only ratio variables tell whether they can be negative."
            )

    def _validate_additivity(
        self, dimension: Dimension, additivity: Additivity
    ) -> None:
        match additivity:
            case Additivity.EXTENSIVE:
                if self.level is not MeasurementLevel.RATIO:
                    raise ValueError(
                        f"{self.name!r} is {self.level.value} and has no true zero, so it cannot be extensive over {dimension.name}."
                    )
            case Additivity.MAXIMAL | Additivity.MINIMAL:
                if not self.level.is_at_least(MeasurementLevel.ORDINAL):
                    raise ValueError(
                        f"{self.name!r} is {self.level.value} and has no order, so it cannot be {additivity.value} over {dimension.name}."
                    )
            case Additivity.FIRST | Additivity.LAST:
                if not dimension.is_ordered:
                    raise ValueError(
                        f"{dimension.name} is not ordered, so {self.name!r} cannot take the {additivity.value} value over it."
                    )
            case Additivity.INTENSIVE | Additivity.NON_ADDITIVE:
                pass

    def _validate_weight(
        self, dimension: Dimension, weight: WeightingVariable | Weighting | None
    ) -> None:
        match weight:
            case None | Weighting.EQUAL:
                return
            case Weighting.SIZE:
                if not dimension.is_sized:
                    raise ValueError(
                        f"units along {dimension.name} have no size, so {self.name!r} cannot be weighted by size over it; use Weighting.EQUAL or a variable."
                    )
            case _:
                for defined in weight.dimensions:
                    _require_same_definition(defined, dimension, weight.name)
                if (
                    dimension not in weight.dimensions
                    or weight.additivity(dimension) is not Additivity.EXTENSIVE
                ):
                    raise ValueError(
                        f"{dimension.name} weight {weight.name!r} of {self.name!r} must be extensive over {dimension.name}."
                    )
                if weight.is_signed is not False:
                    raise ValueError(
                        f"{dimension.name} weight {weight.name!r} of {self.name!r} must not be negative."
                    )
                # A frozen variable cannot contain itself, so only a different
                # definition under the same attribute name can get here.
                if weight.name == self.name:
                    raise ValueError(
                        f"{self.name!r} cannot be weighted by itself or by another variable of the same name."
                    )

    @classmethod
    def nominal(
        cls, name: str, *, combinations: Mapping[Dimension, Combination]
    ) -> Variable:
        """
        Define a variable of unordered categories.

        Parameters
        ----------
        name : str
            Name of the variable.
        combinations : Mapping[Dimension, Combination]
            How the values combine and split along each dimension: intensive
            for a category that describes the whole unit, such as land use,
            or non-additive for an identifier, such as a municipality code.

        Returns
        -------
        Variable
            Nominal variable.

        Raises
        ------
        ValueError
            If no dimension is given or a combination does not apply.
        """
        return cls(
            name=name,
            level=MeasurementLevel.NOMINAL,
            combinations=combinations,
            period=None,
            is_signed=None,
        )

    @classmethod
    def ordinal(
        cls, name: str, *, combinations: Mapping[Dimension, Combination]
    ) -> Variable:
        """
        Define a variable of ordered categories.

        A yes-or-no flag, such as whether a place is flooded, is ordinal with
        no before yes: maximal tells whether any part is flooded, and minimal
        whether every part is.

        Parameters
        ----------
        name : str
            Name of the variable.
        combinations : Mapping[Dimension, Combination]
            How the values combine and split along each dimension, such as
            maximal for the worst hazard rank of an area.

        Returns
        -------
        Variable
            Ordinal variable.

        Raises
        ------
        ValueError
            If no dimension is given or a combination does not apply.
        """
        return cls(
            name=name,
            level=MeasurementLevel.ORDINAL,
            combinations=combinations,
            period=None,
            is_signed=None,
        )

    @classmethod
    def interval(
        cls, name: str, *, combinations: Mapping[Dimension, Combination]
    ) -> Variable:
        """
        Define a quantitative variable with an arbitrary zero.

        Parameters
        ----------
        name : str
            Name of the variable.
        combinations : Mapping[Dimension, Combination]
            How the values combine and split along each dimension. Anything
            but extensive, because the values have no true zero.

        Returns
        -------
        Variable
            Interval variable.

        Raises
        ------
        ValueError
            If no dimension is given or a combination does not apply.
        """
        return cls(
            name=name,
            level=MeasurementLevel.INTERVAL,
            combinations=combinations,
            period=None,
            is_signed=None,
        )

    @classmethod
    def ratio(
        cls,
        name: str,
        *,
        is_signed: bool,
        combinations: Mapping[Dimension, Combination],
    ) -> Variable:
        """
        Define a quantitative variable with a true zero.

        Parameters
        ----------
        name : str
            Name of the variable.
        is_signed : bool
            Whether the values can be negative, as for profit or net
            migration. Ratios between values are then meaningless.
        combinations : Mapping[Dimension, Combination]
            How the values combine and split along each dimension.

        Returns
        -------
        Variable
            Ratio variable.

        Raises
        ------
        ValueError
            If no dimension is given or a combination does not apply.
        """
        return cls(
            name=name,
            level=MeasurementLevel.RATIO,
            combinations=combinations,
            period=None,
            is_signed=is_signed,
        )

    @classmethod
    def cyclic(
        cls,
        name: str,
        *,
        period: float,
        combinations: Mapping[Dimension, Combination],
    ) -> Variable:
        """
        Define a quantitative variable that wraps around after a period.

        Parameters
        ----------
        name : str
            Name of the variable.
        period : float
            Length of the cycle, such as 360 for a direction in degrees or 24
            for a time of day in hours.
        combinations : Mapping[Dimension, Combination]
            How the values combine and split along each dimension: intensive,
            first, last, or non-additive, because the values have no order.

        Returns
        -------
        Variable
            Cyclic variable.

        Raises
        ------
        ValueError
            If the period is not positive and finite, no dimension is given,
            or a combination does not apply.
        """
        return cls(
            name=name,
            level=MeasurementLevel.CYCLIC,
            combinations=combinations,
            period=period,
            is_signed=None,
        )

    @property
    def is_cyclic(self) -> bool:
        """
        Whether the values wrap around after a period.
        """
        return self.level is MeasurementLevel.CYCLIC

    @property
    def dimensions(self) -> frozenset[Dimension]:
        """
        Dimensions along which units of this variable are combined or split.
        """
        return frozenset(self.combinations)

    def additivity(self, dimension: Dimension) -> Additivity:
        """
        How the values behave when units along a dimension are combined.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which units are combined.

        Returns
        -------
        Additivity
            Additivity along the dimension.

        Raises
        ------
        DimensionNotCombinedError
            If the variable is not combined along the dimension.
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        return self._combination(dimension).additivity

    def weight(self, dimension: Dimension) -> WeightingVariable | Weighting | None:
        """
        Measure over which the values are spread along a dimension.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which units are combined or split.

        Returns
        -------
        WeightingVariable | Weighting | None
            Weight along the dimension, or None when the values are neither
            averaged nor divided along it.

        Raises
        ------
        DimensionNotCombinedError
            If the variable is not combined along the dimension.
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        return self._combination(dimension).weight

    def _combination(self, dimension: Dimension) -> Combination:
        if not self._is_combined(dimension):
            raise DimensionNotCombinedError(
                f"{self.name!r} is not combined or split over {dimension.name}."
            )
        return self.combinations[dimension]

    def _is_combined(self, dimension: Dimension) -> bool:
        for defined in self.combinations:
            _require_same_definition(defined, dimension, self.name)
        return dimension in self.combinations

    def aggregation_method(self, dimension: Dimension) -> AggregationMethod:
        """
        Way to derive the value of a unit made by combining units along a dimension.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which units are combined.

        Returns
        -------
        AggregationMethod
            Method that gives the value of the combined unit.

        Raises
        ------
        DimensionNotCombinedError
            If the variable is not combined along the dimension.
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        match self.additivity(dimension):
            case Additivity.EXTENSIVE:
                return AggregationMethod.SUM
            case Additivity.INTENSIVE:
                match self.level:
                    case MeasurementLevel.NOMINAL:
                        return AggregationMethod.WEIGHTED_MODE
                    case MeasurementLevel.ORDINAL:
                        return AggregationMethod.WEIGHTED_MEDIAN
                    case MeasurementLevel.CYCLIC:
                        return AggregationMethod.WEIGHTED_CIRCULAR_MEAN
                    case MeasurementLevel.INTERVAL | MeasurementLevel.RATIO:
                        return AggregationMethod.WEIGHTED_MEAN
            case Additivity.MAXIMAL:
                return AggregationMethod.MAXIMUM
            case Additivity.MINIMAL:
                return AggregationMethod.MINIMUM
            case Additivity.FIRST:
                return AggregationMethod.FIRST
            case Additivity.LAST:
                return AggregationMethod.LAST
            case Additivity.NON_ADDITIVE:
                return AggregationMethod.RECOMPUTE

    def disaggregation_method(self, dimension: Dimension) -> DisaggregationMethod:
        """
        Way to derive the values of the parts when a unit is split along a dimension.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which the unit is split.

        Returns
        -------
        DisaggregationMethod
            Method that gives the values of the parts.

        Raises
        ------
        DimensionNotCombinedError
            If the variable is not split along the dimension.
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        match self.additivity(dimension):
            case Additivity.EXTENSIVE:
                return DisaggregationMethod.PROPORTIONAL
            case Additivity.INTENSIVE:
                return DisaggregationMethod.REPLICATE
            case (
                Additivity.MAXIMAL
                | Additivity.MINIMAL
                | Additivity.FIRST
                | Additivity.LAST
                | Additivity.NON_ADDITIVE
            ):
                return DisaggregationMethod.RECOMPUTE

    @property
    def permitted_operations(self) -> frozenset[Operation]:
        """
        Operations whose results are meaningful for this variable.
        """
        return frozenset(
            operation for operation in Operation if self.permits(operation)
        )

    def permits(self, operation: Operation) -> bool:
        """
        Whether the result of an operation is meaningful for this variable.

        Parameters
        ----------
        operation : Operation
            Operation to check.

        Returns
        -------
        bool
            True when the result is meaningful.
        """
        return self._explain_meaningless(operation) is None

    def warn_unless_permitted(self, operation: Operation) -> None:
        """
        Warn when the result of an operation is not meaningful for this variable.

        The check never stops the caller, so the operation can still run.

        Parameters
        ----------
        operation : Operation
            Operation about to be applied to the values of this variable.

        Warns
        -----
        MeaninglessOperationWarning
            If the result of the operation is not meaningful.
        """
        reason: str | None = self._explain_meaningless(operation)
        if reason is not None:
            warnings.warn(
                f"The {operation.value} of {self.name!r} is not meaningful: {reason}",
                MeaninglessOperationWarning,
                stacklevel=2,
            )

    def permits_aggregation(
        self,
        dimension: Dimension,
        method: AggregationMethod,
        weight: WeightingVariable | Weighting | None = None,
    ) -> bool:
        """
        Whether combining units along a dimension by a method gives their value.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which units are combined.
        method : AggregationMethod
            Method to check.
        weight : WeightingVariable | Weighting | None
            Weight the method uses, to check it against the declared one.
            None skips that check.

        Returns
        -------
        bool
            True when the method gives the value of the combined units: the
            variable's aggregation method, an accepted alternative such as
            the weighted mode for an ordinal variable, or recomputation; and,
            for a weighted method, the declared weight when one is passed.

        Raises
        ------
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        return self._explain_wrong_aggregation(dimension, method, weight) is None

    def warn_unless_aggregation_permitted(
        self,
        dimension: Dimension,
        method: AggregationMethod,
        weight: WeightingVariable | Weighting | None = None,
    ) -> None:
        """
        Warn when combining units along a dimension by a method does not give their value.

        The check never stops the caller, so the aggregation can still run.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which units are about to be combined.
        method : AggregationMethod
            Method about to be used.
        weight : WeightingVariable | Weighting | None
            Weight the method uses, to check it against the declared one.
            None skips that check.

        Warns
        -----
        MeaninglessOperationWarning
            If the method or its weight does not give the value of the
            combined units.

        Raises
        ------
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        reason: str | None = self._explain_wrong_aggregation(dimension, method, weight)
        if reason is not None:
            warnings.warn(
                f"The {method.value} of {self.name!r} over {dimension.name} is not meaningful: {reason}",
                MeaninglessOperationWarning,
                stacklevel=2,
            )

    def permits_disaggregation(
        self,
        dimension: Dimension,
        method: DisaggregationMethod,
        weight: WeightingVariable | Weighting | None = None,
    ) -> bool:
        """
        Whether splitting a unit along a dimension by a method gives the values of its parts.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which the unit is split.
        method : DisaggregationMethod
            Method to check.
        weight : WeightingVariable | Weighting | None
            Weight a proportional division uses, to check it against the
            declared one. None skips that check.

        Returns
        -------
        bool
            True when the method gives the values of the parts: the
            variable's disaggregation method, an interpolation of the same
            kind, or recomputation; and, for a proportional division, the
            declared weight when one is passed.

        Raises
        ------
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        return self._explain_wrong_disaggregation(dimension, method, weight) is None

    def warn_unless_disaggregation_permitted(
        self,
        dimension: Dimension,
        method: DisaggregationMethod,
        weight: WeightingVariable | Weighting | None = None,
    ) -> None:
        """
        Warn when splitting a unit along a dimension by a method does not give the values of its parts.

        The check never stops the caller, so the split can still run.

        Parameters
        ----------
        dimension : Dimension
            Dimension along which the unit is about to be split.
        method : DisaggregationMethod
            Method about to be used.
        weight : WeightingVariable | Weighting | None
            Weight a proportional division uses, to check it against the
            declared one. None skips that check.

        Warns
        -----
        MeaninglessOperationWarning
            If the method or its weight does not give the values of the
            parts.

        Raises
        ------
        ValueError
            If the dimension has the name of one of the variable's dimensions
            but a different definition.
        """
        reason: str | None = self._explain_wrong_disaggregation(
            dimension, method, weight
        )
        if reason is not None:
            warnings.warn(
                f"The {method.value} of {self.name!r} over {dimension.name} is not meaningful: {reason}",
                MeaninglessOperationWarning,
                stacklevel=2,
            )

    def _explain_meaningless(self, operation: Operation) -> str | None:
        match operation:
            case Operation.MODE:
                return None
            case Operation.SUM:
                if self.level is not MeasurementLevel.RATIO:
                    return f"it is {self.level.value} and has no true zero, so a total has no meaning."
                if Additivity.EXTENSIVE not in {
                    combination.additivity for combination in self.combinations.values()
                }:
                    return "it is not extensive along any dimension, so a total of its values describes nothing; aggregate it with its aggregation method instead."
                return None
            case Operation.ORDERING | Operation.MEDIAN:
                if not self.level.is_at_least(MeasurementLevel.ORDINAL):
                    return f"it is {self.level.value}, so its values have no order."
                return None
            case Operation.DIFFERENCE:
                if not self.level.is_quantitative:
                    return f"it is {self.level.value}, so the distances between its categories are undefined."
                return None
            case Operation.MEAN | Operation.STANDARD_DEVIATION:
                if not self.level.is_quantitative:
                    return f"it is {self.level.value}, so the distances between its categories are undefined."
                if self.is_cyclic:
                    return f"it is cyclic; use the circular {operation.value} instead."
                return None
            case Operation.CIRCULAR_MEAN | Operation.CIRCULAR_STANDARD_DEVIATION:
                if not self.is_cyclic:
                    return "it is not cyclic."
                return None
            case (
                Operation.RATIO
                | Operation.GEOMETRIC_MEAN
                | Operation.COEFFICIENT_OF_VARIATION
            ):
                if self.level is not MeasurementLevel.RATIO:
                    return f"it is {self.level.value} and has no true zero."
                if self.is_signed:
                    return "it can be negative, and the result is meaningful only for positive values."
                return None

    def _explain_wrong_aggregation(
        self,
        dimension: Dimension,
        method: AggregationMethod,
        weight: WeightingVariable | Weighting | None,
    ) -> str | None:
        if not self._is_combined(dimension):
            return f"it is not combined over {dimension.name}."
        expected: AggregationMethod = self.aggregation_method(dimension)
        accepted: set[AggregationMethod] = {expected, AggregationMethod.RECOMPUTE}
        if expected in (
            AggregationMethod.WEIGHTED_MEDIAN,
            AggregationMethod.WEIGHTED_CIRCULAR_MEAN,
        ):
            # For categories and directions the value of merged units is a
            # convention, and the majority is as common as the central value.
            accepted.add(AggregationMethod.WEIGHTED_MODE)
        if method not in accepted:
            reason: str = f"it is {self.additivity(dimension).value} over {dimension.name}, so combined units take the {expected.value}."
            if method in (
                AggregationMethod.MAXIMUM,
                AggregationMethod.MINIMUM,
                AggregationMethod.FIRST,
                AggregationMethod.LAST,
            ):
                reason += f" If the {method.value} is meant as a different variable, such as the hottest station or the latest reading, define that variable on its own."
            return reason
        if method in (
            AggregationMethod.WEIGHTED_MEAN,
            AggregationMethod.WEIGHTED_CIRCULAR_MEAN,
            AggregationMethod.WEIGHTED_MEDIAN,
            AggregationMethod.WEIGHTED_MODE,
        ):
            return self._explain_wrong_weight(dimension, weight, "averaged")
        return None

    def _explain_wrong_disaggregation(
        self,
        dimension: Dimension,
        method: DisaggregationMethod,
        weight: WeightingVariable | Weighting | None,
    ) -> str | None:
        if not self._is_combined(dimension):
            return f"it is not split over {dimension.name}."
        expected: DisaggregationMethod = self.disaggregation_method(dimension)
        accepted: set[DisaggregationMethod] = {expected, DisaggregationMethod.RECOMPUTE}
        match expected:
            case DisaggregationMethod.PROPORTIONAL:
                accepted.add(DisaggregationMethod.TOTAL_PRESERVING_INTERPOLATION)
            case DisaggregationMethod.REPLICATE if self.level.is_quantitative:
                accepted.add(DisaggregationMethod.INTERPOLATION)
            case _:
                pass
        if method not in accepted:
            return f"it is {self.additivity(dimension).value} over {dimension.name}, so the parts take the {expected.value}."
        if method is DisaggregationMethod.PROPORTIONAL:
            return self._explain_wrong_weight(dimension, weight, "divided")
        return None

    def _explain_wrong_weight(
        self,
        dimension: Dimension,
        weight: WeightingVariable | Weighting | None,
        verb: str,
    ) -> str | None:
        declared: WeightingVariable | Weighting | None = self.weight(dimension)
        if weight is None or weight == declared:
            return None
        return f"it is {verb} by {_describe_weight(declared)} over {dimension.name}, not by {_describe_weight(weight)}."


def _normalize(name: str) -> str:
    return " ".join(name.split()).casefold()


def _describe_weight(weight: WeightingVariable | Weighting | None) -> str:
    match weight:
        case None:
            return "nothing"
        case Weighting():
            return weight.value
        case _:
            return repr(weight.name)


def _require_same_definition(
    defined: Dimension, given: Dimension, variable_name: str
) -> None:
    if _normalize(defined.name) == _normalize(given.name) and defined != given:
        raise ValueError(
            f"dimension {given.name!r} is given as {given} but defined for {variable_name!r} as {defined}."
        )
