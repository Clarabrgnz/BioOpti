![Project Logo](assets/banner.png)

![Coverage Status](assets/coverage-badge.svg)

<h1 align="center">
BioOpti
</h1>

<br>


**BioOpti** helps you optimize your biochemical workflows — from culture media formulation to enzyme kinetics.  
Whether you're a researcher, student, or just curious about bioprocesses, BioOpti makes it easier to simulate, predict, and improve your experimental setups.


## 🔥 Quick Start

### ⚠️⚠️⚠️COMPLTE FOR CULUTRE MDEIA OPTIMIZATION 


### 🧪 Simulation of enzymatic reactions
This quick example shows how to simulate an enzyme-catalyzed reaction under specific conditions.

```python
from bioopti.simulation import simulate_reaction

# Simulate an enzyme reaction with your input parameters
result = simulate_reaction(
    substrate_conc=2.5,
    enzyme_params={
        "Vmax": 1.8,
        "Km": 0.5,
        "opt_pH": 7.0,
        "opt_temp": 37,
        "inh_type": "competitive",
        "inh_conc": 0.1
    },
    pH=6.8,
    temperature=35,
    inhibitors=True
)

print(result)
```

## 👩‍💻 Installation

Create a new environment, you may also give the environment a different name. 

```
conda create -n bioopti python=3.10 
```

```
conda activate bioopti
(conda_env) $ pip install .
```

If you need jupyter lab, install it 

```
(bioopti) $ pip install jupyterlab
```


## 🛠️ Development installation

Initialize Git (only for the first time). 

Note: You should have create an empty repository on `https://github.com:Clarabrgnz/BioOpti`.

```
git init
git add * 
git add .*
git commit -m "Initial commit" 
git branch -M main
git remote add origin git@github.com:Clarabrgnz/BioOpti.git 
git push -u origin main
```

Then add and commit changes as usual. 

To install the package, run

```
(bioopti) $ pip install -e ".[test,doc]"
```

### ⚙️ Run tests and coverage

```
(conda_env) $ pip install tox
(conda_env) $ tox
```

## ⚖️ License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute this software with proper attribution.  
See the LICENSE file for full details.




