import numpy as np
import pytest

from core.Lotucosm.entity import EntityBase


def test_set_radius_validates_without_touching_size():
    entity = EntityBase("e1", size=12.0)
    entity.set_radius(18.0)
    assert entity.size == 12.0
    assert entity.radius == 18.0
    with pytest.raises(ValueError):
        entity.set_radius(float("nan"))
    assert entity.radius == 18.0
