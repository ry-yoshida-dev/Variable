import pytest

from variable import Dimension


def test_predefined_dimensions() -> None:
    assert Dimension.SPACE.is_sized
    assert not Dimension.SPACE.is_ordered
    assert Dimension.TIME.is_sized
    assert Dimension.TIME.is_ordered


def test_equal_by_value() -> None:
    assert Dimension(name="time", is_sized=True, is_ordered=True) == Dimension.TIME


@pytest.mark.parametrize("name", ["", "   "])
def test_rejects_blank_name(name: str) -> None:
    with pytest.raises(ValueError, match="blank"):
        _ = Dimension(name=name, is_sized=False, is_ordered=False)
