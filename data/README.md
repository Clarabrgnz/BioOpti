# 📁 Data Folder

This folder contains all the **local datasets** used by the BioOpti project.

---

## 🧪 Medium Optimization Dataset

🔧 **(To be completed)**

---

## 🔬 Enzyme Kinetics Dataset

- **Filename**: `enzyme_data.json`
- **Format**: JSON file containing enzyme kinetics parameters.
- **Structure**:
  - Dictionary where each key is an enzyme entry in the form:  
    `"enzyme name (organism name)"`.
  - Each value is a dictionary of kinetic parameters.

### 📌 Example
```json
{
  "lactate dehydrogenase (Homo sapiens)": {
    "vmax": 100.0,
    "km": 0.5,
    "optimal_pH": 7.0,
    "optimal_temp": 37.0,
    "pH_sigma": 1.0,
    "temp_sigma": 5.0
  }
}
```

---

### 📚 Required Fields per Enzyme

| Parameter | Description | Unit |
|:----------|:------------|:-----|
| `vmax` | Maximum reaction rate | µmol/min |
| `km` | Michaelis constant | mM |
| `optimal_pH` | Optimal pH | - |
| `optimal_temp` | Optimal temperature | °C |
| `pH_sigma` | pH tolerance (σ value) | - |
| `temp_sigma` | Temperature tolerance (σ value) | - |
| `ki` *(optional)* | Inhibition constant (competitive) | mM |

---

### ⚙️ Usage

The enzyme kinetics dataset is used by:
- `load_local_enzyme_data`
- `get_enzyme_kinetics`
- `simulate_from_local_data`

---
