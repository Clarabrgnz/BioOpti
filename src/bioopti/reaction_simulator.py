import os #For working with file paths
import json #To read the enzyme data from a .json file
import math #For mathematical operations

def load_local_enzyme_data(filepath):
    """Load enzyme kinetics data from a local JSON file."""
    if not os.path.exists(filepath): #Checks if the file exists
        raise FileNotFoundError(f"Could not find the JSON file at {filepath}") #If not, raises an error
    with open(filepath, "r") as file: #Opens the file in read mode and loads the data
        data = json.load(file)
    return data

def normalize_keys(param_dict):
    """
    Convert unit-tagged keys to generic keys, 
    but preserve already normalized keys.
    """
    key_mapping = { #Creates a dictionary that maps the unit-tagged keys (from the .json) to generic ones
        "km_mM": "km",
        "vmax_umol_per_min": "vmax",
        "optimal_pH": "optimal_pH",
        "optimal_temp_C": "optimal_temp",
        "ph_sigma": "ph_sigma",
        "temp_sigma_C": "temp_sigma",
        "ki_mM": "ki"
    }
    normalized = {}
    for k, v in param_dict.items():
        if k in key_mapping:
            normalized[key_mapping[k]] = v
        else:
            normalized[k] = v  #Keeps the key as it is if it's already normalized
    return normalized


def get_enzyme_kinetics(enzyme_name, organism=None, filepath=None):
    """
    Fetches kinetic parameters for a given enzyme from a local JSON file.
    """
    if filepath is None: #If the user didn’t specify a path, finds the default path: data/enzyme_data.json
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        filepath = os.path.join(project_root, "data", "enzyme_data.json")

    print(f"📁 Loading enzyme data from: {filepath}") #Prints out where the file is being loaded from

    data = load_local_enzyme_data(filepath) #Uses the previous function to load the JSON data into a Python dictionary

    matches = [] #Creates an empty list to store matches in case multiple entries exist for the same enzyme

    for key, params in data.items(): #Splits the key into enzyme name and organism
        enzyme, org = key.rsplit(" (", 1)
        org = org.rstrip(")")
        if enzyme.lower() == enzyme_name.lower() and (organism is None or organism.lower() == org.lower()): #Checks if the enzyme name and organism match the user’s input
            matches.append(normalize_keys(params)) #If they do, appends the parameters to the matches list

    if not matches: #If no matches were found, raises an error
        raise ValueError(f"No match found for enzyme '{enzyme_name}' with organism '{organism}'.")

    return matches[0] #Returns the first match found (if multiple matches exist, the first one is returned)


def simulate_reaction_rate(
    substrate_conc,        # substrate concentration [S] in mM
    vmax,                  # maximum reaction rate Vmax in µmol/min
    km,                    # Michaelis constant Km in mM
    ph,                    # current pH of the system
    temp,                  # current temperature in °C
    optimal_ph=7.0,        # enzyme's optimal pH
    optimal_temp=37.0,     # enzyme's optimal temperature
    ph_sigma=1.0,          # enzyme’s tolerance to pH deviation
    temp_sigma=5.0,        # enzyme’s tolerance to temperature deviation
    inhibitor_conc=None,   # inhibitor concentration [I] in mM (optional)
    ki=None                # inhibition constant Ki in mM (optional)
):

    """
    Calculates enzymatic reaction rate using Michaelis-Menten model
    with temperature and pH Gaussian penalties and optional inhibition.
    """
    km_effective = km #Uses default km unless modified by inhibition
    if inhibitor_conc is not None and ki is not None: #If the user provided an inhibitor concentration and ki value, modifies the km value according to the competitive inhibition formula
        km_effective = km * (1 + inhibitor_conc / ki)

    v = (vmax * substrate_conc) / (km_effective + substrate_conc) #Computes the base reaction rate using the Michaelis-Menten equation

    temp_penalty = math.exp(-((temp - optimal_temp) ** 2) / (2 * temp_sigma ** 2))
    ph_penalty = math.exp(-((ph - optimal_ph) ** 2) / (2 * ph_sigma ** 2))
    #Applies Gaussian penalties for temperature and pH deviations
    v *= temp_penalty * ph_penalty
    #Applies both penalties to the reaction rate to simulate environmental effects
    return v
    #Returns the final simulated reaction rate in µmol/min

def simulate_from_local_data(
    enzyme_name,
    organism=None,
    substrate_conc=1.0,
    ph=7.0,
    temp=37.0,
    inhibitor_conc=None,
    ph_sigma=None,
    temp_sigma=None,
    ki=None
    ):

    """
    Simulates the enzymatic reaction rate using parameters loaded from a local JSON file.

    This function fetches kinetic and environmental parameters (e.g. Km, Vmax, optimal pH, 
    temperature) for a specified enzyme from a local dataset, then computes the reaction 
    rate using the Michaelis-Menten equation adjusted for environmental conditions 
    (pH and temperature) and optional competitive inhibition.

    Parameters:
        enzyme_name (str): Name of the enzyme (e.g., "hexokinase").
        organism (str, optional): Species of origin (e.g., "Homo sapiens"). If None, matches any.
        substrate_conc (float, optional): Substrate concentration [S] in mM (default: 1.0).
        ph (float, optional): Current pH of the environment (default: 7.0).
        temp (float, optional): Current temperature in °C (default: 37.0).
        inhibitor_conc (float, optional): Inhibitor concentration [I] in mM (default: None).
        ph_sigma (float, optional): Override for pH tolerance (if None, uses JSON value).
        temp_sigma (float, optional): Override for temperature tolerance (if None, uses JSON value).
        ki (float, optional): Override for inhibition constant Ki in mM (if None, uses JSON value).

    Returns:
        tuple:
            - v (float): Simulated reaction rate in µmol/min.
            - local_params (dict): Dictionary of kinetic and environmental parameters used.
    """
 
    local_params = get_enzyme_kinetics( #Uses the get_enzyme_kinetics function to load the data for the given enzyme and organism
        enzyme_name=enzyme_name,
        organism=organism
    )

    v = simulate_reaction_rate( #Uses the simulate_reaction_rate function to compute the reaction rate
    # User inputs: substrate_conc, ph, temp, inhibitor_conc
    # Loaded from JSON: vmax, km, optimal_ph, optimal_temp, ph_sigma, temp_sigma, ki
    # If the user provided ph_sigma, temp_sigma, or ki, those override the JSON values
        substrate_conc=substrate_conc,
        vmax=local_params["vmax"],
        km=local_params["km"],
        ph=ph,
        temp=temp,
        optimal_ph=local_params["optimal_pH"],
        optimal_temp=local_params["optimal_temp"],
        ph_sigma=ph_sigma if ph_sigma is not None else local_params["ph_sigma"],
        temp_sigma=temp_sigma if temp_sigma is not None else local_params["temp_sigma"],
        inhibitor_conc=inhibitor_conc,
        ki=ki if ki is not None else local_params.get("ki")
    )
    # Return the computed reaction rate and the parameters used for simulation
    return v, local_params

