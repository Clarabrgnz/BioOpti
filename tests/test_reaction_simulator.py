import bioopti  # Import the bioopti module
import pytest  # type: ignore #Testing framework
import tempfile # To create temporary files (for simulating real JSON files).
import json  # To write and read JSON data
import os # To handle file paths and remove temporary files
from scipy.optimize import differential_evolution #For optimization functions
import sys # To add the src directory to the path for importing bioopti
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))) #Adds the src directory to the Python path so that the bioopti module can be imported


from bioopti.reaction_simulator import ( # Import the functions to be tested
    load_local_enzyme_data,
    normalize_keys,
    get_enzyme_kinetics,
    simulate_reaction_rate,
    simulate_from_local_data,
    optimize_reaction
)

# --------------------- Fixtures ---------------------
# Fixture that returns fake enzyme data (dictionary format) to use in tests (It simulates what a real enzyme_data.json would contain)
@pytest.fixture 
def mock_enzyme_data():
    """Mock enzyme kinetics data for testing."""
    return {
        "lactate dehydrogenase (Homo sapiens)": {
            "vmax": 100.0,
            "km": 0.5,
            "optimal_pH": 7.0,
            "optimal_temp": 37.0,
            "ph_sigma": 1.0,
            "temp_sigma": 5.0
        },
        "hexokinase (Saccharomyces cerevisiae)": {
            "vmax": 80.0,
            "km": 0.3,
            "optimal_pH": 7.5,
            "optimal_temp": 30.0,
            "ph_sigma": 1.0,
            "temp_sigma": 5.0
        }
    }

# Temporary .json file containing the mock enzyme data.
@pytest.fixture
def temp_json_file(mock_enzyme_data):
    """Create a temporary JSON file with mock enzyme data."""
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as f:
        json.dump(mock_enzyme_data, f)
        temp_path = f.name
    yield temp_path
    os.remove(temp_path)

# --------------------- Tests ---------------------

# --- Testing load_local_enzyme_data ---
# Loads the temporary file
# Checks that the loaded data exactly matches the mock data
def test_load_local_enzyme_data(temp_json_file, mock_enzyme_data):
    data = load_local_enzyme_data(temp_json_file)
    assert data == mock_enzyme_data

# --- Testing normalize_keys ---
# Creates a fake input dictionary mixing old names (km_mM) and already normalized names (optimal_pH)
# Calls normalize_keys function to convert the old names to the new ones
# Asserts that keys are correctly normalized (and extra keys are preserved)
def test_normalize_keys():
    input_data = {
        "km_mM": 0.5,
        "vmax_umol_per_min": 100.0,
        "optimal_pH": 7.0,
        "optimal_temp_C": 37.0,
        "ph_sigma": 1.0,
        "temp_sigma_C": 5.0,
        "extra_param": 42
    }
    normalized = normalize_keys(input_data)
    assert normalized["km"] == 0.5
    assert normalized["vmax"] == 100.0
    assert normalized["optimal_pH"] == 7.0
    assert normalized["optimal_temp"] == 37.0
    assert normalized["ph_sigma"] == 1.0
    assert normalized["temp_sigma"] == 5.0
    assert normalized["extra_param"] == 42  # extra keys should be preserved

# --- Testing get_enzyme_kinetics ---
# Fetches enzyme parameters by name + organism
# Asserts that the output contains important fields (vmax, km, etc)
def test_get_enzyme_kinetics_exact_match(temp_json_file):
    params = get_enzyme_kinetics("lactate dehydrogenase", "Homo sapiens", filepath=temp_json_file)
    assert isinstance(params, dict)
    assert "vmax" in params
    assert "km" in params

# Tries fetching an enzyme that doesn't exist
# Checks that the function correctly raises a ValueError
def test_get_enzyme_kinetics_no_match(temp_json_file):
    with pytest.raises(ValueError):
        get_enzyme_kinetics("nonexistent enzyme", "Unknown organism", filepath=temp_json_file)

# --- Testing simulate_reaction_rate ---

# Simulates a simple reaction (no inhibitor)
# Checks that the rate is a positive float
def test_simulate_reaction_rate_basic():
    rate = simulate_reaction_rate(
        substrate_conc=1.0,
        vmax=100.0,
        km=0.5,
        ph=7.0,
        temp=37.0
    )
    assert isinstance(rate, float)
    assert rate > 0

# Simulates reaction with and without inhibitor.
# Asserts that inhibitors slow down the reaction (rate decreases).
def test_simulate_reaction_rate_with_inhibitor():
    rate_without_inhibitor = simulate_reaction_rate(
        substrate_conc=1.0,
        vmax=100.0,
        km=0.5,
        ph=7.0,
        temp=37.0
    )
    rate_with_inhibitor = simulate_reaction_rate(
        substrate_conc=1.0,
        vmax=100.0,
        km=0.5,
        ph=7.0,
        temp=37.0,
        inhibitor_conc=0.5,
        ki=0.1
    )
    assert isinstance(rate_with_inhibitor, float)
    assert rate_with_inhibitor < rate_without_inhibitor

# --- Testing simulate_from_local_data ---

# Uses monkeypatch.setattr(...) to replace get_enzyme_kinetics temporarily with a fake version that returns fixed params, and then calls simulate_from_local_data
# Checks that it returns: a float rate and a dict of params with all necessary fields
def test_simulate_from_local_data(monkeypatch):
    """Test high-level simulation with mocked get_enzyme_kinetics."""
    monkeypatch.setattr(
        "bioopti.reaction_simulator.get_enzyme_kinetics",
        lambda enzyme_name, organism=None, filepath=None: {
            "vmax": 90.0,
            "km": 0.4,
            "optimal_pH": 7.0,
            "optimal_temp": 37.0,
            "ph_sigma": 1.0,
            "temp_sigma": 5.0
        }
    )
    v, params = simulate_from_local_data("lactate dehydrogenase", "Homo sapiens")
    assert isinstance(v, float)
    assert isinstance(params, dict)
    assert "vmax" in params
    assert "km" in params
    assert "optimal_pH" in params
    assert "optimal_temp" in params

def main():
    enzyme = get_enzyme_kinetics("lactate dehydrogenase", "Homo sapiens")  # Replace with your enzyme
    result = optimize_reaction(enzyme)

    print("Optimal Conditions:")
    print(f"Substrate Concentration: {result['best_conditions'][0]:.2f} mM")
    print(f"pH: {result['best_conditions'][1]:.2f}")
    print(f"Temperature: {result['best_conditions'][2]:.2f} °C")
    print(f"Maximum Reaction Rate: {result['max_rate']:.2f} µmol/min")

if __name__ == "__main__":
    main()

# --- Testing optimize_reaction ---

# Defines a enzyme system with a clear optimum: Vmax high, Km low to favor high rates at moderate substrate and optimal pH and temperature set to physiological values.
# Asserts that:
#   Out contains the keys "best_conditions" and "max_rate".
#   best_conditions is an array of three values.
#   Each of those three values lies within the allowed search bounds (substrate concentration between 0.01–10.0, pH between 4.0–9.0, temperature between 20–60 °C).
#   max_rate is non‑negative.
def test_optimize_reaction_smoke():
    enzyme = { # Defines the enzyme system
        "vmax": 100.0,
        "km": 0.1,
        "optimal_pH": 7.0,
        "optimal_temp": 37.0,
        "ph_sigma": 0.5, # Narrow pH tolerance
        "temp_sigma": 5.0 # Moderate temperature tolerance
    }
    # Runs the optimization function
    out = bioopti.reaction_simulator.optimize_reaction(enzyme)
    # Checks that the output contains the expected keys
    assert "best_conditions" in out and "max_rate" in out
    bc = out["best_conditions"]
    # Ensures the three expected values were obtained: [substrate_conc, pH, temp]
    assert len(bc) == 3
    # Verifies each optimized parameter stays within the predefined bounds
    assert 4.0 <= bc[1] <= 9.0
    assert 20.0 <= bc[2] <= 60.0
    assert out["max_rate"] >= 0.0