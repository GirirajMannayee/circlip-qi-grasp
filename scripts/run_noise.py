#!/usr/bin/env python3
"""Gate 2 + Gate 3: ideal statevector and FakeManilaV2 noisy runs (Tables 12-14, Fig. 17).
Writes data/results/noise_runs.json."""
import json, pathlib, platform
import qiskit, qiskit_aer, qiskit_ibm_runtime
from qi_grasp.noise import run_all, SEEDS, SHOTS

ROOT = pathlib.Path(__file__).resolve().parents[1]
res = run_all()
meta = dict(qiskit=qiskit.__version__, qiskit_aer=qiskit_aer.__version__,
            qiskit_ibm_runtime=qiskit_ibm_runtime.__version__, python=platform.python_version(),
            shots=SHOTS, seeds=SEEDS, optimization_level=1, seed_transpiler=42, backend="FakeManilaV2")
out = ROOT / "data" / "results" / "noise_runs.json"
out.write_text(json.dumps({"meta": meta, "runs": res}, indent=2))
for r in res:
    print(f'{r["name"]:36s} depth={r["depth"]:3d} 2q={r["two_qubit_gates"]:3d} ideal={r["ideal_p"]:.3f} '
          f'noisy={r["noisy_p_mean"]:.3f}±{r["noisy_p_sd"]:.3f} H={r["hellinger_mean"]:.3f} modal={r["modal_best_all_seeds"]}')
print("wrote", out)
