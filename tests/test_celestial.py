import pytest
from satquery.backend.celestial.body import get_body, Earth, Moon, Mars

def test_get_earth():
    body = get_body("earth")
    assert isinstance(body, Earth)
    assert body.radius_km == 6378.137

def test_get_moon():
    body = get_body("moon")
    assert isinstance(body, Moon)
    assert body.type == "moon"

def test_get_mars():
    body = get_body("mars")
    assert isinstance(body, Mars)
    assert body.mu_km3_s2 > 0

def test_invalid_body():
    with pytest.raises(ValueError):
        get_body("jupiter")
