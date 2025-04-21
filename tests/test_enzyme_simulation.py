
import pytest # type: ignore
import tempfile
import json
import os
from bioopti.simulation import simulate_reaction_rate, simulate_from_local_data
from bioopti.enzyme_kinetics import load_local_enzyme_data, get_enzyme_kinetics

# Holds test data with 2 enzymes.
@pytest.fixture 
def mock_enzyme_data():
    return {
        "lactate dehydrogenase (Homo sapiens)": {
            "vmax": 100.0,
            "km": 0.5,
            "optimal_pH": 7.0,
            "optimal_temp": 37.0
        },
        "hexokinase (Saccharomyces cerevisiae)": {
            "vmax": 80.0,
            "km": 0.3,
            "optimal_pH": 7.5,
            "optimal_temp": 30.0
        }
    }

# Creates a temporary JSON file with mock data
@pytest.fixture
def temp_json_file(mock_enzyme_data):
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json") as f:
        json.dump(mock_enzyme_data, f)
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

# Checks the loader returns exactly what you wrote into the file
def test_load_local_enzyme_data(temp_json_file, mock_enzyme_data): 
    data = load_local_enzyme_data(temp_json_file)
    assert data == mock_enzyme_data

# Confirms correct lookup works
def test_get_enzyme_kinetics_exact_match(temp_json_file):
    params = get_enzyme_kinetics("lactate dehydrogenase", "Homo sapiens", filepath=temp_json_file)
    assert "vmax" in params and "km" in params

# Validates ValueError when no match is found
def test_get_enzyme_kinetics_no_match(temp_json_file):
    with pytest.raises(ValueError):
        get_enzyme_kinetics("random enzyme", "Unknown", filepath=temp_json_file)

# Verifies output is a float
def test_simulate_reaction_rate_basic():
    rate = simulate_reaction_rate(
        substrate_conc=1.0, vmax=100, km=0.5, ph=7.0, temp=37.0
    )
    assert isinstance(rate, float)

# Tests the inhibition penalty (check that the rate is lower with inhibitor)
def test_simulate_reaction_rate_with_inhibitor():
    rate = simulate_reaction_rate(
        substrate_conc=1.0, vmax=100, km=0.5, ph=7.0, temp=37.0,
        inhibitor_conc=0.5, ki=0.1
    )
    assert isinstance(rate, float)
    assert rate < 100

# Mocks get_enzyme_kinetics to test this higher-level wrapper in isolation
def test_simulate_from_local_data(temp_json_file, monkeypatch):
    monkeypatch.setattr("bioopti.enzyme_kinetics.get_enzyme_kinetics", lambda enzyme_name, organism=None, filepath=None: {
        "vmax": 90.0, "km": 0.4, "optimal_pH": 7.0, "optimal_temp": 37.0
    })
    v, params = simulate_from_local_data("lactate dehydrogenase", "Homo sapiens")
    assert isinstance(v, float)
    assert "vmax" in params
