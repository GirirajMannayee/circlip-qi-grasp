"""Qiskit circuits (Appendix B.2), Quirk JSON (B.4) and OpenQASM (B.5) exports."""
from __future__ import annotations
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import DiagonalGate


def build_circuit(phases, K: int) -> QuantumCircuit:
    """Soft/hard oracle as a 4-qubit DiagonalGate (Appendix B.2, build_circuit)."""
    qc = QuantumCircuit(4, 4)
    qc.h(range(4))
    for _ in range(K):
        qc.append(DiagonalGate(list(np.exp(1j * np.asarray(phases)))), range(4))
        _diffusion(qc)
    qc.measure(range(4), range(4))
    return qc


def _diffusion(qc: QuantumCircuit) -> None:
    qc.h(range(4)); qc.x(range(4))
    qc.h(3); qc.mcx([0, 1, 2], 3); qc.h(3)
    qc.x(range(4)); qc.h(range(4))


def build_gate_level(K: int, measure: bool = True) -> QuantumCircuit:
    """Hard oracle, marked index 0101 (candidate 5), X-CCCZ-X (Appendix B.2, build_gate_level)."""
    qc = QuantumCircuit(4, 4 if measure else 0)
    qc.h(range(4))
    for _ in range(K):
        qc.x([1, 3]); qc.h(3); qc.mcx([0, 1, 2], 3); qc.h(3); qc.x([1, 3])   # oracle
        _diffusion(qc)
    if measure:
        qc.measure(range(4), range(4))
    return qc


def quirk_json(K: int = 3) -> dict:
    """Quirk export of the hard-oracle circuit: 1 + K*10 gate columns + measurement (Sec. 4.4)."""
    H = ["H"] * 4; X4 = ["X"] * 4
    cols = [H]
    for _ in range(K):
        cols += [[1, "X", 1, "X"], ["•", "•", "•", "Z"], [1, "X", 1, "X"],
                 H, X4, [1, 1, 1, "H"], ["•", "•", "•", "X"], [1, 1, 1, "H"], X4, H]
    cols.append(["Measure"] * 4)
    return {"cols": cols}


def quirk_url(K: int = 3) -> str:
    return "https://algassert.com/quirk#circuit=" + json.dumps(quirk_json(K), separators=(",", ":"), ensure_ascii=False)


def gate_level_qasm2(K: int = 3) -> str:
    """OpenQASM 2.0 with primitive gates only (h, x, cx, ccx-free: CCCZ/CCCX via qelib1 'c3x')."""
    L = ["OPENQASM 2.0;", 'include "qelib1.inc";', "qreg q[4];", "creg c[4];", "h q;"]
    for _ in range(K):
        L += ["x q[1];", "x q[3];", "h q[3];", "c3x q[0],q[1],q[2],q[3];", "h q[3];", "x q[1];", "x q[3];"]
        L += ["h q;", "x q;", "h q[3];", "c3x q[0],q[1],q[2],q[3];", "h q[3];", "x q;", "h q;"]
    L.append("measure q -> c;")
    return "\n".join(L) + "\n"
