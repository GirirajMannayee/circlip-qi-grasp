#!/usr/bin/env python3
"""Write Quirk JSON/URL and OpenQASM (Appendix B.4/B.5) and verify P(0101) = 0.9613 independently."""
import json, pathlib, numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qi_grasp.circuits import quirk_json, quirk_url, gate_level_qasm2, build_gate_level
ROOT = pathlib.Path(__file__).resolve().parents[1] / "circuits"
(ROOT / "qio_quirk_circuit_K3.json").write_text(json.dumps(quirk_json(3), ensure_ascii=False, indent=1))
(ROOT / "qio_quirk_url.txt").write_text(quirk_url(3) + "\n")
qasm = gate_level_qasm2(3); (ROOT / "qio_hard_oracle_K3.qasm").write_text(qasm)
qc = QuantumCircuit.from_qasm_str(qasm).remove_final_measurements(inplace=False)
p = Statevector.from_instruction(qc).probabilities()
ref = Statevector.from_instruction(build_gate_level(3, measure=False)).probabilities()
print("QASM  P(0101)=%.4f argmax=%d" % (p[5], p.argmax()))
assert abs(p[5] - 0.9613) < 5e-4 and p.argmax() == 5 and np.allclose(p, ref, atol=1e-12)
print("columns in Quirk export:", len(quirk_json(3)["cols"]), "(= 1 + 3x10 + measurement)")
