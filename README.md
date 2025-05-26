# Echofoam-Falsifiability-suite
Scientific challenge suite for testing Echofoam Theory (emergent c, BAOs, redshift)
# Echofoam Falsifiability Suite
## 🔗 Cite This Release

## 📌 Cite This Release

[![DOI](https://zenodo.org/badge/961712182.svg)](https://doi.org/10.5281/zenodo.15505391)

> Lorello, James. *Echofoam Falsifiability Suite v1.0*. Zenodo.  
DOI: [10.5281/zenodo.15505391](https://doi.org/10.5281/zenodo.15505391)

This repository contains a simplified simulation framework designed to test the Echofoam Theory of cosmological structure formation.

**Purpose:**  
To allow open, scientific attempts to *falsify* the theory by evaluating its predictions under clean, documented conditions.

**Included Tests:**
- Emergent `c` (causality propagation without injected constants)
- BAO ring emergence via foam burst tension
- Redshift via tension drag ("Echoshift")

**Why?**  
If Echofoam holds up to scrutiny, it may offer a new pathway to understanding cosmic memory, emergence, and tension as foundational to structure.

## Getting Started

1. Install requirements
```bash
pip install numpy matplotlib
```

2. Run the Tkinter viewer to visualize the tension-based interface. Tkinter is bundled with Python on many systems (on some Linux distributions you may need to install `python3-tk`). Use the command:
```bash
python adaptive_gui.py
```

3. Run the simulation or use the blockchain memory module as needed.

## Blockchain Memory Scaffold

The file `blockchain_memory.py` implements a minimal compressed memory chain where each entry references the previous block via its hash. The chain is saved to disk for persistence.

### Example
```python
from blockchain_memory import BlockchainMemory

mem = BlockchainMemory("demo_chain.json")
block = mem.add_memory("an important observation")
print(block.hash)
```

## Weather Sphere Simulation
The module `weather_sphere.py` provides a simple 3D fluid field in spherical coordinates. It models the atmosphere as a thin shell above a bumpy terrain and visualizes a slice of the final temperature-pressure field.

### Usage
```bash
python -m echofoam_falsifiability.weather_sphere --radius 1.0 --theta 1.57 --phi 6.28 --bump 0.05 --steps 200 --show
```
Adjust the parameters to explore different sphere sizes, angular extents and terrain bumpiness.
Use `--show` to display an updating 3D view. A final `weather_sphere.png` image is also saved.
