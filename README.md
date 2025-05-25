# Echofoam-Falsifiability-suite
Scientific challenge suite for testing Echofoam Theory (emergent c, BAOs, redshift)
# Echofoam Falsifiability Suite

This repository contains a simplified simulation framework designed to test the Echofoam Theory of cosmological structure formation.

**Purpose:**  
To allow open, scientific attempts to *falsify* the theory by evaluating its predictions under clean, documented conditions.

**Included Tests:**
- Emergent `c` (causality propagation without injected constants)
- BAO ring emergence via foam burst tension
- Redshift via tension drag ("Echoshift")

**Why?**  
If Echofoam holds up to scrutiny, it may offer a new pathway to understanding cosmic memory, emergence, and tension as foundational to structure.
## Dependencies

The programs rely on the following packages:
- numpy
- matplotlib
- pillow
- moviepy
- ffmpeg (for video creation)
- tkinter (usually installed with Python)
- pytest and flake8 (for tests and linting)

A Conda environment file `environment.yml` is provided for convenience.


## Getting Started

1. Create the Conda environment:
```bash
conda env create -f environment.yml
conda activate echofoam
```

Alternatively install with pip:
```bash
pip install numpy matplotlib pillow moviepy
```

2. Run the simulation or use the blockchain memory module as needed.


## Blockchain Memory Scaffold

The file `blockchain_memory.py` implements a minimal compressed memory chain where each entry references the previous block via its hash. The chain is saved to disk for persistence.

### Example
```python
from blockchain_memory import BlockchainMemory

mem = BlockchainMemory("demo_chain.json")
block = mem.add_memory("an important observation")
print(block.hash)
```
