import pytest
import os
import numpy as np
from datetime import datetime, timezone
from unittest.mock import patch, mock_open

from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.celestial.body import get_body
from satquery.backend.orbit.propagator import get_propagator, AnalyticalPropagator
from satquery.backend.simulation.gmat.gmat_runner import GMATRunner
from satquery.backend.simulation.gmat.gmat_script_generator import GMATScriptGenerator
from satquery.backend.simulation.gmat.gmat_parser import GMATParser
from satquery.backend.simulation.gmat.gmat_propagator import GMATPropagator

@pytest.fixture
def sample_elements():
    return OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=98.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )

def test_gmat_runner_availability():
    with patch('os.path.exists', return_value=True):
        assert GMATRunner.is_available() is True
        
    with patch('os.path.exists', return_value=False):
        # Even if environment variable is set, it checks exists
        assert GMATRunner.is_available() is False

def test_gmat_script_generator(sample_elements):
    body = get_body("earth")
    target_time = datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    
    script = GMATScriptGenerator.generate_script(
        sample_elements, target_time, body, "data/test_report.txt"
    )
    
    assert "Create Spacecraft Sat;" in script
    assert "GMAT Sat.Epoch = '01 Jan 2026 00:00:00.000';" in script
    assert "GMAT Sat.SMA = 7000.0;" in script
    assert "GMAT DefaultProp_ForceModel.CentralBody = Earth;" in script
    assert "GMAT DefaultProp_ForceModel.PointMasses = {Earth};" in script
    assert "GMAT ReportFile1.Filename = 'data/test_report.txt';" in script
    assert "Propagate DefaultProp(Sat) {Sat.UTCGregorian = '01 Jan 2026 01:00:00.000'};" in script

def test_gmat_parser():
    mock_report_content = "% Header\n% YYYY-MM-DD\n01 Jan 2026 01:00:00.000 -6856.860903293499 200.6895189863977 1427.9801269956658 1.552982855583943 1.0266771480472823 7.305187493879407\n"
    with patch("builtins.open", mock_open(read_data=mock_report_content)):
        with patch("os.path.exists", return_value=True):
            res = GMATParser.parse_report("dummy.txt")
            assert res is not None
            pos, vel = res
            assert len(pos) == 3
            assert len(vel) == 3
            assert pos[0] == -6856.860903293499
            assert vel[2] == 7.305187493879407

def test_gmat_parser_empty():
    with patch("builtins.open", mock_open(read_data="")):
        with patch("os.path.exists", return_value=True):
            res = GMATParser.parse_report("dummy.txt")
            assert res is None

def test_propagator_factory_gmat_available():
    with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.is_available', return_value=True):
        prop = get_propagator("gmat")
        assert isinstance(prop, GMATPropagator)

def test_propagator_factory_gmat_fallback():
    with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.is_available', return_value=False):
        prop = get_propagator("gmat")
        assert isinstance(prop, AnalyticalPropagator)

def test_gmat_propagator_logic(sample_elements):
    body = get_body("earth")
    target_time = datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    
    with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.is_available', return_value=True):
        with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.run_script', return_value=True):
            with patch('satquery.backend.simulation.gmat.gmat_parser.GMATParser.parse_report', return_value=(np.array([1, 2, 3]), np.array([4, 5, 6]))):
                prop = GMATPropagator(temp_dir="data/mock_temp")
                # Also mock write
                with patch("builtins.open", mock_open()):
                    pos, vel, alt = prop.propagate(sample_elements, target_time, body)
                    assert len(pos) == 3
                    assert len(vel) == 3
                    assert isinstance(alt, float)
