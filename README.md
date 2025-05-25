# Echofoam-Falsifiability-suite
Scientific challenge suite for testing Echofoam Theory (emergent c, BAOs, redshift)
# Echofoam Falsifiability Suite

This repository contains a simplified simulation framework designed to test the Echofoam Theory of cosmological structure formation.

**Purpose:**  
To allow open, scientific attempts to *falsify* the theory by evaluating its predictions under clean, documented conditions.

**Included Tests:**
- **Emergent `c`** – checks whether the wave field naturally converges on a
  uniform propagation speed, echoing the observed speed of light.
- **BAO** – tests for self-organizing ring patterns similar to baryon acoustic
  oscillations within the tension field.
- **Higgs** – looks for localized resonance that would mimic mass acquisition
  through a Higgs-like mechanism.
- Redshift via tension drag ("Echoshift")

**Why?**  
If Echofoam holds up to scrutiny, it may offer a new pathway to understanding cosmic memory, emergence, and tension as foundational to structure.

## Getting Started

1. Install requirements
```bash
pip install numpy matplotlib
```

2. Run the simulation
```bash
python simulation.py
```
This generates an animation of the tension field along with a final frame image.
Output files are saved in the repository root:
- `simulation.mp4` – animation of the full run
- `final_frame.png` – last frame of the visualization
- `echofoam_cosmo_log.txt` – log with the final verdict

The MP4 animation requires the optional `ffmpeg` dependency so `matplotlib` can
use the `FFMpegWriter` backend.

3. Use the blockchain memory module as needed.

## Blockchain Memory Scaffold

The file `blockchain_memory.py` implements a minimal compressed memory chain where each entry references the previous block via its hash. The chain is saved to disk for persistence.

### Example
```python
from blockchain_memory import BlockchainMemory

mem = BlockchainMemory("demo_chain.json")
block = mem.add_memory("an important observation")
print(block.hash)
```
