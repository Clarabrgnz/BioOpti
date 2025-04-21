import math
from .enzyme_kinetics import get_enzyme_kinetics

def simulate_reaction_rate(
    substrate_conc,        # [S] in mM
    vmax,                  # Vmax in µmol/min
    km,                    # Km in mM
    ph,                    # current pH
    temp,                  # current temperature in °C
    optimal_ph=7.0,        # enzyme's optimal pH
    optimal_temp=37.0,     # enzyme's optimal temperature
    ph_sigma=1.0,          # tolerance to pH deviation
    temp_sigma=5.0,        # tolerance to temp deviation
    inhibitor_conc=None,   # [I] in mM (optional)
    ki=None                # Ki in mM (optional)
):
    """
    Calculates the enzymatic reaction rate v under given conditions
    using Michaelis-Menten kinetics with optional temperature and pH penalties,
    and competitive inhibition.

    Returns:
        v (float): reaction rate in µmol/min
    """

    # 📈 Apply competitive inhibition if parameters are provided
    if inhibitor_conc is not None and ki is not None:
        effective_km = km * (1 + inhibitor_conc / ki)
    else:
        effective_km = km

    base_rate = (vmax * substrate_conc) / (effective_km + substrate_conc)

    # 📉 Gaussian penalty for temperature deviation
    temp_penalty = math.exp(-((temp - optimal_temp) ** 2) / (2 * temp_sigma ** 2))

    # 📉 Gaussian penalty for pH deviation
    ph_penalty = math.exp(-((ph - optimal_ph) ** 2) / (2 * ph_sigma ** 2))

    # 🔬 Adjust Km if inhibitor is present (competitive inhibition)
    km_effective = km
    if inhibitor_conc is not None and ki is not None:
        km_effective = km * (1 + inhibitor_conc / ki)

    # ⚙️ Michaelis-Menten equation
    v = (vmax * substrate_conc) / (km_effective + substrate_conc)

    # ⚠️ Apply environmental effects
    v *= temp_penalty * ph_penalty

    return v

def simulate_from_local_data(
    enzyme_name,
    organism=None,
    substrate_conc=1.0,
    ph=7.0,
    temp=37.0,
    inhibitor_conc=None,
    ki=None,
    ph_sigma=1.0,
    temp_sigma=5.0
):
    local_params = get_enzyme_kinetics(
        enzyme_name=enzyme_name,
        organism=organism
    )

    v = simulate_reaction_rate(
        substrate_conc=substrate_conc,
        vmax=local_params["vmax"],
        km=local_params["km"],
        ph=ph,
        temp=temp,
        optimal_ph=local_params["optimal_pH"],
        optimal_temp=local_params["optimal_temp"],
        ph_sigma=ph_sigma,
        temp_sigma=temp_sigma,
        inhibitor_conc=inhibitor_conc,
        ki=ki
    )

    return v, local_params

if __name__ == "__main__":
    enzyme = "lactate dehydrogenase"
    organism = "Homo sapiens"
    rate, params = simulate_from_local_data(
        enzyme_name=enzyme,
        organism=organism,
        substrate_conc=0.3,
        ph=7.2,
        temp=36.0
    )

    print(f"\nSimulated rate for {enzyme} ({organism}): {rate:.2f} µmol/min")
    print("Used parameters:", params)

