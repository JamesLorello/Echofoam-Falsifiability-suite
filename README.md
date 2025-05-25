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

## Getting Started

1. Install requirements  
```bash  
pip install numpy matplotlib  
```


2. Run the simulation or use the blockchain memory module as needed.

## Directory Structure

Each major program lives in its own subdirectory:

- `adaptive_gui/`
- `blockchain_memory/`
- `laser_filamentation/`
- `mashup_maker/`
- `teleportation/`
- `weather_simulation/`

## Blockchain Memory Scaffold

The `blockchain_memory` package implements a minimal compressed memory chain where each entry references the previous block via its hash. The chain is saved to disk for persistence.

### Example
```python
from blockchain_memory.blockchain_memory import BlockchainMemory

mem = BlockchainMemory("demo_chain.json")
block = mem.add_memory("an important observation")
print(block.hash)
```
