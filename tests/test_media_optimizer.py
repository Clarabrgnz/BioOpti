import bioopti  # Import the bioopti module
import pytest  # type: ignore #Testing framework
import tempfile # To create temporary files (for simulating real JSON files).
import json  # To write and read JSON data
import os # To handle file paths and remove temporary files
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import requests
from scipy.optimize import differential_evolution #For optimization functions
import sys # To add the src directory to the path for importing bioopti
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))) #Adds the src directory to the Python path so that the bioopti module can be imported

from bioopti.media_optimizer import (
    get_bearer_token,
    search_ids,
    fetch_strain,
    extract_media,
    extract_temperature,
    display_media_table,
    run,
)
import bioopti.media_optimizer as mo
# --------------------- Fixtures ---------------------
class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"Status {self.status_code}")

@pytest.fixture
def token_resp():
    return DummyResponse({"access_token": "fake-token"})

@pytest.fixture
def search_resp():
    # simulate two kinds of results: dict-entry and bare int
    return DummyResponse({"results": [{"bacdive_id": 42}, 99]})

@pytest.fixture
def strain_resp():
    # returns one dict under key "1", with a simple CGC block
    strain = {
        "Culture and growth conditions": {
            "culture medium": [
                {"name": "M1", "growth": "good", "composition": "C1", "link": "L1"}
            ],
            "optimum temperature": [{"value": "37 °C"}]
        }
    }
    return DummyResponse({"results": {"1": strain}})

@pytest.fixture(autouse=True)
def mock_requests(monkeypatch, token_resp, search_resp, strain_resp):
    # stub out requests.post → token
    monkeypatch.setattr(bioopti.media_optimizer.requests, "post",
                        lambda *a, **k: token_resp)
    # stub out requests.get → search or fetch endpoints
    def fake_get(url, headers):
        if url.startswith(bioopti.media_optimizer.API_BASE_URL + "/culturecollectionno"):
            return search_resp
        if url.startswith(bioopti.media_optimizer.API_BASE_URL + "/taxon"):
            return search_resp
        if url.startswith(bioopti.media_optimizer.API_BASE_URL + "/fetch"):
            return strain_resp
        return DummyResponse({}, 404)
    monkeypatch.setattr(bioopti.media_optimizer.requests, "get", fake_get)


# --------------------- Tests ---------------------

def test_get_bearer_token_success():
    token = get_bearer_token()
    assert token == "fake-token"

def test_search_ids_by_collection():
    ids = search_ids("AB 12345", headers={})
    assert ids == [42, 99]

def test_search_ids_by_taxon():
    ids = search_ids("Bacillus subtilis", headers={})
    assert ids == [42, 99]

def test_search_ids_too_few_parts():
    with pytest.raises(ValueError):
        search_ids("Bacillus", headers={})

def test_fetch_strain_returns_dict():
    strain = fetch_strain(1, headers={})
    # our fixture puts the strain dict under key "1"
    assert "Culture and growth conditions" in strain

def test_extract_media_empty():
    assert extract_media({}) == []
    assert extract_media({"Culture and growth conditions": {}}) == []

def test_extract_media_list():
    strain = {"Culture and growth conditions": {"culture medium": {"name": "X"}}}
    media = extract_media(strain)
    assert isinstance(media, list)
    assert media[0]["name"] == "X"

def test_extract_temperature_optimum():
    strain = {
        "Culture and growth conditions": {
            "opt_temp": [{"test_type": "optimum", "value": "20–30 °C"}]
        }
    }
    # average of 20 and 30 is 25
    assert extract_temperature(strain) == "25°C"

def test_extract_temperature_regex_blob():
    strain = {"Culture and growth conditions": {"foo": "grows at 42 °C happily"}}
    assert extract_temperature(strain) == "42°C"

def test_extract_temperature_none():
    # no temp info at all
    assert extract_temperature({"Culture and growth conditions": {}}) == "-"

def test_display_media_table(capsys):
    media_list = [{"name": "M1", "growth": "G", "composition": "C", "link": "L"}]
    display_media_table("Q", media_list, "30°C")
    out = capsys.readouterr().out
    # should include header and at least one media name
    assert "Media Recipes for 'Q'" in out
    assert "M1" in out
    assert "30°C" in out

def test_run_happy_path(capsys, monkeypatch):
    # stub search_ids → [1], fetch_strain → well-formed
    monkeypatch.setattr(mo, "search_ids", lambda q, h: [1])
    monkeypatch.setattr(mo, "fetch_strain", lambda i, h: {
        "Culture and growth conditions": {
            "culture medium": [{"name": "X", "growth": "-", "composition": "-", "link": "-"}]
        }
    })
    # patch temperature extractor
    monkeypatch.setattr(mo, "extract_temperature", lambda s: "15°C")

    run("anything")
    out = capsys.readouterr().out
    assert "Media Recipes for 'anything'" in out
    assert "X" in out

def test_run_value_error(monkeypatch, capsys):
    monkeypatch.setattr(mo, "search_ids", lambda q, h: (_ for _ in ()).throw(ValueError("oops")))
    with pytest.raises(SystemExit) as e:
        run("bad")
    out = capsys.readouterr().out
    assert "[red]Error:[/]" in out
    assert e.value.code == 1

def test_run_no_ids(monkeypatch, capsys):
    monkeypatch.setattr(mo, "search_ids", lambda q, h: [])
    with pytest.raises(SystemExit) as e:
        run("none")
    out = capsys.readouterr().out
    assert "No strains found for 'none'" in out
    assert e.value.code == 0