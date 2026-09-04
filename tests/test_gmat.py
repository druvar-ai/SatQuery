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
    assert "GMAT Sat.SMA = 7000.0;" in script
    assert "GMAT DefaultProp_ForceModel.CentralBody = Earth;" in script
    assert "GMAT DefaultProp_ForceModel.PointMasses = {Earth};" in script
    assert "Propagate DefaultProp(Sat) {Sat.ElapsedSecs = 3600.0};" in script

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
        with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.run_script', return_value=(True, "stdout", "stderr", "cmd")):
            with patch('satquery.backend.simulation.gmat.gmat_parser.GMATParser.parse_report', return_value=(np.array([1, 2, 3]), np.array([4, 5, 6]))):
                prop = GMATPropagator(temp_dir="data/mock_temp")
                # Also mock write
                with patch("builtins.open", mock_open()):
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove", return_value=None):
                            pos, vel, alt = prop.propagate(sample_elements, target_time, body)
                            assert len(pos) == 3
                            assert len(vel) == 3
                            assert isinstance(alt, float)

def test_gmat_parser_batch():
    mock_report_content = "% Header\n% YYYY-MM-DD\n01 Jan 2026 01:00:00.000 -6856.8 200.6 1427.9 1.5 1.0 7.3\n01 Jan 2026 01:01:00.000 -6800.0 250.0 1500.0 1.6 1.1 7.4\n"
    with patch("builtins.open", mock_open(read_data=mock_report_content)):
        with patch("os.path.exists", return_value=True):
            res = GMATParser.parse_report_batch("dummy.txt")
            assert res is not None
            times, pos, vel = res
            assert len(times) == 2
            assert len(pos) == 2
            assert len(vel) == 2
            assert pos[0][0] == -6856.8
            assert pos[1][0] == -6800.0

def test_gmat_propagator_trajectory(sample_elements):
    body = get_body("earth")
    start_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 1, 1, 0, 2, 0, tzinfo=timezone.utc)
    
    # Mock parse_report_batch to return 3 points at 0, 60, 120 seconds
    t0 = start_time
    t1 = datetime(2026, 1, 1, 0, 1, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 0, 2, 0, tzinfo=timezone.utc)
    mock_times = [t0, t1, t2]
    mock_pos = np.array([[1000, 0, 0], [1100, 0, 0], [1200, 0, 0]])
    mock_vel = np.array([[10, 0, 0], [11, 0, 0], [12, 0, 0]])
    
    with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.is_available', return_value=True):
        with patch('satquery.backend.simulation.gmat.gmat_runner.GMATRunner.run_script', return_value=(True, "stdout", "stderr", "cmd")):
            with patch('satquery.backend.simulation.gmat.gmat_parser.GMATParser.parse_report_batch', return_value=(mock_times, mock_pos, mock_vel)):
                prop = GMATPropagator(temp_dir="data/mock_temp")
                with patch("builtins.open", mock_open()):
                    with patch("os.path.exists", return_value=True):
                        with patch("os.remove", return_value=None):
                            times, pos, vel, alt = prop.propagate_trajectory(
                                elements=sample_elements, 
                                start_time=start_time, 
                                end_time=end_time, 
                                timestep_seconds=60, 
                                body=body
                            )
                            assert len(times) == 3
                            assert len(pos) == 3
                            assert len(vel) == 3
                            assert len(alt) == 3
                            assert times[0] == start_time
                            assert times[2] == end_time
