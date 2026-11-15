import pytest

from variable import Additivity, Combination, Weighting


@pytest.mark.parametrize(
    ("combination", "additivity", "weight"),
    [
        (Combination.extensive(Weighting.SIZE), Additivity.EXTENSIVE, Weighting.SIZE),
        (Combination.intensive(Weighting.EQUAL), Additivity.INTENSIVE, Weighting.EQUAL),
        (Combination.maximal(), Additivity.MAXIMAL, None),
        (Combination.minimal(), Additivity.MINIMAL, None),
        (Combination.first(), Additivity.FIRST, None),
        (Combination.last(), Additivity.LAST, None),
        (Combination.non_additive(), Additivity.NON_ADDITIVE, None),
    ],
)
def test_class_methods(
    combination: Combination, additivity: Additivity, weight: Weighting | None
) -> None:
    assert combination.additivity is additivity
    assert combination.weight is weight


@pytest.mark.parametrize("additivity", [Additivity.EXTENSIVE, Additivity.INTENSIVE])
def test_requires_weight(additivity: Additivity) -> None:
    with pytest.raises(ValueError, match="requires a weight"):
        _ = Combination(additivity=additivity, weight=None)


@pytest.mark.parametrize(
    "additivity",
    [
        Additivity.MAXIMAL,
        Additivity.MINIMAL,
        Additivity.FIRST,
        Additivity.LAST,
        Additivity.NON_ADDITIVE,
    ],
)
def test_rejects_weight(additivity: Additivity) -> None:
    with pytest.raises(ValueError, match="takes no weight"):
        _ = Combination(additivity=additivity, weight=Weighting.SIZE)
