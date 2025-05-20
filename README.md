# Echofoam EPCD Console Tool

This tool processes `.wav` audio files using Echofoam Prime-Coherence Detection (EPCD).  
It analyzes coherence, detects decoherence valleys, and outputs tone cues with embedded prime-aligned frequencies.

## Usage

```bash
python3 epcd_console.py input.wav
```

## Output

- `epcd_results.txt`: summary of coherence and tone cues
- `epcd_tone_output.wav`: audio track with tone cues injected at resonance points
