import requests # type: ignore
import re

# 🔁 Helper function outside the main block so it’s always visible
def _prompt_user_for_value(label):
    while True:
        try:
            return float(input(f"⚠️ {label} not found. Please enter {label} manually: "))
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_kinetic_params_from_sabio(enzyme_name, organism=None, interactive=True):
    """
    Fetches kinetic parameters for a given enzyme from the SABIO-RK database.
    """
    base_url = "https://sabiork.h-its.org/sabioRestWebServices/kineticLaws"

    # ✅ Use SABIO-RK's advanced search syntax
    query_string = f'EnzymeName:"{enzyme_name}"'
    if organism:
        query_string += f' AND Organism:"{organism}"'

    params = {
        "format": "txt",
        "query": query_string
    }

    try:
        print(f"\n🔍 Querying SABIO-RK for: {enzyme_name} ({organism or 'any organism'})...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        text_data = response.text

        # Extract values using regex
        km_values = [float(v) for v in re.findall(r"Km\s*=\s*([\d.]+)", text_data, re.IGNORECASE)]
        vmax_values = [float(v) for v in re.findall(r"Vmax\s*=\s*([\d.]+)", text_data, re.IGNORECASE)]
        ph_optima = [float(v) for v in re.findall(r"pH[- ]?optimum\s*=\s*([\d.]+)", text_data, re.IGNORECASE)]
        temp_optima = [float(v) for v in re.findall(r"temperature[- ]?optimum\s*=\s*([\d.]+)", text_data, re.IGNORECASE)]

        def get_avg(values):
            return sum(values) / len(values) if values else None

        # Handle missing values using fallback
        km = get_avg(km_values) or (_prompt_user_for_value("Km (mM)") if interactive else None)
        vmax = get_avg(vmax_values) or (_prompt_user_for_value("Vmax (µmol/min)") if interactive else None)
        pH_opt = get_avg(ph_optima) or (_prompt_user_for_value("optimal pH") if interactive else None)
        temp_opt = get_avg(temp_optima) or (_prompt_user_for_value("optimal temperature (°C)") if interactive else None)

        return {
            "km": km,
            "vmax": vmax,
            "optimal_pH": pH_opt,
            "optimal_temp": temp_opt
        }

    except Exception as e:
        print("❌ Error accessing SABIO-RK:", e)
        if interactive:
            return {
                "km": _prompt_user_for_value("Km (mM)"),
                "vmax": _prompt_user_for_value("Vmax (µmol/min)"),
                "optimal_pH": _prompt_user_for_value("optimal pH"),
                "optimal_temp": _prompt_user_for_value("optimal temperature (°C)")
            }
        else:
            return None
