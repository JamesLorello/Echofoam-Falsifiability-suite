# Orientation control pass: retained record

The full run passes the prospective 1% material-effect threshold and all
declared control gates. Its adjusted coherent endpoint effect is 1.3738%
(paired seed-bootstrap 95% interval 1.3736% to 1.3740%).

Read the [result report](../../docs/ORIENTATION_CONTROL_RESULTS_2026-09-13.md)
for interpretation and the [protocol](../../docs/ORIENTATION_CONTROL_PROTOCOL.md)
for the estimand, initialization changes, and decision rules.

| File or directory | Contents |
| --- | --- |
| [manifest.json](manifest.json) | Parameters, fixed seeds, threshold, software versions, and source hashes recorded before outcomes |
| [runs.csv](runs.csv) | 1,368 measurements: 24 seeds times 3 conditions times 19 angles, including both dynamics and initial energies |
| [effects.csv](effects.csv) | Paired AUC and percentage effects, bootstrap intervals, standardized effects, and simultaneous bands |
| [summary.json](summary.json) | Full statistics, primary/control contrasts, numerical diagnostics, and decision gates |
| [verification.json](verification.json) | Source-hash checks, exact statistics replay from CSV, and numerical sensitivity comparisons |
| [source_history.bundle](source_history.bundle) | Original local source commits referenced by the run manifests, including the prospective protocol and supplementary-check specification |
| [angle_sweep.png](angle_sweep.png), [angle_sweep.svg](angle_sweep.svg) | Sweep figure with simultaneous uncertainty bands and the material threshold |
| [numerical_checks/timestep_halved](numerical_checks/timestep_halved) | Four-seed endpoint sensitivity run with dt halved |
| [numerical_checks/finer_grid](numerical_checks/finer_grid) | Four-seed endpoint sensitivity run with N=128 and dt halved |

There are 24 independent seed blocks in the main run. Bootstrap intervals
describe seed variation in these toy equations. The smaller timestep run's
standalone coherent-minus-shuffled comparison remains inconclusive at the 1%
margin; it is retained and is not pooled into the main inference.

The CSV line endings and SVG trailing spaces were normalized for version
control after capture. Measurement values and statistical results are unchanged.

Publication through the connected GitHub account creates a publication commit
with its own timestamp and identifier. The original run revisions are preserved
in the source bundle, rather than relabeling the measurements with a later
publication revision. From a checkout containing baseline main commit
`40d23df`, recover that source history with:

```bash
git fetch results/orientation_control_2026-09-13/source_history.bundle refs/heads/codex/orientation-run-source:refs/heads/reproduce/orientation-run-source
```
