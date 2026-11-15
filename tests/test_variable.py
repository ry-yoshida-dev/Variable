import copy
import pickle
import warnings

import pytest

from variable import (
    Additivity,
    AggregationMethod,
    Combination,
    Dimension,
    DimensionNotCombinedError,
    DisaggregationMethod,
    MeaninglessOperationWarning,
    MeasurementLevel,
    Operation,
    Variable,
    Weighting,
)

SPACE: Dimension = Dimension.SPACE
TIME: Dimension = Dimension.TIME
AGE_GROUP: Dimension = Dimension(name="age group", is_sized=False, is_ordered=True)
STATION: Dimension = Dimension(name="station", is_sized=False, is_ordered=False)

AREA: Variable = Variable.ratio(
    "area",
    is_signed=False,
    combinations={SPACE: Combination.extensive(Weighting.SIZE)},
)
POPULATION: Variable = Variable.ratio(
    "population",
    is_signed=False,
    combinations={
        SPACE: Combination.extensive(Weighting.SIZE),
        TIME: Combination.intensive(Weighting.SIZE),
        AGE_GROUP: Combination.extensive(Weighting.EQUAL),
    },
)
PROFIT: Variable = Variable.ratio(
    "profit",
    is_signed=True,
    combinations={
        SPACE: Combination.extensive(Weighting.SIZE),
        TIME: Combination.extensive(Weighting.SIZE),
    },
)
PRECIPITATION: Variable = Variable.ratio(
    "precipitation",
    is_signed=False,
    combinations={
        SPACE: Combination.intensive(Weighting.SIZE),
        TIME: Combination.extensive(Weighting.SIZE),
    },
)
DENSITY: Variable = Variable.ratio(
    "density",
    is_signed=False,
    combinations={
        SPACE: Combination.intensive(Weighting.SIZE),
        TIME: Combination.intensive(Weighting.SIZE),
    },
)
INCOME: Variable = Variable.ratio(
    "income",
    is_signed=False,
    combinations={
        SPACE: Combination.intensive(POPULATION),
        AGE_GROUP: Combination.intensive(POPULATION),
    },
)
BALANCE: Variable = Variable.ratio(
    "balance",
    is_signed=True,
    combinations={
        SPACE: Combination.extensive(Weighting.SIZE),
        TIME: Combination.last(),
    },
)
TEMPERATURE: Variable = Variable.interval(
    "temperature",
    combinations={
        STATION: Combination.intensive(Weighting.EQUAL),
        TIME: Combination.intensive(Weighting.SIZE),
    },
)
MAXIMUM_TEMPERATURE: Variable = Variable.interval(
    "maximum_temperature",
    combinations={
        STATION: Combination.intensive(Weighting.EQUAL),
        TIME: Combination.maximal(),
    },
)
MINIMUM_TEMPERATURE: Variable = Variable.interval(
    "minimum_temperature",
    combinations={STATION: Combination.minimal(), TIME: Combination.minimal()},
)
SPECIES_RICHNESS: Variable = Variable.ratio(
    "species_richness",
    is_signed=False,
    combinations={SPACE: Combination.non_additive(), TIME: Combination.non_additive()},
)
WIND_DIRECTION: Variable = Variable.cyclic(
    "wind_direction",
    period=360.0,
    combinations={
        STATION: Combination.intensive(Weighting.EQUAL),
        TIME: Combination.intensive(Weighting.SIZE),
    },
)
MEDIAN_DIRECTION: Variable = Variable.cyclic(
    "median_direction",
    period=360.0,
    combinations={STATION: Combination.non_additive()},
)
LAND_USE: Variable = Variable.nominal(
    "land_use", combinations={SPACE: Combination.intensive(Weighting.SIZE)}
)
MUNICIPALITY_CODE: Variable = Variable.nominal(
    "municipality_code", combinations={SPACE: Combination.non_additive()}
)
HAZARD_RANK: Variable = Variable.ordinal(
    "hazard_rank",
    combinations={SPACE: Combination.maximal(), TIME: Combination.maximal()},
)
SOIL_CLASS: Variable = Variable.ordinal(
    "soil_class", combinations={SPACE: Combination.intensive(AREA)}
)

QUANTITATIVE_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.MODE,
        Operation.ORDERING,
        Operation.MEDIAN,
        Operation.DIFFERENCE,
        Operation.MEAN,
        Operation.STANDARD_DEVIATION,
    }
)
RATIO_OPERATIONS: frozenset[Operation] = QUANTITATIVE_OPERATIONS | {
    Operation.RATIO,
    Operation.GEOMETRIC_MEAN,
    Operation.COEFFICIENT_OF_VARIATION,
}
CYCLIC_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.MODE,
        Operation.DIFFERENCE,
        Operation.CIRCULAR_MEAN,
        Operation.CIRCULAR_STANDARD_DEVIATION,
    }
)


def ratio(combination: Combination, dimension: Dimension = SPACE) -> Variable:
    return Variable.ratio(
        "value", is_signed=False, combinations={dimension: combination}
    )


class TestConstruction:
    def test_constructor_matches_class_method(self) -> None:
        direct: Variable = Variable(
            name="area",
            level=MeasurementLevel.RATIO,
            combinations={SPACE: Combination.extensive(Weighting.SIZE)},
            period=None,
            is_signed=False,
        )
        assert direct == AREA
        assert hash(direct) == hash(AREA)

    def test_combinations_are_copied(self) -> None:
        combinations: dict[Dimension, Combination] = {SPACE: Combination.non_additive()}
        variable: Variable = Variable.ratio(
            "value", is_signed=False, combinations=combinations
        )
        combinations[TIME] = Combination.non_additive()
        assert variable.dimensions == frozenset({SPACE})

    def test_custom_dimension_matches_by_value(self) -> None:
        age_group: Dimension = Dimension(
            name="age group", is_sized=False, is_ordered=True
        )
        assert POPULATION.additivity(age_group) is Additivity.EXTENSIVE

    def test_accessors(self) -> None:
        assert POPULATION.dimensions == frozenset({SPACE, TIME, AGE_GROUP})
        assert POPULATION.additivity(TIME) is Additivity.INTENSIVE
        assert INCOME.weight(SPACE) is POPULATION
        assert HAZARD_RANK.weight(SPACE) is None
        assert WIND_DIRECTION.is_cyclic
        assert not TEMPERATURE.is_cyclic

    def test_rejects_missing_dimension(self) -> None:
        with pytest.raises(
            DimensionNotCombinedError, match="not combined or split over time"
        ):
            _ = LAND_USE.additivity(TIME)
        with pytest.raises(
            DimensionNotCombinedError, match="not combined or split over time"
        ):
            _ = LAND_USE.weight(TIME)
        with pytest.raises(
            DimensionNotCombinedError, match="not combined or split over time"
        ):
            _ = LAND_USE.aggregation_method(TIME)
        with pytest.raises(
            DimensionNotCombinedError, match="not combined or split over time"
        ):
            _ = LAND_USE.disaggregation_method(TIME)

    @pytest.mark.parametrize("name", ["", "   "])
    def test_rejects_blank_name(self, name: str) -> None:
        with pytest.raises(ValueError, match="blank"):
            _ = Variable.nominal(name, combinations={SPACE: Combination.non_additive()})

    def test_rejects_no_dimension(self) -> None:
        with pytest.raises(ValueError, match="at least one dimension"):
            _ = Variable.nominal("land_use", combinations={})

    @pytest.mark.parametrize(
        ("level", "period"),
        [
            (MeasurementLevel.NOMINAL, None),
            (MeasurementLevel.ORDINAL, None),
            (MeasurementLevel.INTERVAL, None),
            (MeasurementLevel.CYCLIC, 360.0),
        ],
    )
    def test_only_ratio_can_be_extensive(
        self, level: MeasurementLevel, period: float | None
    ) -> None:
        with pytest.raises(ValueError, match="no true zero"):
            _ = Variable(
                name="value",
                level=level,
                combinations={SPACE: Combination.extensive(Weighting.SIZE)},
                period=period,
                is_signed=None,
            )

    @pytest.mark.parametrize(
        ("level", "period"),
        [(MeasurementLevel.NOMINAL, None), (MeasurementLevel.CYCLIC, 360.0)],
    )
    @pytest.mark.parametrize(
        "combination", [Combination.maximal(), Combination.minimal()]
    )
    def test_unordered_levels_reject_maximal_and_minimal(
        self, level: MeasurementLevel, period: float | None, combination: Combination
    ) -> None:
        with pytest.raises(ValueError, match="has no order"):
            _ = Variable(
                name="value",
                level=level,
                combinations={SPACE: combination},
                period=period,
                is_signed=None,
            )

    @pytest.mark.parametrize("combination", [Combination.first(), Combination.last()])
    def test_first_and_last_need_ordered_dimension(
        self, combination: Combination
    ) -> None:
        with pytest.raises(ValueError, match="space is not ordered"):
            _ = ratio(combination, SPACE)
        assert ratio(combination, TIME).dimensions == frozenset({TIME})

    @pytest.mark.parametrize(
        "level",
        [
            MeasurementLevel.NOMINAL,
            MeasurementLevel.ORDINAL,
            MeasurementLevel.INTERVAL,
            MeasurementLevel.RATIO,
        ],
    )
    def test_only_cyclic_takes_period(self, level: MeasurementLevel) -> None:
        with pytest.raises(ValueError, match="takes no period"):
            _ = Variable(
                name="angle",
                level=level,
                combinations={SPACE: Combination.non_additive()},
                period=360.0,
                is_signed=False if level is MeasurementLevel.RATIO else None,
            )

    def test_cyclic_requires_period(self) -> None:
        with pytest.raises(ValueError, match="period is required"):
            _ = Variable(
                name="hour",
                level=MeasurementLevel.CYCLIC,
                combinations={SPACE: Combination.non_additive()},
                period=None,
                is_signed=None,
            )

    @pytest.mark.parametrize("period", [0.0, -1.0, float("inf"), float("nan")])
    def test_rejects_invalid_period(self, period: float) -> None:
        with pytest.raises(ValueError, match="positive and finite"):
            _ = Variable.cyclic(
                "hour",
                period=period,
                combinations={SPACE: Combination.non_additive()},
            )

    def test_ratio_requires_sign(self) -> None:
        with pytest.raises(ValueError, match="whether it can be negative"):
            _ = Variable(
                name="sales",
                level=MeasurementLevel.RATIO,
                combinations={SPACE: Combination.non_additive()},
                period=None,
                is_signed=None,
            )

    def test_only_ratio_takes_sign(self) -> None:
        with pytest.raises(ValueError, match="takes no sign"):
            _ = Variable(
                name="temperature",
                level=MeasurementLevel.INTERVAL,
                combinations={SPACE: Combination.non_additive()},
                period=None,
                is_signed=True,
            )

    def test_size_needs_sized_dimension(self) -> None:
        with pytest.raises(ValueError, match="have no size"):
            _ = ratio(Combination.intensive(Weighting.SIZE), STATION)
        equal: Variable = ratio(Combination.intensive(Weighting.EQUAL), STATION)
        assert equal.dimensions == frozenset({STATION})

    @pytest.mark.parametrize("weight", [DENSITY, PRECIPITATION])
    def test_rejects_weight_not_extensive_along_dimension(
        self, weight: Variable
    ) -> None:
        with pytest.raises(ValueError, match="must be extensive over space"):
            _ = ratio(Combination.intensive(weight))

    def test_rejects_weight_not_combined_along_dimension(self) -> None:
        with pytest.raises(ValueError, match="must be extensive over time"):
            _ = ratio(Combination.intensive(AREA), TIME)

    def test_rejects_signed_weight(self) -> None:
        with pytest.raises(ValueError, match="must not be negative"):
            _ = ratio(Combination.intensive(PROFIT))

    def test_rejects_self_weight(self) -> None:
        with pytest.raises(ValueError, match="by itself"):
            _ = Variable.ratio(
                "population",
                is_signed=False,
                combinations={SPACE: Combination.extensive(POPULATION)},
            )

    def test_accepts_ancillary_weight_for_split(self) -> None:
        floor_area: Variable = Variable.ratio(
            "residential_floor_area",
            is_signed=False,
            combinations={SPACE: Combination.extensive(Weighting.SIZE)},
        )
        residents: Variable = ratio(Combination.extensive(floor_area))
        assert residents.weight(SPACE) is floor_area


class TestPermittedOperations:
    @pytest.mark.parametrize(
        ("variable", "expected"),
        [
            (LAND_USE, frozenset({Operation.MODE})),
            (MUNICIPALITY_CODE, frozenset({Operation.MODE})),
            (
                HAZARD_RANK,
                frozenset({Operation.MODE, Operation.ORDERING, Operation.MEDIAN}),
            ),
            (TEMPERATURE, QUANTITATIVE_OPERATIONS),
            (MAXIMUM_TEMPERATURE, QUANTITATIVE_OPERATIONS),
            (SPECIES_RICHNESS, RATIO_OPERATIONS),
            (WIND_DIRECTION, CYCLIC_OPERATIONS),
            (MEDIAN_DIRECTION, CYCLIC_OPERATIONS),
            (DENSITY, RATIO_OPERATIONS),
            (POPULATION, RATIO_OPERATIONS | {Operation.SUM}),
            (PROFIT, QUANTITATIVE_OPERATIONS | {Operation.SUM}),
        ],
    )
    def test_permitted_operations(
        self, variable: Variable, expected: frozenset[Operation]
    ) -> None:
        assert variable.permitted_operations == expected

    def test_permits_matches_permitted_operations(self) -> None:
        for operation in Operation:
            assert DENSITY.permits(operation) == (
                operation in DENSITY.permitted_operations
            )


class TestWarnUnlessPermitted:
    def test_suggests_circular_mean(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="circular mean"):
            WIND_DIRECTION.warn_unless_permitted(Operation.MEAN)

    def test_explains_sign(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="can be negative"):
            PROFIT.warn_unless_permitted(Operation.RATIO)

    def test_names_variable(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="'land_use'"):
            LAND_USE.warn_unless_permitted(Operation.MEDIAN)

    def test_silent_for_permitted_operation(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            POPULATION.warn_unless_permitted(Operation.RATIO)

    def test_points_at_caller(self) -> None:
        with pytest.warns(MeaninglessOperationWarning) as records:
            TEMPERATURE.warn_unless_permitted(Operation.RATIO)
        assert records[0].filename == __file__


class TestAggregation:
    @pytest.mark.parametrize(
        ("variable", "dimension", "expected"),
        [
            (LAND_USE, SPACE, AggregationMethod.WEIGHTED_MODE),
            (MUNICIPALITY_CODE, SPACE, AggregationMethod.RECOMPUTE),
            (SOIL_CLASS, SPACE, AggregationMethod.WEIGHTED_MEDIAN),
            (HAZARD_RANK, SPACE, AggregationMethod.MAXIMUM),
            (TEMPERATURE, STATION, AggregationMethod.WEIGHTED_MEAN),
            (WIND_DIRECTION, TIME, AggregationMethod.WEIGHTED_CIRCULAR_MEAN),
            (MEDIAN_DIRECTION, STATION, AggregationMethod.RECOMPUTE),
            (POPULATION, SPACE, AggregationMethod.SUM),
            (POPULATION, TIME, AggregationMethod.WEIGHTED_MEAN),
            (POPULATION, AGE_GROUP, AggregationMethod.SUM),
            (INCOME, AGE_GROUP, AggregationMethod.WEIGHTED_MEAN),
            (PRECIPITATION, SPACE, AggregationMethod.WEIGHTED_MEAN),
            (PRECIPITATION, TIME, AggregationMethod.SUM),
            (MAXIMUM_TEMPERATURE, TIME, AggregationMethod.MAXIMUM),
            (MINIMUM_TEMPERATURE, TIME, AggregationMethod.MINIMUM),
            (BALANCE, TIME, AggregationMethod.LAST),
            (ratio(Combination.first(), TIME), TIME, AggregationMethod.FIRST),
            (SPECIES_RICHNESS, SPACE, AggregationMethod.RECOMPUTE),
        ],
    )
    def test_aggregation_method(
        self, variable: Variable, dimension: Dimension, expected: AggregationMethod
    ) -> None:
        assert variable.aggregation_method(dimension) is expected

    @pytest.mark.parametrize(
        ("variable", "dimension", "expected"),
        [
            (LAND_USE, SPACE, DisaggregationMethod.REPLICATE),
            (MUNICIPALITY_CODE, SPACE, DisaggregationMethod.RECOMPUTE),
            (HAZARD_RANK, SPACE, DisaggregationMethod.RECOMPUTE),
            (TEMPERATURE, TIME, DisaggregationMethod.REPLICATE),
            (POPULATION, SPACE, DisaggregationMethod.PROPORTIONAL),
            (POPULATION, TIME, DisaggregationMethod.REPLICATE),
            (PRECIPITATION, TIME, DisaggregationMethod.PROPORTIONAL),
            (MAXIMUM_TEMPERATURE, TIME, DisaggregationMethod.RECOMPUTE),
            (BALANCE, TIME, DisaggregationMethod.RECOMPUTE),
            (SPECIES_RICHNESS, SPACE, DisaggregationMethod.RECOMPUTE),
        ],
    )
    def test_disaggregation_method(
        self, variable: Variable, dimension: Dimension, expected: DisaggregationMethod
    ) -> None:
        assert variable.disaggregation_method(dimension) is expected


class TestAggregationCheck:
    @pytest.mark.parametrize(
        ("dimension", "method", "is_permitted"),
        [
            (SPACE, AggregationMethod.SUM, True),
            (SPACE, AggregationMethod.RECOMPUTE, True),
            (TIME, AggregationMethod.SUM, False),
            (TIME, AggregationMethod.WEIGHTED_MEAN, True),
            (STATION, AggregationMethod.SUM, False),
        ],
    )
    def test_permits_aggregation(
        self, dimension: Dimension, method: AggregationMethod, is_permitted: bool
    ) -> None:
        assert POPULATION.permits_aggregation(dimension, method) is is_permitted

    def test_warns_for_temporal_sum_of_stock(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="take the weighted mean"):
            POPULATION.warn_unless_aggregation_permitted(TIME, AggregationMethod.SUM)

    def test_warns_for_dimension_not_combined(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="not combined over time"):
            LAND_USE.warn_unless_aggregation_permitted(
                TIME, AggregationMethod.WEIGHTED_MODE
            )

    def test_aggregation_warning_points_at_caller(self) -> None:
        with pytest.warns(MeaninglessOperationWarning) as records:
            DENSITY.warn_unless_aggregation_permitted(SPACE, AggregationMethod.SUM)
        assert records[0].filename == __file__

    def test_silent_for_permitted_aggregation(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            HAZARD_RANK.warn_unless_aggregation_permitted(
                SPACE, AggregationMethod.MAXIMUM
            )

    @pytest.mark.parametrize(
        ("dimension", "method", "is_permitted"),
        [
            (SPACE, DisaggregationMethod.PROPORTIONAL, True),
            (SPACE, DisaggregationMethod.REPLICATE, False),
            (TIME, DisaggregationMethod.REPLICATE, True),
            (TIME, DisaggregationMethod.RECOMPUTE, True),
            (STATION, DisaggregationMethod.RECOMPUTE, False),
        ],
    )
    def test_permits_disaggregation(
        self, dimension: Dimension, method: DisaggregationMethod, is_permitted: bool
    ) -> None:
        assert POPULATION.permits_disaggregation(dimension, method) is is_permitted

    def test_warns_for_replicating_count(self) -> None:
        with pytest.warns(
            MeaninglessOperationWarning, match="take the proportional division"
        ):
            POPULATION.warn_unless_disaggregation_permitted(
                SPACE, DisaggregationMethod.REPLICATE
            )


class TestDimensionConflict:
    MISDEFINED_AGE_GROUP: Dimension = Dimension(
        name="age group", is_sized=False, is_ordered=False
    )

    def test_rejects_lookup_by_misdefined_dimension(self) -> None:
        with pytest.raises(ValueError, match="defined for 'population'"):
            _ = POPULATION.additivity(self.MISDEFINED_AGE_GROUP)
        with pytest.raises(ValueError, match="defined for 'population'"):
            _ = POPULATION.permits_aggregation(
                self.MISDEFINED_AGE_GROUP, AggregationMethod.SUM
            )

    def test_rejects_weight_with_misdefined_dimension(self) -> None:
        with pytest.raises(ValueError, match="defined for 'population'"):
            _ = ratio(Combination.intensive(POPULATION), self.MISDEFINED_AGE_GROUP)

    def test_rejects_same_name_twice(self) -> None:
        with pytest.raises(ValueError, match="same name"):
            _ = Variable.ratio(
                "value",
                is_signed=False,
                combinations={
                    AGE_GROUP: Combination.non_additive(),
                    self.MISDEFINED_AGE_GROUP: Combination.non_additive(),
                },
            )


class TestReviewFixes:
    def test_pickles_and_deep_copies(self) -> None:
        restored: object = pickle.loads(pickle.dumps(INCOME))  # pyright: ignore[reportAny]
        assert restored == INCOME
        assert copy.deepcopy(INCOME) == INCOME

    def test_rejects_bool_period(self) -> None:
        with pytest.raises(TypeError, match="not a bool"):
            _ = Variable.cyclic(
                "hour", period=True, combinations={SPACE: Combination.non_additive()}
            )

    def test_rejects_names_differing_in_case_and_spacing(self) -> None:
        with pytest.raises(ValueError, match="same name"):
            _ = Variable.ratio(
                "value",
                is_signed=False,
                combinations={
                    AGE_GROUP: Combination.non_additive(),
                    Dimension(
                        name=" Age  Group", is_sized=False, is_ordered=False
                    ): Combination.non_additive(),
                },
            )

    def test_sum_needs_extensive_ratio(self) -> None:
        with pytest.warns(MeaninglessOperationWarning, match="not extensive"):
            DENSITY.warn_unless_permitted(Operation.SUM)
        with pytest.warns(MeaninglessOperationWarning, match="no true zero"):
            TEMPERATURE.warn_unless_permitted(Operation.SUM)

    def test_checks_aggregation_weight(self) -> None:
        assert INCOME.permits_aggregation(
            SPACE, AggregationMethod.WEIGHTED_MEAN, POPULATION
        )
        assert INCOME.permits_aggregation(SPACE, AggregationMethod.WEIGHTED_MEAN)
        with pytest.warns(
            MeaninglessOperationWarning, match="averaged by 'population'.*not by size"
        ):
            INCOME.warn_unless_aggregation_permitted(
                SPACE, AggregationMethod.WEIGHTED_MEAN, Weighting.SIZE
            )

    def test_checks_disaggregation_weight(self) -> None:
        floor_area: Variable = Variable.ratio(
            "residential_floor_area",
            is_signed=False,
            combinations={SPACE: Combination.extensive(Weighting.SIZE)},
        )
        residents: Variable = Variable.ratio(
            "residents",
            is_signed=False,
            combinations={SPACE: Combination.extensive(floor_area)},
        )
        assert not residents.permits_disaggregation(
            SPACE, DisaggregationMethod.PROPORTIONAL, Weighting.SIZE
        )
        assert residents.permits_disaggregation(
            SPACE, DisaggregationMethod.PROPORTIONAL, floor_area
        )

    @pytest.mark.parametrize("variable", [SOIL_CLASS, WIND_DIRECTION])
    def test_accepts_majority_for_ordinal_and_cyclic(self, variable: Variable) -> None:
        dimension: Dimension = next(iter(variable.dimensions - {TIME}))
        assert variable.permits_aggregation(dimension, AggregationMethod.WEIGHTED_MODE)

    def test_rejects_majority_for_quantity(self) -> None:
        assert not DENSITY.permits_aggregation(SPACE, AggregationMethod.WEIGHTED_MODE)

    @pytest.mark.parametrize(
        ("variable", "method", "is_permitted"),
        [
            (POPULATION, DisaggregationMethod.TOTAL_PRESERVING_INTERPOLATION, True),
            (POPULATION, DisaggregationMethod.INTERPOLATION, False),
            (DENSITY, DisaggregationMethod.INTERPOLATION, True),
            (DENSITY, DisaggregationMethod.TOTAL_PRESERVING_INTERPOLATION, False),
            (LAND_USE, DisaggregationMethod.INTERPOLATION, False),
        ],
    )
    def test_interpolation(
        self, variable: Variable, method: DisaggregationMethod, is_permitted: bool
    ) -> None:
        assert variable.permits_disaggregation(SPACE, method) is is_permitted

    def test_suggests_separate_variable_only_for_order_methods(self) -> None:
        with pytest.warns(MeaninglessOperationWarning) as records:
            POPULATION.warn_unless_aggregation_permitted(TIME, AggregationMethod.SUM)
            TEMPERATURE.warn_unless_aggregation_permitted(
                STATION, AggregationMethod.MAXIMUM
            )
        assert "variable on its own" not in str(records[0].message)
        assert "variable on its own" in str(records[1].message)

    def test_rejects_weight_of_unknown_sign(self) -> None:
        class UnknownSignWeight:
            name: str = "unknown"
            is_signed: bool | None = None
            dimensions: frozenset[Dimension] = frozenset({SPACE})

            def additivity(self, dimension: Dimension) -> Additivity:
                assert dimension == SPACE
                return Additivity.EXTENSIVE

        with pytest.raises(ValueError, match="must not be negative"):
            _ = ratio(Combination.intensive(UnknownSignWeight()))
