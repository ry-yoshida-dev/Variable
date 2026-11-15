import pytest

from variable import MeasurementLevel


@pytest.mark.parametrize(
    ("level", "is_quantitative"),
    [
        (MeasurementLevel.NOMINAL, False),
        (MeasurementLevel.ORDINAL, False),
        (MeasurementLevel.INTERVAL, True),
        (MeasurementLevel.RATIO, True),
        (MeasurementLevel.CYCLIC, True),
    ],
)
def test_is_quantitative(level: MeasurementLevel, is_quantitative: bool) -> None:
    assert level.is_quantitative is is_quantitative


def test_is_at_least() -> None:
    assert MeasurementLevel.RATIO.is_at_least(MeasurementLevel.INTERVAL)
    assert MeasurementLevel.ORDINAL.is_at_least(MeasurementLevel.ORDINAL)
    assert not MeasurementLevel.NOMINAL.is_at_least(MeasurementLevel.ORDINAL)


def test_cyclic_branches_off_after_nominal() -> None:
    assert MeasurementLevel.CYCLIC.is_at_least(MeasurementLevel.NOMINAL)
    assert not MeasurementLevel.CYCLIC.is_at_least(MeasurementLevel.ORDINAL)
    assert not MeasurementLevel.RATIO.is_at_least(MeasurementLevel.CYCLIC)
