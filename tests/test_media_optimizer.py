
import os, sys, inspect
# (make sure this path truly points at your src folder)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import bioopti.media_optimizer as mo

print(">>> LOADED MEDIA_OPTIMIZER FROM:", inspect.getfile(mo))


import bioopti.media_optimizer
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
    get_headers,
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
    monkeypatch.setattr(bioopti.media_optimizer.imizer.requests, "get", fake_get)


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

def test_get_bearer_token_http_error(monkeypatch):
    # simulate a 400 from the token endpoint
    dummy = DummyResponse({}, status_code=400)
    monkeypatch.setattr(requests, "post", lambda *a, **k: dummy)
    with pytest.raises(requests.HTTPError):
        get_bearer_token()

def test_get_bearer_token_missing_token(monkeypatch):
    # simulate no "access_token" field
    monkeypatch.setattr(requests, "post", lambda *a, **k: DummyResponse({"foo":"bar"}))
    with pytest.raises(RuntimeError):
        get_bearer_token()

def test_get_headers(monkeypatch):
    # stub get_bearer_token
    monkeypatch.setattr(bioopti.media_optimizer, "get_bearer_token", lambda: "abc123")
    assert get_headers() == {"Authorization":"Bearer abc123"}

def test_search_ids_with_fallback_id_key(monkeypatch, token_resp):
    # pretend results include dicts with key "id", not "bacdive_id"
    resp = DummyResponse({"results":[{"id":123}, 456]})
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    ids = search_ids("AB 123", headers={})
    assert ids == [123, 456]

def test_search_ids_http_error(monkeypatch):
    err = DummyResponse({}, status_code=500)
    monkeypatch.setattr(requests, "get", lambda *a, **k: err)
    with pytest.raises(requests.HTTPError):
        search_ids("Foo bar", headers={})

def test_fetch_strain_list(monkeypatch):
    data = [{"foo":"bar"}]
    resp = DummyResponse({"results": data})
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    assert fetch_strain(1, {}) == data[0]

def test_fetch_strain_empty(monkeypatch):
    # no results key or empty
    resp = DummyResponse({})
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    assert fetch_strain(1, {}) == {}

def test_extract_media_multiple_entries():
    strain = {"Culture and growth conditions":{
        "culture medium":[{"name":"A"}, {"name":"B"}]
    }}
    media = extract_media(strain)
    assert [m["name"] for m in media] == ["A","B"]

def test_extract_media_missing_key():
    assert extract_media({}) == []
    assert extract_media({"Culture and growth conditions":{}}) == []

def test_extract_temperature_growth_field():
    strain = {"Culture and growth conditions":{
        "opt_temp":[],"some_temp":[{"test_type":"growth","value": 42}]
    }}
    assert extract_temperature(strain) == "42°C"

def test_extract_temperature_numeric_field():
    strain = {"Culture and growth conditions":{
        "foo_temp":[{"temperature": 37}]
    }}
    assert extract_temperature(strain) == "37°C"

def test_extract_temperature_range_hyphen():
    strain = {"Culture and growth conditions":{
        "temp_info":[{"value":"10-20"}]
    }}
    # (10+20)/2 = 15
    assert extract_temperature(strain) == "15°C"

def test_extract_temperature_description():
    strain = {"Culture and growth conditions":{
        "weird":[{"description":"thrives at 55 °C in lab"}]
    }}
    assert extract_temperature(strain) == "55°C"

def test_run_no_media(monkeypatch, capsys):
    # search → [1], fetch → no culture medium
    monkeypatch.setattr(mo, "search_ids", lambda q,h: [1])
    monkeypatch.setattr(mo, "fetch_strain", lambda i,h: {})
    # must exit 0 with correct message
    with pytest.raises(SystemExit) as e:
        run("foo")
    out = capsys.readouterr().out
    assert "No medium info available for 'foo'" in out
    assert e.value.code == 0
