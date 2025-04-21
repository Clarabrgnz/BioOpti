import os
import json

def load_local_enzyme_data(filepath):
    """Load enzyme kinetics data from a local JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Could not find the JSON file at {filepath}")
    with open(filepath, "r") as file:
        data = json.load(file)
    return data

def get_enzyme_kinetics(enzyme_name, organism=None, filepath=None):
    """
    Fetches kinetic parameters for a given enzyme from a local JSON file.
    """
    if filepath is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        filepath = os.path.join(project_root, "data", "enzyme_data.json")

    print(f"📁 Loading enzyme data from: {filepath}")

    data = load_local_enzyme_data(filepath)

    matches = []
    for key, params in data.items():
        enzyme, org = key.rsplit(" (", 1)
        org = org.rstrip(")")
        if enzyme.lower() == enzyme_name.lower() and (organism is None or organism.lower() == org.lower()):
            matches.append(params)

    if not matches:
        raise ValueError(f"No match found for enzyme '{enzyme_name}' with organism '{organism}'.")

    return matches[0]
