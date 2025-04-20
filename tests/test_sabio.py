import pytest # type: ignore
from bioopti.sabio import get_kinetic_params_from_sabio

# --------------------------
# ✅ Test 1: Normal success case
# Simulates an API response that contains all parameters (some with multiple values).
# Checks if values are correctly averaged and parsed.
# --------------------------
def test_sabio_success(monkeypatch):
    class MockResponse:
        def raise_for_status(self): pass
        text = (
            "Km = 0.1\nKm = 0.3\n"
            "Vmax = 5.0\nVmax = 7.0\n"
            "pH-optimum = 7.4\n"
            "temperature-optimum = 37.0"
        )

    monkeypatch.setattr("requests.get", lambda *a, **kw: MockResponse())

    result = get_kinetic_params_from_sabio("fake enzyme", "Fake organism", interactive=False)

    assert result["km"] == pytest.approx(0.2)
    assert result["vmax"] == pytest.approx(6.0)
    assert result["optimal_pH"] == 7.4
    assert result["optimal_temp"] == 37.0

# --------------------------
# ⚠️ Test 2: Missing all values
# Simulates a valid API response that returns no kinetic data.
# The function should ask the user to input everything manually.
# --------------------------
def test_sabio_missing_values(monkeypatch):
    class MockResponse:
        def raise_for_status(self): pass
        text = ""

    monkeypatch.setattr("requests.get", lambda *a, **kw: MockResponse())

    # Simulate user inputs for all 4 missing values
    inputs = iter(["0.2", "10.0", "6.8", "42.0"])
    monkeypatch.setattr("builtins.input", lambda msg: next(inputs))

    result = get_kinetic_params_from_sabio("any", "thing", interactive=True)

    assert result["km"] == 0.2
    assert result["vmax"] == 10.0
    assert result["optimal_pH"] == 6.8
    assert result["optimal_temp"] == 42.0

# --------------------------
# ❌ Test 3: API error with fallback
# Simulates an API failure (e.g., network or 500 error).
# Should fall back to manual input.
# --------------------------
def test_sabio_api_error(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **kw: (_ for _ in ()).throw(Exception("API error")))

    inputs = iter(["1.0", "15.0", "7.2", "36.0"])
    monkeypatch.setattr("builtins.input", lambda msg: next(inputs))

    result = get_kinetic_params_from_sabio("bad", "query", interactive=True)

    assert result["km"] == 1.0
    assert result["vmax"] == 15.0
    assert result["optimal_pH"] == 7.2
    assert result["optimal_temp"] == 36.0

# --------------------------
# 🔇 Test 4: API error in non-interactive mode
# Function should not prompt the user and should return None.
# --------------------------
def test_sabio_api_error_noninteractive(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **kw: (_ for _ in ()).throw(Exception("No internet")))

    result = get_kinetic_params_from_sabio("x", "y", interactive=False)
    assert result is None

# --------------------------
# 🧩 Test 5: Partial data available
# Km and pH come from SABIO, Vmax and temp are entered by user.
# --------------------------
def test_sabio_partial_data(monkeypatch):
    class MockResponse:
        def raise_for_status(self): pass
        text = "Km = 0.4\npH-optimum = 6.5\n"

    monkeypatch.setattr("requests.get", lambda *a, **kw: MockResponse())

    inputs = iter(["11.0", "40.0"])  # for Vmax and temperature
    monkeypatch.setattr("builtins.input", lambda msg: next(inputs))

    result = get_kinetic_params_from_sabio("X", "Y", interactive=True)

    assert result["km"] == 0.4
    assert result["optimal_pH"] == 6.5
    assert result["vmax"] == 11.0
    assert result["optimal_temp"] == 40.0

# --------------------------
# 🔁 Test 6: Invalid user input then correction
# First input is invalid (non-numeric), second one is correct.
# Checks that the retry mechanism works.
# --------------------------
def test_sabio_input_retry(monkeypatch):
    class MockResponse:
        def raise_for_status(self): pass
        text = ""

    monkeypatch.setattr("requests.get", lambda *a, **kw: MockResponse())

    # Simulate: first input fails, then valid values
    responses = iter(["oops", "0.5", "5.5", "6.0", "37.0"])
    monkeypatch.setattr("builtins.input", lambda msg: next(responses))

    result = get_kinetic_params_from_sabio("retry", "case", interactive=True)

    assert result["km"] == 0.5
    assert result["vmax"] == 5.5
    assert result["optimal_pH"] == 6.0
    assert result["optimal_temp"] == 37.0
